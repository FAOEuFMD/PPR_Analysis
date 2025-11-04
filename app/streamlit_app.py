
"""
Streamlit UI for PPR Eradication Cost Dashboard
"""

import streamlit as st
import os
import sys
import pandas as pd
import episystems
import methodology
import regions_countries
import scenario_builder
import subregions
from cost_data import country_region_map, get_regional_costs


def format_table_values(df, numeric_columns):
    """Format numeric values in DataFrame for display"""
    df = df.copy()
    for col in numeric_columns:
        if col in df:
            df[col] = df[col].map(lambda x: f"{int(float(x)):,}" if pd.notnull(x) and x != 0 else "0")
    return df

# Add src directory to path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    import sys
    import os
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    from data_load import main as load_data
    from calculations import (
        vaccinated_initial, doses_required, cost_before_adj,
        total_cost, second_year_coverage
    )
except ImportError as e:
    import traceback
    print('ERROR: Could not import src modules. Check your folder structure and sys.path.')
    print('sys.path:', sys.path)
    print(traceback.format_exc())
    raise

# Import our modules
import continental_overview






# Set Streamlit page config for wide layout
st.set_page_config(layout="wide")

# Custom header styles and full-width layout
st.markdown("""
<style>
.header-title {font-size:2.2rem;font-weight:700;margin-bottom:0.5rem;}
.header-sub {font-size:1.1rem;color:#555;}
.kpi-card {background:#f8f9fa;border-radius:16px;padding:1.2rem;margin:0.5rem;box-shadow:0 2px 8px #eee;}
.header-title {font-size:2.2rem;font-weight:700;margin-bottom:0.5rem;}
.header-sub {font-size:1.1rem;color:#555;}
.kpi-card {background:#f8f9fa;border-radius:16px;padding:1.2rem;margin:0.5rem;box-shadow:0 2px 8px #eee;}
/* Force main container to full width */
.main .block-container {
    max-width: 100vw !important;
    width: 100vw !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}
</style>
""", unsafe_allow_html=True)


col_logo, col_note = st.columns([2,3])
with col_logo:
    st.image("public/EuFMD_2023.png", width=480)
with col_note:
    st.markdown('<div style="font-size:1.1rem; color:#b22222; font-weight:600; margin-top:32px;">This tool is under development and currently being validated.</div>', unsafe_allow_html=True)
st.markdown('<div class="header-title">PPR Vaccination Cost Analysis</div>', unsafe_allow_html=True)

# Initialize session state
if "regional_cost_mode" not in st.session_state:
    costs = get_regional_costs()
    st.session_state["regional_cost_mode"] = {r["Region"]: "Average" for r in costs}
    st.session_state["regional_custom_cost"] = {r["Region"]: r["Average"] for r in costs}

# Configure sidebar
with st.sidebar:
    st.header("Scenario Controls")
    scenario_name = st.text_input("Scenario Name", "Default Scenario")
    # Regional vaccination cost selection
    costs = get_regional_costs()
    for row in costs:
        region = row["Region"]
        min_val = 0.0
        max_val = 2.0
        avg_val = float(f"{row['Average']:.2f}")
        region_stats_text = f"Min: {row['Minimum']:.2f}, Avg: {row['Average']:.2f}, Max: {row['Maximum']:.2f}"
        st.markdown(f"<span style='font-weight:600;font-size:1rem;margin-bottom:0px;'>{region} <span style='font-size:0.9rem;color:#888;'>({region_stats_text})</span></span>", unsafe_allow_html=True)
        slider_val = st.slider(
            f"{region} Cost",
            min_value=min_val,
            max_value=max_val,
            value=avg_val,
            step=0.01,
            key=f"cost_slider_{region}",
            label_visibility="collapsed"
        )
        st.session_state["regional_custom_cost"][region] = slider_val
    # Coverage settings
    coverage = st.slider("Coverage Target", 0, 100, 80)
    # Newborn settings
    newborn_goats = st.number_input("Goats (% of initial population)", 0, 100, 60)
    newborn_sheep = st.number_input("Sheep (% of initial population)", 0, 100, 40)
    second_year_coverage_val = st.slider("Second Year Coverage", 0, 100, 100)
    # Wastage and delivery settings
    wastage = st.slider("Wastage Rate", 0, 100, 10)
    delivery_channel = st.radio("Delivery Channel", ["Public", "Mixed", "Private"], index=1)
    del_mult_public = st.number_input("Public", 0.0, 5.0, 1.2)
    del_mult_mixed = st.number_input("Mixed", 0.0, 5.0, 1.0)
    del_mult_private = st.number_input("Private", 0.0, 5.0, 0.85)
    # Political stability settings
    st.markdown("<span style='font-weight:600;font-size:1.1rem;'>Political Stability Index (PSI)</span>", unsafe_allow_html=True)
    thresh_low = st.number_input("Low threshold", -2.5, 2.5, -1.0)
    thresh_high = st.number_input("High threshold", -2.5, 2.5, 0.0)
    mult_high_risk = st.number_input("Multiplier for high risk (index < low)", 1.0, 5.0, 2.0)
    mult_moderate_risk = st.number_input("Multiplier for moderate risk (low ≤ index < high)", 1.0, 5.0, 1.5)
    mult_low_risk = st.number_input("Multiplier for low risk (index ≥ high)", 1.0, 5.0, 1.0)

# Store all config values in session state
config = {
    "scenario_name": scenario_name,
    "coverage": coverage,
    "newborn_goats": newborn_goats,
    "newborn_sheep": newborn_sheep,
    "second_year_coverage": second_year_coverage_val,
    "wastage": wastage,
    "delivery_channel": delivery_channel,
    "delivery_multipliers": {
        "Public": del_mult_public,
        "Mixed": del_mult_mixed,
        "Private": del_mult_private
    },
    "political_stability": {
        "thresh_low": thresh_low,
        "thresh_high": thresh_high,
        "mult_high_risk": mult_high_risk,
        "mult_moderate_risk": mult_moderate_risk,
        "mult_low_risk": mult_low_risk
    }
}

st.session_state["config"] = config

# Load data
with st.spinner("Loading data..."):
    data = load_data()
    national_df = data["national_df"]
    subregions_df = data["subregions_df"]

# Calculate political stability multiplier based on index
def get_political_mult(psi, config):
    """Get political stability multiplier based on PSI and thresholds"""
    if psi < config["political_stability"]["thresh_low"]:
        return config["political_stability"]["mult_high_risk"]
    elif psi < config["political_stability"]["thresh_high"]:
        return config["political_stability"]["mult_moderate_risk"]
    else:
        return config["political_stability"]["mult_low_risk"]

# Calculate statistics for each country
country_stats = {}
for idx, row in national_df.iterrows():
    country = row["Country"]
    species = str(row["Species"]).capitalize()
    pop = row["Population"] if pd.notnull(row["Population"]) else 0
    coverage_frac = config["coverage"] / 100.0
    vaccinated = vaccinated_initial(pop, coverage_frac)
    doses = doses_required(vaccinated, config["wastage"]/100)
    region = country_region_map.get(country, "West Africa")
    cost_per_animal = st.session_state["regional_custom_cost"][region]
    cost_before_adj_val = cost_before_adj(doses, cost_per_animal)
    psi = row["Political_Stability_Index"] if pd.notnull(row["Political_Stability_Index"]) else 0.3
    political_mult = get_political_mult(psi, config)
    delivery_mult = config["delivery_multipliers"][config["delivery_channel"]]
    total_cost_val = total_cost(cost_before_adj_val, political_mult, delivery_mult)
    vaccines_wasted = doses - vaccinated

    # Initialize country stats if not exists
    if country not in country_stats:
        country_stats[country] = {
            "Y1": {"Goat": 0, "Sheep": 0, "doses": 0, "cost": 0, "wasted": 0},
            "Y2": {"Goat": 0, "Sheep": 0, "doses": 0, "cost": 0, "wasted": 0}
        }

    # Update Y1 stats
    if species in ["Goat", "Goats"]:
        country_stats[country]["Y1"]["Goat"] += vaccinated
    elif species in ["Sheep", "Sheeps"]:
        country_stats[country]["Y1"]["Sheep"] += vaccinated
    country_stats[country]["Y1"]["doses"] += doses
    country_stats[country]["Y1"]["cost"] += total_cost_val
    country_stats[country]["Y1"]["wasted"] += vaccines_wasted

    # Calculate and update Y2 stats
    newborn_rate = config["newborn_goats"]/100 if species in ["Goat", "Goats"] else config["newborn_sheep"]/100
    newborn_count = vaccinated * newborn_rate
    second_year_coverage_frac = config["second_year_coverage"] / 100.0
    vaccinated_y2 = second_year_coverage(newborn_count, second_year_coverage_frac)
    doses_y2 = doses_required(vaccinated_y2, config["wastage"]/100)
    cost_before_adj_val = cost_before_adj(doses_y2, cost_per_animal)
    total_cost_val = total_cost(cost_before_adj_val, political_mult, delivery_mult)
    vaccines_wasted = doses_y2 - vaccinated_y2

    if species in ["Goat", "Goats"]:
        country_stats[country]["Y2"]["Goat"] += vaccinated_y2
    elif species in ["Sheep", "Sheeps"]:
        country_stats[country]["Y2"]["Sheep"] += vaccinated_y2
    country_stats[country]["Y2"]["doses"] += doses_y2
    country_stats[country]["Y2"]["cost"] += total_cost_val
    country_stats[country]["Y2"]["wasted"] += vaccines_wasted

# Create tabs
tabs = st.tabs([
    "Scenario Builder",
    "Episystems",
    "Continental Overview", 
    "Regions & Countries",
    "Subregions",
    "Methodology & Data Sources"
])

# Render each tab
with tabs[0]:
    scenario_builder.render_tab(subregions_df)

with tabs[1]:
    episystems.render_tab(subregions_df)

with tabs[2]:
    continental_overview.render_tab(country_stats, national_df)

with tabs[3]:
    regions_countries.render_tab(country_stats)

with tabs[4]:
    subregions.render_tab(subregions_df, national_df)

with tabs[5]:
    methodology.render_tab(national_df)
