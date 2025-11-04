"""
Subregions tab for PPR Vaccination Cost Dashboard
"""

import streamlit as st
import pandas as pd
from cost_data import country_region_map

def format_table_values(df, numeric_columns):
    """Format numeric values in DataFrame for display"""
    df = df.copy()
    for col in numeric_columns:
        if col in df:
            df[col] = df[col].map(lambda x: f"{int(float(x)):,}" if pd.notnull(x) and x != 0 else "0")
    return df

def clean_population(value):
    """Clean population value from raw data"""
    if pd.isna(value) or value == "Unknown":
        return 0
    return float(str(value).replace(',', ''))

def vaccinated_initial(population, coverage):
    """Calculate number of animals vaccinated in first year"""
    return population * coverage

def doses_required(vaccinated, wastage_rate):
    """Calculate doses required including wastage"""
    return vaccinated * (1 + wastage_rate)

def cost_before_adj(doses, cost_per_animal):
    """Calculate base cost before adjustments"""
    return doses * cost_per_animal

def total_cost(cost_base, political_mult, delivery_mult):
    """Calculate total cost with all multipliers"""
    return cost_base * political_mult * delivery_mult

def second_year_coverage(newborns, coverage):
    """Calculate second year vaccination coverage"""
    return newborns * coverage

def get_political_mult(psi, config):
    """Get political stability multiplier based on PSI and thresholds"""
    if psi < config["political_stability"]["thresh_low"]:
        return config["political_stability"]["mult_high_risk"]
    elif psi < config["political_stability"]["thresh_high"]:
        return config["political_stability"]["mult_moderate_risk"]
    else:
        return config["political_stability"]["mult_low_risk"]

def render_tab(subregions_df, national_df):
    """Render the Subregions tab"""
    st.subheader("Subregion Breakdown")
    
    # Get configuration from session state
    config = st.session_state.get('config', {})
    
    # List of PPR-free countries to exclude
    ppr_free_countries = {
        "Botswana", "eSwatini", "Eswatini", "Lesotho", "Madagascar", 
        "Mauritius", "Namibia", "South Africa", "Kingdom of eSwatini"
    }
    
    # Country selection (excluding PPR-free countries)
    available_countries = sorted(set(subregions_df["Country"]) - ppr_free_countries)
    selected_country = st.selectbox("Select Country", available_countries)
    subregion_data = subregions_df[subregions_df["Country"] == selected_country]
    
    # Group data by Subregion to aggregate species
    from collections import defaultdict
    grouped_subregion_data = defaultdict(lambda: {"goats_data": None, "sheep_data": None})
    
    for idx, row in subregion_data.iterrows():
        subregion = row["Subregion"] if pd.notnull(row["Subregion"]) else "Unknown"
        
        # Handle different species column names
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
    
    # Build subregion breakdown table
    subregion_table = []
    for subregion, species_data in grouped_subregion_data.items():
        goats_data = species_data["goats_data"]
        sheep_data = species_data["sheep_data"]
        
        # Get Political Stability Index from national data
        country_data = national_df[national_df["Country"] == selected_country]
        psi = country_data["Political_Stability_Index"].iloc[0] if not country_data.empty and pd.notnull(country_data["Political_Stability_Index"].iloc[0]) else 0.3
        
        # Get region and cost per animal
        region = country_region_map.get(selected_country, "West Africa")
        cost_per_animal = st.session_state.get(f"cost_slider_{region}", 0)
        
        # Calculate political stability and delivery multipliers
        political_mult = get_political_mult(psi, config)
        delivery_mult = config["delivery_multipliers"][config["delivery_channel"]]
        
        # Initialize row data
        row = {
            "Subregion": subregion,
            "Political_Stability_Index": f"{psi:.3f}",
            "Goats Y1": 0, "Sheep Y1": 0, "Total Y1": 0,
            "Cost Y1": 0, "Doses Y1": 0, "Wasted Y1": 0,
            "Goats Y2": 0, "Sheep Y2": 0, "Total Y2": 0,
            "Cost Y2": 0, "Doses Y2": 0, "Wasted Y2": 0,
            "Total Campaign Cost": 0
        }
        
        # Calculate Y1 stats for goats
        if goats_data is not None:
            pop_raw = goats_data["100%_Coverage"] if pd.notnull(goats_data["100%_Coverage"]) else 0
            try:
                population = clean_population(pop_raw)
                coverage_frac = config["coverage"] / 100.0
                vaccinated = vaccinated_initial(population, coverage_frac)
                doses = doses_required(vaccinated, config["wastage"]/100)
                cost_before_adj_val = cost_before_adj(doses, cost_per_animal)
                total_cost_val = total_cost(cost_before_adj_val, political_mult, delivery_mult)
                
                row["Goats Y1"] = int(vaccinated)
                row["Doses Y1"] += doses
                row["Cost Y1"] += total_cost_val
                row["Wasted Y1"] += doses - vaccinated
                
                # Calculate Y2 stats
                newborn_rate = config["newborn_goats"] / 100
                newborn_count = vaccinated * newborn_rate
                second_year_coverage_frac = config["second_year_coverage"] / 100.0
                vaccinated_y2 = second_year_coverage(newborn_count, second_year_coverage_frac)
                doses_y2 = doses_required(vaccinated_y2, config["wastage"]/100)
                cost_before_adj_val = cost_before_adj(doses_y2, cost_per_animal)
                total_cost_val_y2 = total_cost(cost_before_adj_val, political_mult, delivery_mult)
                
                row["Goats Y2"] = int(vaccinated_y2)
                row["Doses Y2"] += doses_y2
                row["Cost Y2"] += total_cost_val_y2
                row["Wasted Y2"] += doses_y2 - vaccinated_y2
            except (ValueError, TypeError):
                pass

        # Calculate Y1 stats for sheep
        if sheep_data is not None:
            pop_raw = sheep_data["100%_Coverage"] if pd.notnull(sheep_data["100%_Coverage"]) else 0
            try:
                population = clean_population(pop_raw)
                coverage_frac = config["coverage"] / 100.0
                vaccinated = vaccinated_initial(population, coverage_frac)
                doses = doses_required(vaccinated, config["wastage"]/100)
                cost_before_adj_val = cost_before_adj(doses, cost_per_animal)
                total_cost_val = total_cost(cost_before_adj_val, political_mult, delivery_mult)
                
                row["Sheep Y1"] = int(vaccinated)
                row["Doses Y1"] += doses
                row["Cost Y1"] += total_cost_val
                row["Wasted Y1"] += doses - vaccinated
                
                # Calculate Y2 stats
                newborn_rate = config["newborn_sheep"] / 100
                newborn_count = vaccinated * newborn_rate
                second_year_coverage_frac = config["second_year_coverage"] / 100.0
                vaccinated_y2 = second_year_coverage(newborn_count, second_year_coverage_frac)
                doses_y2 = doses_required(vaccinated_y2, config["wastage"]/100)
                cost_before_adj_val = cost_before_adj(doses_y2, cost_per_animal)
                total_cost_val_y2 = total_cost(cost_before_adj_val, political_mult, delivery_mult)
                
                row["Sheep Y2"] = int(vaccinated_y2)
                row["Doses Y2"] += doses_y2
                row["Cost Y2"] += total_cost_val_y2
                row["Wasted Y2"] += doses_y2 - vaccinated_y2
            except (ValueError, TypeError):
                pass
        
        row["Total Y1"] = row["Goats Y1"] + row["Sheep Y1"]
        row["Total Y2"] = row["Goats Y2"] + row["Sheep Y2"]
        
        # Format cost values as currency
        campaign_total = row["Cost Y1"] + row["Cost Y2"]
        row["Cost Y1"] = f"${row['Cost Y1']:,.2f}"
        row["Cost Y2"] = f"${row['Cost Y2']:,.2f}"
        row["Total Campaign Cost"] = f"${campaign_total:,.2f}"
        
        if row["Total Y1"] > 0 or row["Total Y2"] > 0:
            subregion_table.append(row)
    
    if subregion_table:
        # Convert to DataFrame and format for display
        subregion_table_df = pd.DataFrame(subregion_table)
        display_cols = [
            "Subregion", "Political_Stability_Index", 
            "Goats Y1", "Sheep Y1", "Total Y1", "Cost Y1", "Doses Y1", "Wasted Y1",
            "Goats Y2", "Sheep Y2", "Total Y2", "Cost Y2", "Doses Y2", "Wasted Y2",
            "Total Campaign Cost"
        ]
        numeric_cols = [
            "Goats Y1", "Sheep Y1", "Total Y1", "Doses Y1", "Wasted Y1",
            "Goats Y2", "Sheep Y2", "Total Y2", "Doses Y2", "Wasted Y2"
        ]
        
        subregion_display_df = format_table_values(subregion_table_df[display_cols], numeric_cols)
        st.dataframe(subregion_display_df, height=len(subregion_table)*35+40, width=1400)
    else:
        st.info(f"No data available for {selected_country}'s subregions.")
