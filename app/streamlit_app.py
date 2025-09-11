"""
streamlit_app.py
Streamlit UI for PPR Eradication Cost Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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
        min_val = float(f"{row['Minimum']:.2f}")
        max_val = float(f"{row['Maximum']:.2f}")
        avg_val = float(f"{row['Average']:.2f}")
        st.markdown(f"<span style='font-weight:600;font-size:1rem;margin-bottom:0px;'>{region}</span>", unsafe_allow_html=True)
        cols = st.columns([1, 6, 1])
        with cols[0]:
            st.markdown(f"<span style='font-size:0.9rem;font-weight:500;'>Min<br>{min_val:.2f}</span>", unsafe_allow_html=True)
        with cols[1]:
            slider_val = st.slider(
                "",
                min_value=min_val,
                max_value=max_val,
                value=avg_val,
                step=0.01,
                key=f"cost_slider_{region}"
            )
            st.session_state["regional_custom_cost"][region] = slider_val
        with cols[2]:
            st.markdown(f"<span style='font-size:0.9rem;font-weight:500;'>Max<br>{max_val:.2f}</span>", unsafe_allow_html=True)

    st.markdown("<span style='font-weight:600;font-size:1.1rem;'>Coverage % (First Year)</span>", unsafe_allow_html=True)
    coverage = st.slider("", 0, 100, 80)

    st.markdown("---")
    st.markdown("<span style='font-weight:600;font-size:1.1rem;'>Newborn Estimation Defaults</span>", unsafe_allow_html=True)
    newborn_goats = st.number_input("Goats (% of initial)", 0.0, 1.0, 0.6)
    newborn_sheep = st.number_input("Sheep (% of initial)", 0.0, 1.0, 0.4)
    st.markdown("<span style='font-weight:600;font-size:1.1rem;'>Coverage in Year 2 (% of newborns)</span>", unsafe_allow_html=True)
    second_year_coverage_val = st.slider("", 0, 100, 100)

    st.markdown("<span style='font-weight:600;font-size:1.1rem;'>Vaccine Wastage %</span>", unsafe_allow_html=True)
    wastage = st.slider("", 0.0, 0.5, 0.10)
    st.markdown("<span style='font-weight:600;font-size:1.1rem;'>Delivery Channel</span>", unsafe_allow_html=True)
    delivery_channel = st.radio("", ["Public", "Mixed", "Private"])

    st.markdown("<span style='font-weight:600;font-size:1.1rem;'>Delivery Channel Multipliers</span>", unsafe_allow_html=True)
    del_mult_public = st.number_input("Public", 0.0, 5.0, 1.2)
    del_mult_mixed = st.number_input("Mixed", 0.0, 5.0, 1.0)
    del_mult_private = st.number_input("Private", 0.0, 5.0, 0.85)


    st.markdown("---")
    st.markdown("<span style='font-weight:600;font-size:1.1rem;'>Political Multiplier Thresholds</span>", unsafe_allow_html=True)
    thresh_low = st.number_input("Low threshold", 0.0, 1.0, 0.4)
    thresh_high = st.number_input("High threshold", 0.0, 1.0, 0.7)



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
        return 1.0
    elif psi < thresh_high:
        return 1.5
    else:
        return 2.0

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
    doses = doses_required(vaccinated, wastage)
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
    newborn_rate = newborn_goats if species in ["Goat", "Goats"] else newborn_sheep
    newborn_count = vaccinated * newborn_rate
    second_year_coverage_frac = second_year_coverage_val / 100.0
    vaccinated_y2 = second_year_coverage(newborn_count, second_year_coverage_frac)
    doses_y2 = doses_required(vaccinated_y2, wastage)
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

# --- Second year calculations ---
total_newborns_y2 = 0
total_animals_vaccinated_y2 = 0
total_doses_required_y2 = 0
total_cost_y2 = 0
total_vaccines_wasted_y2 = 0
second_year_coverage_frac = second_year_coverage_val / 100.0

for idx, row in national_df.iterrows():
    pop = row["Population"] if pd.notnull(row["Population"]) else 0
    coverage_frac = coverage / 100.0
    vaccinated = vaccinated_initial(pop, coverage_frac)
    species = row["Species"]
    # Use sidebar newborn rates
    newborn_rate = newborn_goats if str(species).lower() == "goat" or str(species).lower() == "goats" else newborn_sheep
    newborn_count = vaccinated * newborn_rate
    vaccinated_y2 = second_year_coverage(newborn_count, second_year_coverage_frac)
    doses_y2 = doses_required(vaccinated_y2, wastage)
    cost_per_animal = get_country_cost(row["Country"])
    cost_before_adj_val = cost_before_adj(doses_y2, cost_per_animal)
    psi = row["Political_Stability_Index"] if pd.notnull(row["Political_Stability_Index"]) else 0.3
    political_mult = get_political_mult(psi)
    total_cost_val = total_cost(cost_before_adj_val, political_mult, delivery_mult)
    vaccines_wasted = doses_y2 - vaccinated_y2
    total_newborns_y2 += newborn_count
    total_animals_vaccinated_y2 += vaccinated_y2
    total_doses_required_y2 += doses_y2
    total_cost_y2 += total_cost_val
    total_vaccines_wasted_y2 += vaccines_wasted

## ...existing code...

# Tabs
tabs = st.tabs([
    "Overview",
    "Regions & Countries",
    "Subregions",
    "Scenario Builder",
    "Methodology & Data Sources",
    "Data",
    "Export / Reports"
])

with tabs[0]:
    st.subheader("Continent Overview")
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

with tabs[1]:
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
    st.dataframe(region_table)

        st.subheader("Subregion Breakdown")
        country_options = sorted(subregions_df["Country"].unique())
        selected_country = st.selectbox("Select Country", country_options)
        subregion_data = subregions_df[subregions_df["Country"] == selected_country]
        subregion_table = []
        for idx, row in subregion_data.iterrows():
            pop = row["Population"] if pd.notnull(row["Population"]) else 0
            area = row["Area"] if "Area" in row and pd.notnull(row["Area"]) else None
            species = str(row["Species"]).capitalize() if "Species" in row else "Unknown"
            coverage_frac = coverage / 100.0
            vaccinated_y1 = vaccinated_initial(pop, coverage_frac)
            doses_y1 = doses_required(vaccinated_y1, wastage)
            cost_per_animal = get_country_cost(selected_country)
            cost_before_adj_val = cost_before_adj(doses_y1, cost_per_animal)
            psi = row["Political_Stability_Index"] if "Political_Stability_Index" in row and pd.notnull(row["Political_Stability_Index"]) else 0.3
            political_mult = get_political_mult(psi)
            total_cost_y1 = total_cost(cost_before_adj_val, political_mult, delivery_mult)
            vaccines_wasted_y1 = doses_y1 - vaccinated_y1
            newborn_rate = newborn_goats if species in ["Goat", "Goats"] else newborn_sheep
            newborn_count = vaccinated_y1 * newborn_rate
            second_year_coverage_frac = second_year_coverage_val / 100.0
            vaccinated_y2 = second_year_coverage(newborn_count, second_year_coverage_frac)
            doses_y2 = doses_required(vaccinated_y2, wastage)
            cost_before_adj_val_y2 = cost_before_adj(doses_y2, cost_per_animal)
            total_cost_y2 = total_cost(cost_before_adj_val_y2, political_mult, delivery_mult)
            vaccines_wasted_y2 = doses_y2 - vaccinated_y2
            subregion_table.append({
                "Subregion": row["Subregion"] if "Subregion" in row else idx,
                "Area": area,
                "Population": int(pop),
                "Species": species,
                "Goats Y1": int(vaccinated_y1) if species in ["Goat", "Goats"] else 0,
                "Sheep Y1": int(vaccinated_y1) if species in ["Sheep", "Sheeps"] else 0,
                "Total Y1": int(vaccinated_y1),
                "Cost Y1": f"${total_cost_y1:,.2f}",
                "Doses Y1": int(doses_y1),
                "Wasted Y1": int(vaccines_wasted_y1),
                "Goats Y2": int(vaccinated_y2) if species in ["Goat", "Goats"] else 0,
                "Sheep Y2": int(vaccinated_y2) if species in ["Sheep", "Sheeps"] else 0,
                "Total Y2": int(vaccinated_y2),
                "Cost Y2": f"${total_cost_y2:,.2f}",
                "Doses Y2": int(doses_y2),
                "Wasted Y2": int(vaccines_wasted_y2),
            })
        subregion_table_df = pd.DataFrame(subregion_table)
        # Format columns
        for col in ["Area", "Population", "Goats Y1", "Sheep Y1", "Total Y1", "Doses Y1", "Wasted Y1", "Goats Y2", "Sheep Y2", "Total Y2", "Doses Y2", "Wasted Y2"]:
            if col in subregion_table_df:
                subregion_table_df[col] = subregion_table_df[col].map(lambda x: f"{int(x):,}" if pd.notnull(x) and str(x).isdigit() else x)
        st.dataframe(subregion_table_df)
    st.subheader("Breakdown by Country")
    # Build country breakdown table
    country_table = []
    for country, stats in country_stats.items():
        country_table.append({
            "Country": country,
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
    st.dataframe(country_table_df)

    with tabs[4]:
        st.subheader("Methodology & Data Sources")
        st.markdown("### Methodology")
        st.markdown(docs.get("methodology", "Methodology markdown not found."), unsafe_allow_html=True)
        st.markdown("### Regional Costs")
        st.markdown(docs.get("regional_costs", "Regional costs markdown not found."), unsafe_allow_html=True)
        st.markdown("### Country Case Costs")
        st.markdown(docs.get("country_case_costs", "Country case costs markdown not found."), unsafe_allow_html=True)
        st.markdown("### Data Sources")
        st.markdown(docs.get("data_sources", "Data sources markdown not found."), unsafe_allow_html=True)
