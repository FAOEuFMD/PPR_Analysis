"""
streamlit_app.py
Streamlit UI for PPR Eradication Cost Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
from streamlit_folium import st_folium
import requests
import json
import sys
import os

st.set_page_config(
    page_title="PPR Vaccination Cost Analysis",
    layout="wide",
    initial_sidebar_state="expanded"
)
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
try:
    from data_load import main as load_data
    from calculations import vaccinated_initial, doses_required, cost_before_adj, total_cost, second_year_coverage
except ImportError as e:
    import traceback
    print('ERROR: Could not import src modules. Check your folder structure and sys.path.')
    print('sys.path:', sys.path)
    print(traceback.format_exc())
    raise

# --- Regional cost table for modal ---
def get_regional_costs():
    # Hardcoded from markdown for now
    return [
        {"Region": "North Africa", "Minimum": 0.106, "Average": 0.191, "Maximum": 0.325},
        {"Region": "West Africa", "Minimum": 0.106, "Average": 0.191, "Maximum": 0.325},
        {"Region": "East Africa", "Minimum": 0.085, "Average": 0.153, "Maximum": 0.260},
        {"Region": "Central Africa", "Minimum": 0.095, "Average": 0.171, "Maximum": 0.291},
        {"Region": "Southern Africa", "Minimum": 0.127, "Average": 0.229, "Maximum": 0.389},
    ]



# --- Sidebar controls ---
with st.sidebar:

    st.header("Scenario Controls")
    scenario_name = st.text_input("Scenario Name", "Default Scenario")

    st.markdown("**Regional Vaccination Cost Selection (USD/animal)**")
    cost_modes = ["Minimum", "Average", "Maximum", "Custom"]
    costs = get_regional_costs()
    if "regional_cost_mode" not in st.session_state:
        st.session_state["regional_cost_mode"] = {r["Region"]: "Average" for r in costs}
    if "regional_custom_cost" not in st.session_state:
        st.session_state["regional_custom_cost"] = {r["Region"]: r["Average"] for r in costs}
    for row in costs:
        region = row["Region"]
        min_val = 0.0
        max_val = 2.0
        avg_val = float(f"{row['Average']:.2f}")
        region_stats_text = f"Min: {row['Minimum']:.2f}, Avg: {row['Average']:.2f}, Max: {row['Maximum']:.2f}"
        st.markdown(f"<span style='font-weight:600;font-size:1rem;margin-bottom:0px;'>{region} <span style='font-size:0.9rem;color:#888;'>({region_stats_text})</span></span>", unsafe_allow_html=True)
        slider_val = st.slider(
            "",
            min_value=min_val,
            max_value=max_val,
            value=avg_val,
            step=0.01,
            key=f"cost_slider_{region}"
        )
        st.session_state["regional_custom_cost"][region] = slider_val

    st.markdown("<span style='font-weight:600;font-size:1.1rem;'>Coverage % (First Year)</span>", unsafe_allow_html=True)
    coverage = st.slider("", 0, 100, 80)

    st.markdown("---")
    st.markdown("<span style='font-weight:600;font-size:1.1rem;'>Newborn Estimation Defaults (% of initial population)</span>", unsafe_allow_html=True)
    newborn_goats = st.number_input("Goats (% of initial population)", 0, 100, 60)
    newborn_sheep = st.number_input("Sheep (% of initial population)", 0, 100, 40)
    st.markdown("<span style='font-weight:600;font-size:1.1rem;'>Coverage in Year 2 (% of newborns)</span>", unsafe_allow_html=True)
    second_year_coverage_val = st.slider("", 0, 100, 100)

    st.markdown("<span style='font-weight:600;font-size:1.1rem;'>Vaccine Wastage (% of doses)</span>", unsafe_allow_html=True)
    wastage = st.slider("", 0, 100, 10)
    st.markdown("<span style='font-weight:600;font-size:1.1rem;'>Delivery Channel</span>", unsafe_allow_html=True)
    delivery_channel = st.radio("", ["Public", "Mixed", "Private"], index=1)

    st.markdown("<span style='font-weight:600;font-size:1.1rem;'>Delivery Channel Multipliers</span>", unsafe_allow_html=True)
    del_mult_public = st.number_input("Public", 0.0, 5.0, 1.2)
    del_mult_mixed = st.number_input("Mixed", 0.0, 5.0, 1.0)
    del_mult_private = st.number_input("Private", 0.0, 5.0, 0.85)


    st.markdown("---")
    st.markdown("<span style='font-weight:600;font-size:1.1rem;'>Political Stability Index Multiplier Thresholds</span>", unsafe_allow_html=True)
    st.caption("Lower or negative index = less stable = higher cost.\nThresholds: Below low = high risk, above high = low risk.")
    thresh_low = st.number_input("Low threshold", -2.5, 2.5, -1.0)
    thresh_high = st.number_input("High threshold", -2.5, 2.5, 0.0)
    mult_high_risk = st.number_input("Multiplier for high risk (index < low)", 1.0, 5.0, 2.0)
    mult_moderate_risk = st.number_input("Multiplier for moderate risk (low ≤ index < high)", 1.0, 5.0, 1.5)
    mult_low_risk = st.number_input("Multiplier for low risk (index ≥ high)", 1.0, 5.0, 1.0)



# Custom header
st.markdown("""
<style>
.header-title {font-size:2.2rem;font-weight:700;margin-bottom:0.5rem;}
.header-sub {font-size:1.1rem;color:#555;}
.kpi-card {background:#f8f9fa;border-radius:16px;padding:1.2rem;margin:0.5rem;box-shadow:0 2px 8px #eee;}
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="header-title">PPR Vaccination Cost Analysis</div>', unsafe_allow_html=True)


# Load data
with st.spinner("Loading data..."):
    data = load_data()
    national_df = data["national_df"]
    subregions_df = data["subregions_df"]
    docs = data["docs"]
    audit_log = data["audit_log"]

# --- Country to Region mapping (simple example, should be replaced with authoritative mapping) ---
country_region_map = {
    # North Africa
    "Algeria": "North Africa",
    "Egypt": "North Africa",
    "Libya": "North Africa",
    "Morocco": "North Africa",
    "Sudan": "North Africa",
    "Tunisia": "North Africa",
    # West Africa
    "Benin": "West Africa",
    "Burkina Faso": "West Africa",
    "Cape Verde": "West Africa",
    "Gambia": "West Africa",
    "Ghana": "West Africa",
    "Guinea": "West Africa",
    "Guinea-Bissau": "West Africa",
    "Côte d'Ivoire": "West Africa",
    "Liberia": "West Africa",
    "Mali": "West Africa",
    "Mauritania": "West Africa",
    "Niger": "West Africa",
    "Nigeria": "West Africa",
    "Senegal": "West Africa",
    "Sierra Leone": "West Africa",
    "Togo": "West Africa",
    # East Africa
    "Burundi": "East Africa",
    "Comoros": "East Africa",
    "Djibouti": "East Africa",
    "Eritrea": "East Africa",
    "Ethiopia": "East Africa",
    "Kenya": "East Africa",
    "Madagascar": "East Africa",
    "Malawi": "East Africa",
    "Mauritius": "East Africa",
    "Mozambique": "East Africa",
    "Rwanda": "East Africa",
    "Seychelles": "East Africa",
    "Somalia": "East Africa",
    "South Sudan": "East Africa",
    "United Republic of Tanzania": "East Africa",
    "Uganda": "East Africa",
    # Central Africa
    "Angola": "Central Africa",
    "Cameroon": "Central Africa",
    "Central African Republic": "Central Africa",
    "Chad": "Central Africa",
    "Congo": "Central Africa",
    "Democratic Republic of the Congo": "Central Africa",
    "Equatorial Guinea": "Central Africa",
    "Gabon": "Central Africa",
    "Sao Tome and Principe": "Central Africa",
    # Southern Africa
    "Botswana": "Southern Africa",
    "Eswatini": "Southern Africa",
    "Lesotho": "Southern Africa",
    "Namibia": "Southern Africa",
    "South Africa": "Southern Africa",
    "Zambia": "Southern Africa",
    "Zimbabwe": "Southern Africa",
    # North Africa
    "Western Sahara": "North Africa",
    # Southern Africa
    "Reunion": "Southern Africa",
}

# --- Get regional cost per country ---
def get_country_cost(country):
    region = country_region_map.get(country, "West Africa")  # Default to West Africa if not found
    return st.session_state["regional_custom_cost"].get(region, 0.191)

# --- Delivery channel multiplier ---
delivery_mult_map = {
    "Public": del_mult_public,
    "Mixed": del_mult_mixed,
    "Private": del_mult_private,
}
delivery_mult = delivery_mult_map.get(delivery_channel, 1.0)

# --- Political multiplier thresholds ---
def get_political_mult(psi):
    if psi < thresh_low:
        return mult_high_risk
    elif psi < thresh_high:
        return mult_moderate_risk
    else:
        return mult_low_risk

# --- First year calculations ---

# --- Per-country and per-species breakdowns ---
country_stats = {}
species_list = ["Goat", "Sheep"]
for idx, row in national_df.iterrows():
    country = row["Country"]
    species = str(row["Species"]).capitalize()
    pop = row["Population"] if pd.notnull(row["Population"]) else 0
    coverage_frac = coverage / 100.0
    vaccinated = vaccinated_initial(pop, coverage_frac)
    doses = doses_required(vaccinated, wastage/100)
    cost_per_animal = get_country_cost(country)
    cost_before_adj_val = cost_before_adj(doses, cost_per_animal)
    psi = row["Political_Stability_Index"] if pd.notnull(row["Political_Stability_Index"]) else 0.3
    political_mult = get_political_mult(psi)
    total_cost_val = total_cost(cost_before_adj_val, political_mult, delivery_mult)
    vaccines_wasted = doses - vaccinated
    if country not in country_stats:
        country_stats[country] = {"Y1": {"Goat": 0, "Sheep": 0, "doses": 0, "cost": 0, "wasted": 0}, "Y2": {"Goat": 0, "Sheep": 0, "doses": 0, "cost": 0, "wasted": 0}}
    if species in ["Goat", "Goats"]:
        country_stats[country]["Y1"]["Goat"] += vaccinated
    elif species in ["Sheep", "Sheeps"]:
        country_stats[country]["Y1"]["Sheep"] += vaccinated
    country_stats[country]["Y1"]["doses"] += doses
    country_stats[country]["Y1"]["cost"] += total_cost_val
    country_stats[country]["Y1"]["wasted"] += vaccines_wasted

# --- Second year calculations ---
for idx, row in national_df.iterrows():
    country = row["Country"]
    species = str(row["Species"]).capitalize()
    pop = row["Population"] if pd.notnull(row["Population"]) else 0
    coverage_frac = coverage / 100.0
    vaccinated = vaccinated_initial(pop, coverage_frac)
    newborn_rate = newborn_goats/100 if species in ["Goat", "Goats"] else newborn_sheep/100
    newborn_count = vaccinated * newborn_rate
    second_year_coverage_frac = second_year_coverage_val / 100.0
    vaccinated_y2 = second_year_coverage(newborn_count, second_year_coverage_frac)
    doses_y2 = doses_required(vaccinated_y2, wastage/100)
    cost_per_animal = get_country_cost(country)
    cost_before_adj_val = cost_before_adj(doses_y2, cost_per_animal)
    psi = row["Political_Stability_Index"] if pd.notnull(row["Political_Stability_Index"]) else 0.3
    political_mult = get_political_mult(psi)
    total_cost_val = total_cost(cost_before_adj_val, political_mult, delivery_mult)
    vaccines_wasted = doses_y2 - vaccinated_y2
    if species in ["Goat", "Goats"]:
        country_stats[country]["Y2"]["Goat"] += vaccinated_y2
    elif species in ["Sheep", "Sheeps"]:
        country_stats[country]["Y2"]["Sheep"] += vaccinated_y2
    country_stats[country]["Y2"]["doses"] += doses_y2
    country_stats[country]["Y2"]["cost"] += total_cost_val
    country_stats[country]["Y2"]["wasted"] += vaccines_wasted

# --- Aggregate totals ---
total_animals_vaccinated_y1 = sum(country_stats[c]["Y1"]["Goat"] + country_stats[c]["Y1"]["Sheep"] for c in country_stats)
total_doses_required_y1 = sum(country_stats[c]["Y1"]["doses"] for c in country_stats)
total_cost_y1 = sum(country_stats[c]["Y1"]["cost"] for c in country_stats)
total_vaccines_wasted_y1 = sum(country_stats[c]["Y1"]["wasted"] for c in country_stats)
total_goats_y1 = sum(country_stats[c]["Y1"]["Goat"] for c in country_stats)
total_sheep_y1 = sum(country_stats[c]["Y1"]["Sheep"] for c in country_stats)

total_animals_vaccinated_y2 = sum(country_stats[c]["Y2"]["Goat"] + country_stats[c]["Y2"]["Sheep"] for c in country_stats)
total_doses_required_y2 = sum(country_stats[c]["Y2"]["doses"] for c in country_stats)
total_cost_y2 = sum(country_stats[c]["Y2"]["cost"] for c in country_stats)
total_vaccines_wasted_y2 = sum(country_stats[c]["Y2"]["wasted"] for c in country_stats)
total_goats_y2 = sum(country_stats[c]["Y2"]["Goat"] for c in country_stats)
total_sheep_y2 = sum(country_stats[c]["Y2"]["Sheep"] for c in country_stats)

if total_animals_vaccinated_y1 > 0:
    weighted_cost = total_cost_y1 / total_animals_vaccinated_y1
else:
    weighted_cost = 0

## ...existing code...

# Tabs
tabs = st.tabs([
    "Scenario Builder",
    "Overview",
    "Regions & Countries",
    "Subregions",
    "Methodology & Data Sources"
])

with tabs[0]:
    st.markdown("""
**Build Custom Vaccination Scenarios**

This tool allows you to create targeted vaccination scenarios by adjusting parameters in the sidebar and selecting specific countries and regions for analysis. Use the sidebar controls to modify coverage rates, regional costs, political stability factors, and delivery channels - all calculations will update automatically across all tabs. Below, you can select particular countries and their subnational regions to focus your analysis on specific geographic areas, such as border regions, episystems, or outbreak-prone zones. The results table will show vaccination costs and logistics only for your selected areas.

**Tab Guide:**
- **Overview**: Total vaccination impact across all of Africa
- **Regions & Countries**: Breakdown by African regions and individual countries  
- **Subregions**: Detailed view of subnational areas within a single country
- **Scenario Builder** (this tab): Create custom scenarios by selecting specific countries/regions
""")
    
    # Hierarchical Country/Region Selector
    st.markdown("---")
    st.markdown("**Select Countries and Subnational Regions for Custom Scenario:**")
    
    # Get available countries from subregions data
    available_countries = sorted(subregions_df["Country"].unique())
    
    # Multi-select for countries
    selected_countries = st.multiselect("Select Countries:", available_countries, key="scenario_countries")
    
    # Initialize session state for region selections
    if "region_selections" not in st.session_state:
        st.session_state["region_selections"] = {}
    
    selected_regions_data = []
    
    if selected_countries:
        st.markdown("**Configure regions for each selected country:**")
        
        for country in selected_countries:
            st.markdown(f"**{country}:**")
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Option to select all regions or specific regions
                region_option = st.radio(
                    f"Regions for {country}:",
                    ["All regions", "Select specific regions"],
                    key=f"region_option_{country}"
                )
            
            with col2:
                if region_option == "Select specific regions":
                    # Get available regions for this country
                    country_regions = sorted(subregions_df[subregions_df["Country"] == country]["Subregion"].unique())
                    selected_regions = st.multiselect(
                        f"Select regions in {country}:",
                        country_regions,
                        key=f"regions_{country}"
                    )
                    
                    # Add selected regions to data
                    for region in selected_regions:
                        region_data = subregions_df[
                            (subregions_df["Country"] == country) & 
                            (subregions_df["Subregion"] == region)
                        ]
                        selected_regions_data.extend(region_data.to_dict('records'))
                else:
                    # Add all regions for this country
                    country_data = subregions_df[subregions_df["Country"] == country]
                    selected_regions_data.extend(country_data.to_dict('records'))
        
        # Add Map visualization
if selected_countries:
    st.markdown("---")
    # Create a horizontal row: map title (left), parameters summary (right)
    title_col, param_col = st.columns([2, 2])
    with title_col:
        st.markdown("**Map of Selected Countries and Regions:**")
    with param_col:
        st.markdown("<b>Parameters Summary</b>", unsafe_allow_html=True)
        colA, colB = st.columns(2)
        with colA:
            st.markdown("<small><b>Coverage & Vaccination</b></small>", unsafe_allow_html=True)
            st.write(f"<span style='font-size:0.95em'>• 1st Year Coverage: <b>{coverage}%</b></span>", unsafe_allow_html=True)
            st.write(f"<span style='font-size:0.95em'>• Wastage: <b>{wastage}%</b></span>", unsafe_allow_html=True)
            st.write(f"<span style='font-size:0.95em'>• Channel: <b>{delivery_channel}</b> (x{delivery_mult:.2f})</span>", unsafe_allow_html=True)
            st.markdown("<small><b>Newborn Estimation</b></small>", unsafe_allow_html=True)
            st.write(f"<span style='font-size:0.95em'>• Goats: <b>{newborn_goats}%</b>", unsafe_allow_html=True)
            st.write(f"<span style='font-size:0.95em'>• Sheep: <b>{newborn_sheep}%</b>", unsafe_allow_html=True)
            st.write(f"<span style='font-size:0.95em'>• 2nd Yr Coverage: <b>{second_year_coverage_val}%</b></span>", unsafe_allow_html=True)
        with colB:
            st.markdown("<small><b>Political Stability</b></small>", unsafe_allow_html=True)
            st.write(f"<span style='font-size:0.95em'>• Low: <b>{thresh_low}</b> | High: <b>{thresh_high}</b></span>", unsafe_allow_html=True)
            st.write(f"<span style='font-size:0.95em'>• High Risk: <b>{mult_high_risk:.1f}x</b>", unsafe_allow_html=True)
            st.write(f"<span style='font-size:0.95em'>• Mod: <b>{mult_moderate_risk:.1f}x</b>", unsafe_allow_html=True)
            st.write(f"<span style='font-size:0.95em'>• Low: <b>{mult_low_risk:.1f}x</b>", unsafe_allow_html=True)
            st.markdown("<small><b>Regional Cost (USD/animal)</b></small>", unsafe_allow_html=True)
            for region, cost in st.session_state["regional_custom_cost"].items():
                st.write(f"<span style='font-size:0.95em'>• {region}: <b>${cost:.3f}</b></span>", unsafe_allow_html=True)

    # Create a folium map centered on Africa
    m = folium.Map(
        location=[0, 20],  # Center of Africa
        zoom_start=3,
        tiles=None  # We'll add custom tiles
    )
    # Add the UN ClearMap WebTopo base layer
    folium.TileLayer(
        tiles='https://geoservices.un.org/arcgis/rest/services/ClearMap_WebTopo/MapServer/tile/{z}/{y}/{x}',
        attr='UN Clear Map',
        name='UN Clear Map',
        overlay=False,
        control=True
    ).add_to(m)
    # Country coordinates (approximate centers for African countries)
    country_coords = {
        "Algeria": [28.0339, 1.6596],
        "Angola": [-11.2027, 17.8739],
        "Benin": [9.3077, 2.3158],
        "Botswana": [-22.3285, 24.6849],
        "Burkina Faso": [12.2383, -1.5616],
        "Burundi": [-3.3731, 29.9189],
        "Cameroon": [7.3697, 12.3547],
        "Cape Verde": [16.5388, -24.0131],
        "Central African Republic": [6.6111, 20.9394],
        "Chad": [15.4542, 18.7322],
        "Comoros": [-11.6455, 43.3333],
        "Congo": [-0.2280, 15.8277],
        "Democratic Republic of the Congo": [-4.0383, 21.7587],
        "Djibouti": [11.8251, 42.5903],
        "Egypt": [26.0975, 31.2357],
        "Equatorial Guinea": [1.5000, 10.5000],
        "Eritrea": [15.1794, 39.7823],
        "Eswatini": [-26.5225, 31.4659],
        "Ethiopia": [9.1450, 40.4897],
        "Gabon": [-0.8037, 11.6094],
        "Gambia": [13.4432, -15.3101],
        "Ghana": [7.9465, -1.0232],
        "Guinea": [9.9456, -9.6966],
        "Guinea-Bissau": [11.8037, -15.1804],
        "Côte d'Ivoire": [7.5400, -5.5471],
        "Kenya": [-0.0236, 37.9062],
        "Lesotho": [-29.6100, 28.2336],
        "Liberia": [6.4281, -9.4295],
        "Libya": [26.3351, 17.2283],
        "Madagascar": [-18.7669, 46.8691],
        "Malawi": [-13.2543, 34.3015],
        "Mali": [17.5707, -3.9962],
        "Mauritania": [21.0079, -10.9408],
        "Mauritius": [-20.3484, 57.5522],
        "Morocco": [31.7917, -7.0926],
        "Mozambique": [-18.6657, 35.5296],
        "Namibia": [-22.9576, 18.4904],
        "Niger": [17.6078, 8.0817],
        "Nigeria": [9.0765, 8.6753],
        "Rwanda": [-1.9403, 29.8739],
        "Sao Tome and Principe": [0.1864, 6.6131],
        "Senegal": [14.4974, -14.4524],
        "Seychelles": [-4.6796, 55.4920],
        "Sierra Leone": [8.4606, -11.7799],
        "Somalia": [5.1521, 46.1996],
        "South Africa": [-30.5595, 22.9375],
        "South Sudan": [6.8770, 31.3070],
        "Sudan": [12.8628, 30.2176],
        "United Republic of Tanzania": [-6.3690, 34.8888],
        "Togo": [8.6195, 0.8248],
        "Tunisia": [33.8869, 9.5375],
        "Uganda": [1.3733, 32.2903],
        "Zambia": [-13.1339, 27.8493],
        "Zimbabwe": [-19.0154, 29.1549]
    }
    
    # ISO3 mapping (critical for geoBoundaries)
    country_iso3 = {
        "Algeria": "DZA",
        "Angola": "AGO", 
        "Benin": "BEN",
        "Botswana": "BWA",
        "Burkina Faso": "BFA",
        "Burundi": "BDI",
        "Cameroon": "CMR",
        "Cape Verde": "CPV",
        "Central African Republic": "CAF",
        "Chad": "TCD",
        "Comoros": "COM",
        "Congo": "COG",
        "Democratic Republic of the Congo": "COD",
        "Djibouti": "DJI",
        "Egypt": "EGY",
        "Equatorial Guinea": "GNQ",
        "Eritrea": "ERI",
        "Eswatini": "SWZ",
        "Ethiopia": "ETH",
        "Gabon": "GAB",
        "Gambia": "GMB",
        "Ghana": "GHA",
        "Guinea": "GIN",
        "Guinea-Bissau": "GNB",
        "Côte d'Ivoire": "CIV",
        "Kenya": "KEN",
        "Lesotho": "LSO",
        "Liberia": "LBR",
        "Libya": "LBY",
        "Madagascar": "MDG",
        "Malawi": "MWI",
        "Mali": "MLI",
        "Mauritania": "MRT",
        "Mauritius": "MUS",
        "Morocco": "MAR",
        "Mozambique": "MOZ",
        "Namibia": "NAM",
        "Niger": "NER",
        "Nigeria": "NGA",
        "Rwanda": "RWA",
        "Sao Tome and Principe": "STP",
        "Senegal": "SEN",
        "Seychelles": "SYC",
        "Sierra Leone": "SLE",
        "Somalia": "SOM",
        "South Africa": "ZAF",
        "South Sudan": "SSD",
        "Sudan": "SDN",
        "United Republic of Tanzania": "TZA",
        "Togo": "TGO",
        "Tunisia": "TUN",
        "Uganda": "UGA",
        "Zambia": "ZMB",
        "Zimbabwe": "ZWE"
    }

    # === Cached function: get ADM1 GeoJSON from geoBoundaries ===
    @st.cache_data(ttl=86400)  # Cache for 24 hours
    def get_adm1_geojson(iso3: str):
        try:
            meta_url = f"https://www.geoboundaries.org/api/current/gbOpen/{iso3}/ADM1"
            meta_resp = requests.get(meta_url, timeout=10)
            if meta_resp.status_code != 200:
                return None
            meta = meta_resp.json()
            gj_url = meta.get("gjDownloadURL", "").strip()
            if not gj_url:
                return None
            gj_resp = requests.get(gj_url, timeout=10)
            if gj_resp.status_code == 200:
                return gj_resp.json()
        except Exception as e:
            st.warning(f"Failed to load ADM1 for {iso3}: {str(e)}")
            return None
        return None

    # === Cached function: world countries (fallback) ===
    @st.cache_data
    def load_world_geojson():
        try:
            url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None

    world_geojson = load_world_geojson()

    # Check if any specific regions are selected
    has_specific_regions = False
    selected_specific_regions = []
    for country in selected_countries:
        region_option = st.session_state.get(f"region_option_{country}", "All regions")
        if region_option == "Select specific regions":
            regions = st.session_state.get(f"regions_{country}", [])
            if regions:
                has_specific_regions = True
                for region in regions:
                    selected_specific_regions.append((country, region))

    # === Handle specific subregions using geoBoundaries ===
    if has_specific_regions:
        for country, region in selected_specific_regions:
            iso3 = country_iso3.get(country)
            if not iso3:
                st.warning(f"ISO3 code not found for {country}. Skipping subregion.")
                continue

            adm1_data = get_adm1_geojson(iso3)
            region_found = False

            if adm1_data:
                for feature in adm1_data['features']:
                    shape_name = feature['properties'].get('shapeName', '').strip()
                    # Match using your Subregion value (case-insensitive, flexible)
                    if (
                        shape_name.lower() == region.lower() or
                        shape_name.lower().replace(' ', '') == region.lower().replace(' ', '') or
                        region.lower() in shape_name.lower() or
                        shape_name.lower() in region.lower()
                    ):
                        folium.GeoJson(
                            feature,
                            style_function=lambda x: {
                                'fillColor': 'red',
                                'color': 'darkred',
                                'weight': 2,
                                'fillOpacity': 0.4,
                                'dashArray': '5, 5'
                            },
                            popup=folium.Popup(f"<b>{region}, {country}</b>", parse_html=True),
                            tooltip=f"{region}, {country}"
                        ).add_to(m)
                        region_found = True
                        break

            if not region_found:
                st.warning(f"Could not find shape for '{region}' in {country}. Showing country instead.")
                # Fallback to country (handled below)

    # === Handle "All regions" countries ===
    if world_geojson:
        for country in selected_countries:
            region_option = st.session_state.get(f"region_option_{country}", "All regions")
            if region_option == "All regions":
                country_found = False
                for feature in world_geojson['features']:
                    country_name = feature['properties'].get('NAME', '').strip()
                    name_matches = [
                        country_name.lower() == country.lower(),
                        country_name.lower().replace(' ', '') == country.lower().replace(' ', ''),
                        country.lower() in country_name.lower(),
                        country_name.lower() in country.lower(),
                        (country == "Democratic Republic of the Congo" and "congo" in country_name.lower() and "democratic" in country_name.lower()),
                        (country == "Côte d'Ivoire" and ("ivory" in country_name.lower() or "cote" in country_name.lower())),
                        (country == "United Republic of Tanzania" and "tanzania" in country_name.lower()),
                        (country == "Cape Verde" and "cabo verde" in country_name.lower()),
                    ]
                    if any(name_matches):
                        folium.GeoJson(
                            feature,
                            style_function=lambda x: {
                                'fillColor': 'red',
                                'color': 'darkred',
                                'weight': 2,
                                'fillOpacity': 0.4,
                                'dashArray': '5, 5'
                            },
                            popup=folium.Popup(f"<b>{country}</b>", parse_html=True),
                            tooltip=f"{country}"
                        ).add_to(m)
                        country_found = True
                        break
                if not country_found:
                    st.warning(f"Country shape not found for {country}. Using marker.")
                    coords = country_coords.get(country)
                    if coords:
                        folium.Marker(
                            location=coords,
                            popup=f"{country} (shape not available)",
                            tooltip=f"{country}",
                            icon=folium.Icon(color='red', icon='info-sign')
                        ).add_to(m)
    else:
        st.error("Could not load country boundary data. Using markers.")
        for country in selected_countries:
            coords = country_coords.get(country)
            if coords:
                folium.Marker(
                    location=coords,
                    popup=f"{country}",
                    tooltip=f"{country}",
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(m)


    # Display map and disclaimer below the title/parameters row
    map_data = st_folium(m, width=700, height=400)
    st.caption("The boundaries and names shown and the designations used on this map do not imply the expression of any opinion whatsoever on the part of FAO concerning the legal status of any country, territory, city or area or of its authorities, or concerning the delimitation of its frontiers and boundaries")

    # Add Calculate button below the map/parameters
    calculate_clicked = st.button("Calculate")

    # Only calculate and display results if button is pressed and there is data
    if calculate_clicked and selected_regions_data:
        st.markdown("---")
        st.markdown("**Custom Scenario Results:**")

        # Group data by Country and Subregion to aggregate species
        from collections import defaultdict
        grouped_data = defaultdict(lambda: {"goats_data": None, "sheep_data": None})

        for row_data in selected_regions_data:
            country = row_data["Country"]
            subregion = row_data["Subregion"] if pd.notnull(row_data["Subregion"]) else "Unknown"
            key = (country, subregion)

            # Check for both 'Specie' and 'Species' columns
            if "Specie" in row_data:
                specie_val = row_data["Specie"]
            elif "Species" in row_data:
                specie_val = row_data["Species"]
            else:
                specie_val = "Unknown"
            specie = specie_val if pd.notnull(specie_val) else "Unknown"

            if specie == "Goats":
                grouped_data[key]["goats_data"] = row_data
            elif specie == "Sheep":
                grouped_data[key]["sheep_data"] = row_data

        scenario_table = []
        for (country, subregion), species_data in grouped_data.items():
            goats_data = species_data["goats_data"]
            sheep_data = species_data["sheep_data"]

            # Get Political Stability Index from national data
            country_data = national_df[national_df["Country"] == country]
            if not country_data.empty:
                psi = country_data["Political_Stability_Index"].iloc[0] if pd.notnull(country_data["Political_Stability_Index"].iloc[0]) else 0.3
            else:
                psi = 0.3
            cost_per_animal = get_country_cost(country)
            political_mult = get_political_mult(psi)
            coverage_frac = coverage / 100.0

            # Initialize totals
            total_goats_y1 = total_sheep_y1 = total_goats_y2 = total_sheep_y2 = 0
            total_doses_y1 = total_doses_y2 = total_cost_y1 = total_cost_y2 = total_wasted_y1 = total_wasted_y2 = 0

            # Calculate for Goats
            if goats_data:
                pop_raw = goats_data["100%_Coverage"] if pd.notnull(goats_data["100%_Coverage"]) else 0
                try:
                    population = float(pop_raw) if pop_raw != "Unknown" else 0
                except (ValueError, TypeError):
                    population = 0

                if population > 0:
                    # Year 1 calculations for goats
                    vaccinated_y1 = vaccinated_initial(population, coverage_frac)
                    doses_y1 = doses_required(vaccinated_y1, wastage/100)
                    cost_before_adj_y1 = cost_before_adj(doses_y1, cost_per_animal)
                    cost_y1 = total_cost(cost_before_adj_y1, political_mult, delivery_mult)
                    wasted_y1 = doses_y1 - vaccinated_y1


            # Year 2 calculations for goats
            if goats_data and population > 0:
                newborn_count = vaccinated_y1 * (newborn_goats/100)
                vaccinated_y2 = second_year_coverage(newborn_count, second_year_coverage_val/100)
                doses_y2 = doses_required(vaccinated_y2, wastage/100)
                cost_before_adj_y2 = cost_before_adj(doses_y2, cost_per_animal)
                cost_y2 = total_cost(cost_before_adj_y2, political_mult, delivery_mult)
                wasted_y2 = doses_y2 - vaccinated_y2

                total_goats_y1 = vaccinated_y1
                total_goats_y2 = vaccinated_y2
                total_doses_y1 += doses_y1
                total_doses_y2 += doses_y2
                total_cost_y1 += cost_y1
                total_cost_y2 += cost_y2
                total_wasted_y1 += wasted_y1
                total_wasted_y2 += wasted_y2

            # Calculate for Sheep
            if sheep_data:
                pop_raw = sheep_data["100%_Coverage"] if pd.notnull(sheep_data["100%_Coverage"]) else 0
                try:
                    population = float(pop_raw) if pop_raw != "Unknown" else 0
                except (ValueError, TypeError):
                    population = 0

                if population > 0:
                    # Year 1 calculations for sheep
                    vaccinated_y1 = vaccinated_initial(population, coverage_frac)
                    doses_y1 = doses_required(vaccinated_y1, wastage/100)
                    cost_before_adj_y1 = cost_before_adj(doses_y1, cost_per_animal)
                    cost_y1 = total_cost(cost_before_adj_y1, political_mult, delivery_mult)
                    wasted_y1 = doses_y1 - vaccinated_y1

                    # Year 2 calculations for sheep
                    newborn_count = vaccinated_y1 * (newborn_sheep/100)
                    vaccinated_y2 = second_year_coverage(newborn_count, second_year_coverage_val/100)
                    doses_y2 = doses_required(vaccinated_y2, wastage/100)
                    cost_before_adj_y2 = cost_before_adj(doses_y2, cost_per_animal)
                    cost_y2 = total_cost(cost_before_adj_y2, political_mult, delivery_mult)
                    wasted_y2 = doses_y2 - vaccinated_y2

                    total_sheep_y1 = vaccinated_y1
                    total_sheep_y2 = vaccinated_y2
                    total_doses_y1 += doses_y1
                    total_doses_y2 += doses_y2
                    total_cost_y1 += cost_y1
                    total_cost_y2 += cost_y2
                    total_wasted_y1 += wasted_y1
                    total_wasted_y2 += wasted_y2

            # Only add row if there's data for at least one species
            if total_goats_y1 > 0 or total_sheep_y1 > 0:
                # Get Political Stability Index for this country
                country_data = national_df[national_df["Country"] == country]
                if not country_data.empty:
                    psi_display = country_data["Political_Stability_Index"].iloc[0] if pd.notnull(country_data["Political_Stability_Index"].iloc[0]) else 0.3
                else:
                    psi_display = 0.3

                scenario_table.append({
                    "Country": country,
                    "Political_Stability_Index": f"{psi_display:.3f}",
                    "Subregion": subregion,
                    "Goats Y1": int(total_goats_y1),
                    "Sheep Y1": int(total_sheep_y1),
                    "Total Y1": int(total_goats_y1 + total_sheep_y1),
                    "Cost Y1": f"${total_cost_y1:,.2f}",
                    "Doses Y1": int(total_doses_y1),
                    "Wasted Y1": int(total_wasted_y1),
                    "Goats Y2": int(total_goats_y2),
                    "Sheep Y2": int(total_sheep_y2),
                    "Total Y2": int(total_goats_y2 + total_sheep_y2),
                    "Cost Y2": f"${total_cost_y2:,.2f}",
                    "Doses Y2": int(total_doses_y2),
                    "Wasted Y2": int(total_wasted_y2),
                })

        if scenario_table:
            scenario_table_df = pd.DataFrame(scenario_table)
            # Display columns (hide Specie and Population for cleaner view)
            display_cols = ["Country", "Political_Stability_Index", "Subregion", "Goats Y1", "Sheep Y1", "Total Y1", "Cost Y1", "Doses Y1", "Wasted Y1", 
                           "Goats Y2", "Sheep Y2", "Total Y2", "Cost Y2", "Doses Y2", "Wasted Y2"]
            scenario_display_df = scenario_table_df[display_cols]
            
            # Format numeric columns
            for col in ["Goats Y1", "Sheep Y1", "Total Y1", "Doses Y1", "Wasted Y1", "Goats Y2", "Sheep Y2", "Total Y2", "Doses Y2", "Wasted Y2"]:
                if col in scenario_display_df:
                    scenario_display_df[col] = scenario_display_df[col].map(lambda x: f"{int(float(x)):,}" if pd.notnull(x) and x != 0 else "0")
            
            st.dataframe(scenario_display_df, height=min(len(scenario_display_df)*35+40, 400))
            
            # Summary totals
            total_goats_y1 = sum([int(str(row["Goats Y1"]).replace(',', '')) for row in scenario_table])
            total_sheep_y1 = sum([int(str(row["Sheep Y1"]).replace(',', '')) for row in scenario_table])
            total_cost_y1 = sum([float(str(row["Cost Y1"]).replace('$', '').replace(',', '')) for row in scenario_table])
            total_cost_y2 = sum([float(str(row["Cost Y2"]).replace('$', '').replace(',', '')) for row in scenario_table])
            
            st.markdown("**Scenario Totals:**")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Goats Y1", f"{total_goats_y1:,}")
            with col2:
                st.metric("Total Sheep Y1", f"{total_sheep_y1:,}")
            with col3:
                st.metric("Total Cost Y1", f"${total_cost_y1:,.2f}")
            with col4:
                st.metric("Total Cost Y2", f"${total_cost_y2:,.2f}")
        else:
            st.info("No data available for the selected regions.")
    else:
        st.info("Please select specific regions to see custom scenario results.")
    
    # Only show parameters section if countries are selected
    if selected_countries:
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        

with tabs[1]:
    st.subheader("African Continent Overview")
    # Y1 info boxes
    cols_y1 = st.columns(3)
    with cols_y1[0]:
        st.markdown(f'<div class="kpi-card">Total Animals Vaccinated (Y1)<br><b>{int(total_animals_vaccinated_y1):,}</b></div>', unsafe_allow_html=True)
    with cols_y1[1]:
        st.markdown(f'<div class="kpi-card">Goats Vaccinated (Y1)<br><b>{int(total_goats_y1):,}</b></div>', unsafe_allow_html=True)
    with cols_y1[2]:
        st.markdown(f'<div class="kpi-card">Sheep Vaccinated (Y1)<br><b>{int(total_sheep_y1):,}</b></div>', unsafe_allow_html=True)

    cols_y1b = st.columns(3)
    with cols_y1b[0]:
        st.markdown(f'<div class="kpi-card">Total Cost (Y1)<br><b>${total_cost_y1:,.2f}</b></div>', unsafe_allow_html=True)
    with cols_y1b[1]:
        st.markdown(f'<div class="kpi-card">Cost per Animal (weighted)<br><b>${weighted_cost:,.2f}</b></div>', unsafe_allow_html=True)
    with cols_y1b[2]:
        st.markdown(f'<div class="kpi-card">Total Doses Required (Y1)<br><b>{int(total_doses_required_y1):,}</b></div>', unsafe_allow_html=True)

    cols_y1c = st.columns(3)
    with cols_y1c[0]:
        st.markdown(f'<div class="kpi-card">Vaccines Wasted (Y1)<br><b>{int(total_vaccines_wasted_y1):,}</b></div>', unsafe_allow_html=True)
    with cols_y1c[1]:
        st.markdown("<div class='kpi-card'>&nbsp;</div>", unsafe_allow_html=True)
    with cols_y1c[2]:
        st.markdown("<div class='kpi-card'>&nbsp;</div>", unsafe_allow_html=True)

    st.markdown("---")
    # Y2 info boxes
    cols_y2 = st.columns(3)
    with cols_y2[0]:
        st.markdown(f'<div class="kpi-card">Total Animals Vaccinated (Y2)<br><b>{int(total_animals_vaccinated_y2):,}</b></div>', unsafe_allow_html=True)
    with cols_y2[1]:
        st.markdown(f'<div class="kpi-card">Goats Vaccinated (Y2)<br><b>{int(total_goats_y2):,}</b></div>', unsafe_allow_html=True)
    with cols_y2[2]:
        st.markdown(f'<div class="kpi-card">Sheep Vaccinated (Y2)<br><b>{int(total_sheep_y2):,}</b></div>', unsafe_allow_html=True)

    cols_y2b = st.columns(3)
    with cols_y2b[0]:
        st.markdown(f'<div class="kpi-card">Total Cost (Y2)<br><b>${total_cost_y2:,.2f}</b></div>', unsafe_allow_html=True)
    with cols_y2b[1]:
        st.markdown(f'<div class="kpi-card">Total Doses Required (Y2)<br><b>{int(total_doses_required_y2):,}</b></div>', unsafe_allow_html=True)
    with cols_y2b[2]:
        st.markdown(f'<div class="kpi-card">Vaccines Wasted (Y2)<br><b>{int(total_vaccines_wasted_y2):,}</b></div>', unsafe_allow_html=True)

with tabs[2]:
    st.subheader("Breakdown by Region")
    # Build region breakdown table
    region_stats = {}
    for country, stats in country_stats.items():
        region = country_region_map.get(country, "West Africa")
        if region not in region_stats:
            region_stats[region] = {
                "Goats Y1": 0, "Sheep Y1": 0, "Total Y1": 0, "Cost Y1": 0, "Doses Y1": 0, "Wasted Y1": 0,
                "Goats Y2": 0, "Sheep Y2": 0, "Total Y2": 0, "Cost Y2": 0, "Doses Y2": 0, "Wasted Y2": 0
            }
        region_stats[region]["Goats Y1"] += stats["Y1"]["Goat"]
        region_stats[region]["Sheep Y1"] += stats["Y1"]["Sheep"]
        region_stats[region]["Total Y1"] += stats["Y1"]["Goat"] + stats["Y1"]["Sheep"]
        region_stats[region]["Cost Y1"] += stats["Y1"]["cost"]
        region_stats[region]["Doses Y1"] += stats["Y1"]["doses"]
        region_stats[region]["Wasted Y1"] += stats["Y1"]["wasted"]
        region_stats[region]["Goats Y2"] += stats["Y2"]["Goat"]
        region_stats[region]["Sheep Y2"] += stats["Y2"]["Sheep"]
        region_stats[region]["Total Y2"] += stats["Y2"]["Goat"] + stats["Y2"]["Sheep"]
        region_stats[region]["Cost Y2"] += stats["Y2"]["cost"]
        region_stats[region]["Doses Y2"] += stats["Y2"]["doses"]
        region_stats[region]["Wasted Y2"] += stats["Y2"]["wasted"]

    import numpy as np
    region_table = pd.DataFrame.from_dict(region_stats, orient="index")
    region_table = region_table.reset_index().rename(columns={"index": "Region"})
    # Format columns
    for col in region_table.columns:
        if region_table[col].dtype == np.float64 or region_table[col].dtype == np.int64:
            if "Cost" in col:
                region_table[col] = region_table[col].map(lambda x: f"${x:,.2f}")
            else:
                region_table[col] = region_table[col].map(lambda x: f"{int(x):,}")
    st.dataframe(region_table, height=region_table.shape[0]*35+40)

    # Pie chart of vaccination cost per region
    import plotly.graph_objects as go
    pie_labels = region_table["Region"]
    pie_values_y1 = region_table["Cost Y1"].apply(lambda x: float(str(x).replace('$','').replace(',','')))
    pie_values_y2 = region_table["Cost Y2"].apply(lambda x: float(str(x).replace('$','').replace(',','')))

    # Use consistent colors for both pies
    color_sequence = px.colors.qualitative.Plotly[:len(pie_labels)]

    fig = go.Figure()
    fig.add_trace(go.Pie(labels=pie_labels, values=pie_values_y1, name="Y1", hole=0.3, marker=dict(colors=color_sequence), legendgroup="cost", domain={'x': [0, 0.48]}))
    fig.add_trace(go.Pie(labels=pie_labels, values=pie_values_y2, name="Y2", hole=0.3, marker=dict(colors=color_sequence), legendgroup="cost", domain={'x': [0.52, 1]}))
    fig.update_layout(
        title_text="Vaccination Cost per Region (Y1 vs Y2)",
        grid={'rows': 1, 'columns': 2},
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    fig.update_traces(textinfo="label+percent", pull=[0.02]*len(pie_labels))
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Breakdown by Country")



# Build country breakdown table
    country_table = []
    for country, stats in country_stats.items():
        # Get Political Stability Index for this country
        country_data = national_df[national_df["Country"] == country]
        if not country_data.empty:
            psi = country_data["Political_Stability_Index"].iloc[0] if pd.notnull(country_data["Political_Stability_Index"].iloc[0]) else 0.3
        else:
            psi = 0.3
        
        country_table.append({
            "Country": country,
            "Political_Stability_Index": f"{psi:.3f}",
            "Goats Y1": int(stats['Y1']['Goat']),
            "Sheep Y1": int(stats['Y1']['Sheep']),
            "Total Y1": int(stats['Y1']['Goat'] + stats['Y1']['Sheep']),
            "Cost Y1": f"${stats['Y1']['cost']:,.2f}",
            "Doses Y1": int(stats['Y1']['doses']),
            "Wasted Y1": int(stats['Y1']['wasted']),
            "Goats Y2": int(stats['Y2']['Goat']),
            "Sheep Y2": int(stats['Y2']['Sheep']),
            "Total Y2": int(stats['Y2']['Goat'] + stats['Y2']['Sheep']),
            "Cost Y2": f"${stats['Y2']['cost']:,.2f}",
            "Doses Y2": int(stats['Y2']['doses']),
            "Wasted Y2": int(stats['Y2']['wasted']),
        })
    country_table_df = pd.DataFrame(country_table)
    st.dataframe(country_table_df, height=country_table_df.shape[0]*35+40)

    # Bar charts for country-level vaccination cost (Y1 and Y2)
    import plotly.graph_objects as go
    # Sort by largest Y1 cost first
    country_table_df_sorted = country_table_df.copy()
    country_table_df_sorted["Cost Y1 Float"] = country_table_df_sorted["Cost Y1"].apply(lambda x: float(str(x).replace('$','').replace(',','')))
    country_table_df_sorted = country_table_df_sorted.sort_values("Cost Y1 Float", ascending=True)
    country_names = country_table_df_sorted["Country"]
    cost_y1 = country_table_df_sorted["Cost Y1 Float"]
    cost_y2 = country_table_df_sorted["Cost Y2"].apply(lambda x: float(str(x).replace('$','').replace(',','')))

    bar_fig = go.Figure()
    bar_fig.add_trace(go.Bar(y=country_names, x=cost_y1, name="Y1", marker_color="#636EFA", orientation="h", width=0.8))
    bar_fig.add_trace(go.Bar(y=country_names, x=cost_y2, name="Y2", marker_color="#EF553B", orientation="h", width=0.8))
    bar_fig.update_layout(
        barmode="group",
        title="Vaccination Cost by Country (Y1 vs Y2)",
        xaxis_title="Cost (USD)",
        yaxis_title="Country",
        legend_title="Year",
        height=700,
        bargap=0.1,  # Reduce gap between bars
        bargroupgap=0.05  # Reduce gap between groups
    )
    st.plotly_chart(bar_fig, use_container_width=True)

    
with tabs[3]:
    st.subheader("Subregion Breakdown")
    country_options = sorted(subregions_df["Country"].unique())
    selected_country = st.selectbox("Select Country", country_options)
    subregion_data = subregions_df[subregions_df["Country"] == selected_country]
    
    # Group data by Subregion to aggregate species
    from collections import defaultdict
    grouped_subregion_data = defaultdict(lambda: {"goats_data": None, "sheep_data": None})
    
    for idx, row in subregion_data.iterrows():
        subregion = row["Subregion"] if pd.notnull(row["Subregion"]) else "Unknown"
        
        # Check for both 'Specie' and 'Species' columns
        if "Specie" in subregion_data.columns:
            specie_val = row["Specie"]
        elif "Species" in subregion_data.columns:
            specie_val = row["Species"]
        else:
            specie_val = "Unknown"
        specie = specie_val if pd.notnull(specie_val) else "Unknown"
        
        if specie == "Goats":
            grouped_subregion_data[subregion]["goats_data"] = row
        elif specie == "Sheep":
            grouped_subregion_data[subregion]["sheep_data"] = row
    
    subregion_table = []
    for subregion, species_data in grouped_subregion_data.items():
        goats_data = species_data["goats_data"]
        sheep_data = species_data["sheep_data"]
        
        # Get Political Stability Index from national data
        country_data = national_df[national_df["Country"] == selected_country]
        if not country_data.empty:
            psi = country_data["Political_Stability_Index"].iloc[0] if pd.notnull(country_data["Political_Stability_Index"].iloc[0]) else 0.3
        else:
            psi = 0.3
        cost_per_animal = get_country_cost(selected_country)
        political_mult = get_political_mult(psi)
        coverage_frac = coverage / 100.0
        
        # Initialize totals
        total_goats_y1 = total_sheep_y1 = total_goats_y2 = total_sheep_y2 = 0
        total_doses_y1 = total_doses_y2 = total_cost_y1 = total_cost_y2 = total_wasted_y1 = total_wasted_y2 = 0
        
        # Calculate for Goats
        if goats_data is not None:
            pop_raw = goats_data["100%_Coverage"] if pd.notnull(goats_data["100%_Coverage"]) else 0
            try:
                population = float(pop_raw) if pop_raw != "Unknown" else 0
            except (ValueError, TypeError):
                population = 0
            
            if population > 0:
                # Year 1 calculations for goats
                vaccinated_y1 = vaccinated_initial(population, coverage_frac)
                doses_y1 = doses_required(vaccinated_y1, wastage/100)
                cost_before_adj_y1 = cost_before_adj(doses_y1, cost_per_animal)
                cost_y1 = total_cost(cost_before_adj_y1, political_mult, delivery_mult)
                wasted_y1 = doses_y1 - vaccinated_y1
                
                # Year 2 calculations for goats
                newborn_count = vaccinated_y1 * (newborn_goats/100)
                vaccinated_y2 = second_year_coverage(newborn_count, second_year_coverage_val/100)
                doses_y2 = doses_required(vaccinated_y2, wastage/100)
                cost_before_adj_y2 = cost_before_adj(doses_y2, cost_per_animal)
                cost_y2 = total_cost(cost_before_adj_y2, political_mult, delivery_mult)
                wasted_y2 = doses_y2 - vaccinated_y2
                
                total_goats_y1 = vaccinated_y1
                total_goats_y2 = vaccinated_y2
                total_doses_y1 += doses_y1
                total_doses_y2 += doses_y2
                total_cost_y1 += cost_y1
                total_cost_y2 += cost_y2
                total_wasted_y1 += wasted_y1
                total_wasted_y2 += wasted_y2
        
        # Calculate for Sheep
        if sheep_data is not None:
            pop_raw = sheep_data["100%_Coverage"] if pd.notnull(sheep_data["100%_Coverage"]) else 0
            try:
                population = float(pop_raw) if pop_raw != "Unknown" else 0
            except (ValueError, TypeError):
                population = 0
            
            if population > 0:
                # Year 1 calculations for sheep
                vaccinated_y1 = vaccinated_initial(population, coverage_frac)
                doses_y1 = doses_required(vaccinated_y1, wastage/100)
                cost_before_adj_y1 = cost_before_adj(doses_y1, cost_per_animal)
                cost_y1 = total_cost(cost_before_adj_y1, political_mult, delivery_mult)
                wasted_y1 = doses_y1 - vaccinated_y1
                
                # Year 2 calculations for sheep
                newborn_count = vaccinated_y1 * (newborn_sheep/100)
                vaccinated_y2 = second_year_coverage(newborn_count, second_year_coverage_val/100)
                doses_y2 = doses_required(vaccinated_y2, wastage/100)
                cost_before_adj_y2 = cost_before_adj(doses_y2, cost_per_animal)
                cost_y2 = total_cost(cost_before_adj_y2, political_mult, delivery_mult)
                wasted_y2 = doses_y2 - vaccinated_y2
                
                total_sheep_y1 = vaccinated_y1
                total_sheep_y2 = vaccinated_y2
                total_doses_y1 += doses_y1
                total_doses_y2 += doses_y2
                total_cost_y1 += cost_y1
                total_cost_y2 += cost_y2
                total_wasted_y1 += wasted_y1
                total_wasted_y2 += wasted_y2
        
        # Only add row if there's data for at least one species
        if total_goats_y1 > 0 or total_sheep_y1 > 0:
            # Get Political Stability Index for this country
            country_data = national_df[national_df["Country"] == selected_country]
            if not country_data.empty:
                psi_display = country_data["Political_Stability_Index"].iloc[0] if pd.notnull(country_data["Political_Stability_Index"].iloc[0]) else 0.3
            else:
                psi_display = 0.3
            
            subregion_table.append({
                "Subregion": subregion,
                "Political_Stability_Index": f"{psi_display:.3f}",
                "Goats Y1": int(total_goats_y1),
                "Sheep Y1": int(total_sheep_y1),
                "Total Y1": int(total_goats_y1 + total_sheep_y1),
                "Cost Y1": f"${total_cost_y1:,.2f}",
                "Doses Y1": int(total_doses_y1),
                "Wasted Y1": int(total_wasted_y1),
                "Goats Y2": int(total_goats_y2),
                "Sheep Y2": int(total_sheep_y2),
                "Total Y2": int(total_goats_y2 + total_sheep_y2),
                "Cost Y2": f"${total_cost_y2:,.2f}",
                "Doses Y2": int(total_doses_y2),
                "Wasted Y2": int(total_wasted_y2),
            })
    
    subregion_table_df = pd.DataFrame(subregion_table)
    # Only show relevant columns 
    display_cols = ["Subregion", "Political_Stability_Index", "Goats Y1", "Sheep Y1", "Total Y1", "Cost Y1", "Doses Y1", "Wasted Y1", "Goats Y2", "Sheep Y2", "Total Y2", "Cost Y2", "Doses Y2", "Wasted Y2"]
    subregion_table_df = subregion_table_df[display_cols]
    # Format columns
    for col in ["Goats Y1", "Sheep Y1", "Total Y1", "Doses Y1", "Wasted Y1", "Goats Y2", "Sheep Y2", "Total Y2", "Doses Y2", "Wasted Y2"]:
        if col in subregion_table_df:
            subregion_table_df[col] = subregion_table_df[col].map(lambda x: f"{int(float(x)):,}" if pd.notnull(x) and x != 0 else "0")
    st.dataframe(subregion_table_df)

with tabs[4]:
    st.markdown("""
<style>
.methodology-title {font-size:1.6rem;font-weight:700;margin-bottom:0.5rem;}
.methodology-section {font-size:1.1rem;font-weight:600;margin-top:1.2rem;}
.methodology-table {margin-bottom:1.5rem;}
</style>
""", unsafe_allow_html=True)
    st.markdown('<div class="methodology-title">Methodology Summary</div>', unsafe_allow_html=True)
    st.markdown('<div class="methodology-section">Approach</div>', unsafe_allow_html=True)
    st.markdown("""
The dashboard estimates the cost of PPR vaccination across Africa using a scenario-based macro calculator. Calculations are performed for each region, country, and subregion, based on user-adjustable parameters for coverage, newborn rates, wastage, delivery channel, and cost multipliers. Year 1 and Year 2 costs are calculated using population, coverage, wastage, and multipliers for political stability and delivery channel.
""")
    st.markdown('<div class="methodology-section">Calculation Steps</div>', unsafe_allow_html=True)
    st.markdown("""
- **Year 1:**
    - Vaccinated = Population × Coverage %
    - Doses = Vaccinated / (1 - Wastage %)
    - Base Cost = Doses × Cost per Animal
    - Final Cost = Base Cost × Political Stability Multiplier × Delivery Channel Multiplier
- **Year 2:**
    - Newborns = Vaccinated × Newborn %
    - Repeat dose and cost calculations for newborns
""")
    st.markdown('<div class="methodology-section">Key Data Tables</div>', unsafe_allow_html=True)
    st.markdown("**Regional Vaccination Costs (USD/animal):**")
    regional_costs_table = pd.DataFrame([
        {"Region": "North Africa", "Minimum": 0.106, "Average": 0.191, "Maximum": 0.325},
        {"Region": "West Africa", "Minimum": 0.106, "Average": 0.191, "Maximum": 0.325},
        {"Region": "East Africa", "Minimum": 0.085, "Average": 0.153, "Maximum": 0.260},
        {"Region": "Central Africa", "Minimum": 0.095, "Average": 0.171, "Maximum": 0.291},
        {"Region": "Southern Africa", "Minimum": 0.127, "Average": 0.229, "Maximum": 0.389},
    ])
    st.dataframe(regional_costs_table, height=regional_costs_table.shape[0]*35+40)
    
    st.markdown('<div class="methodology-section">Key Factors Influencing Vaccination Costs</div>', unsafe_allow_html=True)
    factors_table = pd.DataFrame([
        {"Factor": "Logistics & Personnel", "Impact on Cost": "Often the largest component (>50% of total cost); includes vaccine delivery, transportation, and staff wages."},
        {"Factor": "Channel (Public vs. Private)", "Impact on Cost": "Public campaigns have higher operational costs due to overhead, while private delivery can be cheaper but more variable."},
        {"Factor": "Location & Production System", "Impact on Cost": "Pastoral vs. agropastoral or mixed-crop systems differ in accessibility and farmer participation."},
        {"Factor": "Economies of Scale", "Impact on Cost": "Large campaigns (e.g., Somalia) reduce per-animal costs significantly."},
        {"Factor": "Vaccine Wastage", "Impact on Cost": "Missed shots or leftover doses can add 10–33% to costs."},
        {"Factor": "Farmer Opportunity Cost", "Impact on Cost": "Especially relevant in mixed-crop systems where farmers lose work time to bring animals for vaccination."},
    ])
    st.dataframe(factors_table, height=factors_table.shape[0]*35+40)
    st.markdown("""
Given the significant impact of delivery and logistics challenges on vaccination costs, particularly in regions with varying political stability, we incorporate the Political Stability Index (PSI) as an adjustment factor to account for these operational complexities and their associated cost implications.
""")
    
    st.markdown("**Political Stability Multiplier Logic:**")
    st.markdown("""
Political stability index (-2.5 weak; 2.5 strong), 2023: The average for 2023 based on 53 countries was -0.68 points. The indicator is available from 1996 to 2023.

- Index < Low Threshold: High risk, higher multiplier
- Low ≤ Index < High: Moderate risk, moderate multiplier
- Index ≥ High: Low risk, lower multiplier
""")
    st.markdown("**Example Data Table (National):**")
    # Drop duplicate and None columns before display
    national_df_display = national_df.loc[:,~national_df.columns.duplicated()]
    national_df_display = national_df_display.loc[:,national_df_display.columns.notnull()]
    st.dataframe(national_df_display.head(10), height=350)
    st.markdown("**Example Data Table (Subregions):**")
    st.dataframe(subregions_df.head(10), height=350)
    st.markdown('<div class="methodology-section">Data Sources</div>', unsafe_allow_html=True)
    st.markdown("""
**Population data:** FAO. 2023. FAOSTAT Statistical Database. Food and Agriculture Organization of the United Nations. Available at: [https://www.fao.org/faostat/en/](https://www.fao.org/faostat/en/)

**Livestock density data:** FAO. 2024. Gridded Livestock of the World (GLW) 4: Gridded Livestock Density (Global - 2020 - 10 km). Food and Agriculture Organization of the United Nations. Available at: [https://data.apps.fao.org/catalog/dataset/15f8c56c-5499-45d5-bd89-59ef6c026704](https://data.apps.fao.org/catalog/dataset/15f8c56c-5499-45d5-bd89-59ef6c026704)

**Vaccination cost data:** The document draws from peer-reviewed studies and field cost estimates on Peste des Petits Ruminants (PPR) vaccination programs in Africa. Key cited sources include:

- **Ethiopia:** Lyons NA et al., Prev Vet Med. 2019 – Field-derived cost estimates of PPR vaccination in Ethiopia. [DOI: 10.1016/j.prevetmed.2018.12.007]
- **Burkina Faso, Senegal, Nigeria:** Ilboudo GS et al., Animals (Basel). 2022 – PPR vaccination cost estimates in Burkina Faso. [DOI: 10.3390/ani12162152]
- **Somalia:** Jue S et al., Pastoralism. 2018 – Sero-prevalence and vaccination cost analysis.

**Political stability data:** TheGlobalEconomy.com. 2024. Political stability index for Africa. Available at: [https://www.theglobaleconomy.com/rankings/wb_political_stability/Africa/](https://www.theglobaleconomy.com/rankings/wb_political_stability/Africa/)

**Additional sources:**
- VADEMOS tool (forecasting)
- Key Factors document, case studies (cost references)
- Internal docs: methodology, costs influencers, analysis examples
""")
    
    st.markdown('<div class="methodology-section">License</div>', unsafe_allow_html=True)
    st.markdown("""
**Creative Commons License**

This work is made available under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 IGO license (CC BY-NC-SA 3.0 IGO; [https://creativecommons.org/licenses/by-nc-sa/3.0/igo](https://creativecommons.org/licenses/by-nc-sa/3.0/igo)). 

In addition to this license, some database specific terms of use are listed: [Terms of Use of Datasets](https://www.fao.org/contact-us/terms/db-terms-of-use/en).

[![Creative Commons License](https://i.creativecommons.org/l/by-nc-sa/3.0/igo/88x31.png)](https://creativecommons.org/licenses/by-nc-sa/3.0/igo)
""")
