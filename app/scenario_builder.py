"""
Scenario Builder tab for PPR Vaccination Cost Dashboard
"""

import streamlit as st
import pandas as pd
import folium
import requests
from cost_data import country_coords, country_iso3
from calculations import (
    vaccinated_initial, doses_required, cost_before_adj,
    political_multiplier, delivery_channel_multiplier,
    newborns, second_year_coverage, total_cost
)

# Check if streamlit-folium is available
try:
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    st.error("""
    Error: The streamlit-folium package is required for map visualization.
    Install it with: pip install streamlit-folium
    """)

def format_table_values(df, numeric_columns):
    """Format numeric values in DataFrame for display"""
    df = df.copy()
    for col in numeric_columns:
        if col in df:
            df[col] = df[col].map(lambda x: f"{int(float(x)):,}" if pd.notnull(x) and x != 0 else "0")
    return df

@st.cache_data(ttl=86400)
def get_country_shape(country_name):
    """Get country shape from UN geoservice"""
    iso3 = country_iso3.get(country_name)
    if not iso3:
        return None
    
    try:
        # UN geoservice API endpoint for country shapes (layer 109)
        url = f"https://geoservices.un.org/arcgis/rest/services/ClearMap_WebTopo/MapServer/109/query"
        params = {
            'where': f"ISO3CD='{iso3}'",
            'outFields': '*',
            'returnGeometry': 'true',
            'f': 'geojson'
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and data.get('features'):
                return data
            else:
                st.warning(f"No shape data found for {country_name}")
        else:
            st.error(f"Error fetching shape for {country_name}: {response.status_code}")
    except Exception as e:
        st.error(f"Error loading country shape: {str(e)}")
    return None

@st.cache_data(ttl=86400)
def get_region_shape(country_name):
    """Get regional shapes from geoBoundaries"""
    iso3 = country_iso3.get(country_name)
    if not iso3:
        st.warning(f"No ISO3 code found for {country_name}")
        return None
    
    try:
        meta_url = f"https://www.geoboundaries.org/api/current/gbOpen/{iso3}/ADM1"
        meta_resp = requests.get(meta_url, timeout=10)
        if meta_resp.status_code != 200:
            st.warning(f"Failed to get metadata for {country_name}: {meta_resp.status_code}")
            return None
            
        meta = meta_resp.json()
        gj_url = meta.get("gjDownloadURL", "").strip()
        if not gj_url:
            st.warning(f"No GeoJSON URL found for {country_name}")
            return None
            
        gj_resp = requests.get(gj_url, timeout=10)
        if gj_resp.status_code == 200:
            return gj_resp.json()
        else:
            st.warning(f"Failed to get GeoJSON for {country_name}: {gj_resp.status_code}")
    except Exception as e:
        st.error(f"Error fetching region shapes for {country_name}: {str(e)}")
    return None

# Pre-define map style configuration
MAP_STYLE = {
    "fillColor": "red",
    "color": "darkred",
    "weight": 2,
    "fillOpacity": 0.4,
    "dashArray": "5, 5"
}

import difflib

def update_map_with_regions(m, selected_regions_data):
    """Update map with selected regions"""
    if not selected_regions_data:
        return m
        
    # Process each country's selection
    for country in set(entry['Country'] for entry in selected_regions_data):
        region_option = st.session_state.get(f"region_option_{country}", "All regions")
        
        if region_option == "All regions":
            # Load country shape
            country_geojson = get_country_shape(country)
            if country_geojson and country_geojson.get('features'):
                folium.GeoJson(
                    country_geojson,
                    style_function=lambda x: MAP_STYLE,
                    popup=folium.Popup(f"<b>{country}</b>", parse_html=True),
                    tooltip=country
                ).add_to(m)
            else:
                # Fallback to marker if no GeoJSON data
                coords = country_coords.get(country)
                if coords:
                    folium.Marker(
                        location=coords,
                        popup=country,
                        icon=folium.Icon(color='red', icon='info-sign')
                    ).add_to(m)
        else:
            # Load specific regions
            regions_geojson = get_region_shape(country)
            selected_regions = st.session_state.get(f"regions_{country}", [])
            
            if regions_geojson and regions_geojson.get('features'):

                for region in selected_regions:
                    found = False
                    region_lower = region.lower().strip()
                    
                    for feature in regions_geojson['features']:
                        props = feature['properties']
                        
                        # Try all possible property names that might contain region name
                        for prop_name in props.keys():
                            if 'name' in prop_name.lower() or 'shap' in prop_name.lower():
                                feature_name = str(props[prop_name]).lower().strip()
                                
                                # Try exact match first
                                if feature_name == region_lower:
                                    folium.GeoJson(
                                        feature,
                                        style_function=lambda x: MAP_STYLE,
                                        popup=folium.Popup(f"<b>{region}, {country}</b>", parse_html=True),
                                        tooltip=f"{region}, {country}"
                                    ).add_to(m)
                                    found = True
                                    break
                                
                                # Try fuzzy matching if exact match fails
                                ratio = difflib.SequenceMatcher(None, feature_name, region_lower).ratio()
                                if ratio > 0.85:  # Threshold for fuzzy matching
                                    folium.GeoJson(
                                        feature,
                                        style_function=lambda x: MAP_STYLE,
                                        popup=folium.Popup(f"<b>{region}, {country}</b>", parse_html=True),
                                        tooltip=f"{region}, {country}"
                                    ).add_to(m)
                                    found = True
                                    break
                        
                        if found:
                            break
                            
                    if not found:
                        # Log region matching issue
                        st.warning(
                            f"Could not find shape data for region '{region}' in {country}. "
                            "This might be due to naming differences between the data sources."
                        )
            else:
                # Fallback to marker if no GeoJSON data
                coords = country_coords.get(country)
                if coords:
                    folium.Marker(
                        location=coords,
                        popup=country,
                        icon=folium.Icon(color='red', icon='info-sign')
                    ).add_to(m)
    
    return m

@st.cache_data(show_spinner=False)
def get_initial_map():
    """Get cached initial map with error handling"""
    try:
        m = folium.Map(location=[0, 20], zoom_start=3, tiles=None)
        folium.TileLayer(
            tiles='https://geoservices.un.org/arcgis/rest/services/ClearMap_WebTopo/MapServer/tile/{z}/{y}/{x}',
            attr='UN Clear Map',
            name='UN Clear Map',
            overlay=False,
            control=True
        ).add_to(m)
        return m
    except Exception as e:
        st.error(f"Error initializing map: {str(e)}")
        return None

def render_tab(subregions_df):
    """Render the Scenario Builder tab"""
    
    st.markdown("""
    **Build Custom Vaccination Scenarios**

    This tool allows you to create targeted vaccination scenarios by adjusting parameters in the sidebar and selecting specific countries and regions for analysis. Use the sidebar controls to modify coverage rates, regional costs, political stability factors, and delivery channels - all calculations will update automatically across all tabs. Below, you can select particular countries and their subnational regions to focus your analysis on specific geographic areas, such as border regions, episystems, or outbreak-prone zones. The results table will show vaccination costs and logistics only for your selected areas.

    **Tab Guide:**
    - **Episystems**: Analyze vaccination scenarios for the eight transboundary epidemiological systems in Africa, focusing on cross-border animal movement patterns and disease risk factors
    - **Continental Overview**: Total vaccination impact across all of Africa
    - **Regions & Countries**: Breakdown by African regions and individual countries  
    - **Subregions**: Detailed view of subnational areas within a single country
    - **Scenario Builder** (this tab): Create custom scenarios by selecting specific countries/regions
    """)

    st.markdown("---")
    st.markdown("**Select Countries and Subnational Regions for Custom Scenario:**")
    # Load countries once and cache
    if "available_countries" not in st.session_state:
        st.session_state.available_countries = sorted(subregions_df["Country"].unique())
    
    selected_countries = st.multiselect(
        "Select Countries:", 
        st.session_state.available_countries, 
        key="scenario_countries"
    )
    selected_regions_data = []
    if selected_countries:
        st.markdown("**Configure regions for each selected country:**")
        for country in selected_countries:
            st.markdown(f"**{country}:**")
            col1, col2 = st.columns([1, 2])
            with col1:
                region_option = st.radio(
                    f"Regions for {country}:",
                    ["All regions", "Select specific regions"],
                    key=f"region_option_{country}"
                )
            with col2:
                if region_option == "Select specific regions":
                    country_regions = sorted(subregions_df[subregions_df["Country"] == country]["Subregion"].unique())
                    selected_regions = st.multiselect(
                        f"Select regions in {country}:",
                        country_regions,
                        key=f"regions_{country}"
                    )
                    for region in selected_regions:
                        region_data = subregions_df[
                            (subregions_df["Country"] == country) &
                            (subregions_df["Subregion"] == region)
                        ]
                        selected_regions_data.extend(region_data.to_dict('records'))
                else:
                    country_data = subregions_df[subregions_df["Country"] == country]
                    selected_regions_data.extend(country_data.to_dict('records'))

        # Display the map after selections
        st.markdown("---")
        st.markdown("**Map of Selected Countries and Regions:**")
        
        if FOLIUM_AVAILABLE:
            # Get map object (cached)
            map_obj = get_initial_map()
            if map_obj:
                try:
                    if selected_regions_data:
                        with st.spinner("Loading region data..."):
                            updated_map = update_map_with_regions(map_obj, selected_regions_data)
                            st_folium(updated_map, width=800, height=400, key=f"scenario_map_{len(selected_regions_data)}")
                    else:
                        # Show initial map
                        st_folium(map_obj, width=800, height=400, key="scenario_map_initial")
                except Exception as e:
                    st.error(f"Error loading map: {str(e)}")
                    st.info("The map visualization is temporarily unavailable. You can still continue with region selection.")
        st.caption("The boundaries and names shown and the designations used on this map do not imply the expression of any opinion whatsoever on the part of FAO concerning the legal status of any country, territory, city or area or of its authorities, or concerning the delimitation of its frontiers and boundaries")

        # Add Calculate button and display results
        calculate_clicked = st.button("Calculate", key="calculate_scenario")
        if calculate_clicked and selected_regions_data:
            display_scenario_results(selected_regions_data)

def display_scenario_results(selected_regions_data):
    """Display the results of scenario calculations"""
    st.markdown("---")
    st.markdown("**Custom Scenario Results:**")
    
    from collections import defaultdict
    grouped_data = defaultdict(lambda: {"goats_data": None, "sheep_data": None})
    
    # Group data by Country and Subregion
    for row_data in selected_regions_data:
        country = row_data["Country"]
        subregion = row_data["Subregion"] if pd.notnull(row_data["Subregion"]) else "Unknown"
        key = (country, subregion)
        
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
    

    # Build results table
    results_table = []
    for (country, subregion), species_data in grouped_data.items():
        row = {"Country": country, "Subregion": subregion}
        
        # Calculate for both years
        for year in [1, 2]:
            # Get data for each species
            goats_data = species_data["goats_data"] or {}
            sheep_data = species_data["sheep_data"] or {}
            
            
            def calculate_costs(data, year):
                if not data:
                    return {}
                
                try:
                    # Get scenario parameters from session state
                    params = st.session_state.scenario_params
                    
                    # Initial vaccination calculations with user-defined parameters
                    base_population = float(data.get('100%_Coverage', 0))  # Base population from 100% coverage
                    population = base_population
                    coverage = params['coverage_rate']
                    wastage = params['wastage_rate']
                    cost_per_animal = params['cost_per_animal']
                    psi = params['psi']  # Use PSI from user input
                    delivery = params['delivery_channel']
                    species = data.get('Specie') or data.get('Species', 'Unknown')
                    
                    # Year 1 calculations
                    if year == 1:
                        vacc_init = vaccinated_initial(population, coverage)
                        doses = doses_required(vacc_init, wastage)
                        cost_adj = cost_before_adj(doses, cost_per_animal)
                        pol_mult = political_multiplier(psi)
                        del_mult = delivery_channel_multiplier(delivery)
                        final_cost = total_cost(cost_adj, pol_mult, del_mult)
                        return {
                            'animals_vaccinated': vacc_init,
                            'doses_needed': doses,
                            'doses_wasted': doses - vacc_init,
                            'total_cost': final_cost
                        }
                    # Year 2 calculations
                    else:
                        vacc_init = vaccinated_initial(population, coverage)
                        new_animals = newborns(species, vacc_init)
                        vacc_y2 = second_year_coverage(new_animals)
                        doses = doses_required(vacc_y2, wastage)
                        cost_adj = cost_before_adj(doses, cost_per_animal)
                        pol_mult = political_multiplier(psi)
                        del_mult = delivery_channel_multiplier(delivery)
                        final_cost = total_cost(cost_adj, pol_mult, del_mult)
                        return {
                            'animals_vaccinated': vacc_y2,
                            'doses_needed': doses,
                            'doses_wasted': doses - vacc_y2,
                            'total_cost': final_cost
                        }
                except Exception as e:
                    st.error(f"Calculation error: {str(e)}")
                    return {}

            # Calculate costs for each species
            goat_results = calculate_costs(goats_data, year)
            sheep_results = calculate_costs(sheep_data, year)

            
            # Extract values with fallbacks to 0
            row[f"Goats Y{year}"] = goat_results.get('animals_vaccinated', 0)
            row[f"Sheep Y{year}"] = sheep_results.get('animals_vaccinated', 0)
            row[f"Total Y{year}"] = row[f"Goats Y{year}"] + row[f"Sheep Y{year}"]
            row[f"Cost Y{year}"] = (goat_results.get('total_cost', 0) + 
                                  sheep_results.get('total_cost', 0))
            row[f"Doses Y{year}"] = (goat_results.get('doses_needed', 0) + 
                                   sheep_results.get('doses_needed', 0))
            row[f"Wasted Y{year}"] = (goat_results.get('doses_wasted', 0) + 
                                    sheep_results.get('doses_wasted', 0))
        
        results_table.append(row)
    
    # Convert to DataFrame and format for display
    results_df = pd.DataFrame(results_table)
    
    # Calculate campaign totals
    total_animals_y1 = results_df["Total Y1"].sum()
    total_animals_y2 = results_df["Total Y2"].sum()
    total_doses_y1 = results_df["Doses Y1"].sum()
    total_doses_y2 = results_df["Doses Y2"].sum()
    total_wasted_y1 = results_df["Wasted Y1"].sum()
    total_wasted_y2 = results_df["Wasted Y2"].sum()
    total_cost_y1 = results_df["Cost Y1"].sum()
    total_cost_y2 = results_df["Cost Y2"].sum()
    total_campaign_cost = total_cost_y1 + total_cost_y2

    config = st.session_state.get('config', {})
    region_costs = {
        'North Africa': f"${st.session_state.get('cost_slider_North Africa', '')}",
        'West Africa': f"${st.session_state.get('cost_slider_West Africa', '')}",
        'Central Africa': f"${st.session_state.get('cost_slider_Central Africa', '')}",
        'East Africa': f"${st.session_state.get('cost_slider_East Africa', '')}",
        'Southern Africa': f"${st.session_state.get('cost_slider_Southern Africa', '')}"
    }
    st.markdown("""
    <div style='background-color:#f0f2f6; padding:20px; border-radius:10px; margin:20px 0;'>
        <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
            <div style='text-align:left; flex:1;'>
                <div style='font-size:1.4em; font-weight:600; margin-bottom:10px;'>Total Campaign Cost</div>
                <div style='font-size:2em; font-weight:700; color:#0066cc;'>
                    ${:,.2f}
                </div>
                <div style='font-size:1.1em; color:#666; margin-top:10px;'>
                    Year 1: ${:,.2f} &nbsp;|&nbsp; Year 2: ${:,.2f}
                </div>
            </div>
            <div style='display:flex; flex:2;'>
                <div style='flex:1; border-left:1px solid #ddd; padding-left:20px;'>
                    <div style='font-size:1.2em; font-weight:600; margin-bottom:10px;'>Regional Costs:</div>
                    <div style='font-size:1em; color:#444;'>
                        <div style='margin-bottom:8px;'><b>North Africa:</b> {}</div>
                        <div style='margin-bottom:8px;'><b>West Africa:</b> {}</div>
                        <div style='margin-bottom:8px;'><b>Central Africa:</b> {}</div>
                        <div style='margin-bottom:8px;'><b>East Africa:</b> {}</div>
                        <div style='margin-bottom:8px;'><b>Southern Africa:</b> {}</div>
                    </div>
                </div>
                <div style='flex:1; border-left:1px solid #ddd; padding-left:20px;'>
                    <div style='font-size:1.2em; font-weight:600; margin-bottom:10px;'>Scenario Parameters:</div>
                    <div style='font-size:1em; color:#444;'>
                        <div style='margin-bottom:8px;'><b>Coverage Target:</b> {}%</div>
                        <div style='margin-bottom:8px;'><b>Newborn Goats:</b> {}%</div>
                        <div style='margin-bottom:8px;'><b>Newborn Sheep:</b> {}%</div>
                        <div style='margin-bottom:8px;'><b>Second Year Coverage:</b> {}%</div>
                        <div style='margin-bottom:8px;'><b>Wastage Rate:</b> {}%</div>
                        <div style='margin-bottom:8px;'><b>Delivery Channel:</b> {} (Public: {}, Mixed: {}, Private: {})</div>
                        <div style='margin-bottom:8px;'><b>Political Stability Risk:</b> High: {}, Moderate: {}, Low: {}</div>
                        <div style='margin-bottom:8px;'><b>PSI Index:</b> {}</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """.format(
        total_campaign_cost, total_cost_y1, total_cost_y2,
        region_costs['North Africa'],
        region_costs['West Africa'],
        region_costs['Central Africa'],
        region_costs['East Africa'],
        region_costs['Southern Africa'],
        config.get('coverage', 0),
        config.get('newborn_goats', 0),
        config.get('newborn_sheep', 0),
        config.get('second_year_coverage', 0),
        config.get('wastage', 0),
        config.get('delivery_channel', ''),
        config.get('delivery_multipliers', {}).get('Public', ''),
        config.get('delivery_multipliers', {}).get('Mixed', ''),
        config.get('delivery_multipliers', {}).get('Private', ''),
        config.get('political_stability', {}).get('mult_high_risk', ''),
        config.get('political_stability', {}).get('mult_moderate_risk', ''),
        config.get('political_stability', {}).get('mult_low_risk', ''),
        config.get('psi', '')
    ), unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### Detailed Results by Region")
    display_cols = [
        "Country", "Subregion", "Goats Y1", "Sheep Y1", "Total Y1", "Cost Y1",
        "Doses Y1", "Wasted Y1", "Goats Y2", "Sheep Y2", "Total Y2", "Cost Y2",
        "Doses Y2", "Wasted Y2"
    ]
    numeric_cols = [
        "Goats Y1", "Sheep Y1", "Total Y1", "Doses Y1", "Wasted Y1",
        "Goats Y2", "Sheep Y2", "Total Y2", "Doses Y2", "Wasted Y2"
    ]
    
    results_display_df = format_table_values(results_df[display_cols], numeric_cols)
    st.dataframe(results_display_df, width="stretch")
