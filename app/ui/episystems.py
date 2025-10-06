"""
Episystems Analysis tab for PPR Vaccination Cost Dashboard
"""

import streamlit as st
import pandas as pd
from .calculations import (
    vaccinated_initial, doses_required, cost_before_adj,
    political_multiplier, delivery_channel_multiplier,
    newborns, second_year_coverage, total_cost
)

def format_table_values(df, numeric_columns):
    """Format numeric values in DataFrame for display"""
    df = df.copy()
    for col in numeric_columns:
        if col in df:
            df[col] = df[col].map(lambda x: f"{int(float(x)):,}" if pd.notnull(x) and x != 0 else "0")
    return df

def render_tab(subregions_df):
    """Render the Episystems tab"""
    
    st.markdown("""
    ## Episystem-Based, Risk-Targeted Vaccination

    This strategy focuses vaccination exclusively within the eight transboundary episystems defined in the Framework for PPR Eradication in Africa [1]. An episystem is understood as a network of interconnected small ruminant populations, typically spanning multiple countries—where PPR virus circulation is sustained by cross-border animal movements, trade, and shared pastoral systems.

    These episystems represent critical zones for PPR persistence and spread, making them strategic targets for coordinated vaccination efforts. By focusing on these interconnected animal populations, the strategy aims to efficiently disrupt virus transmission pathways across borders.

    **Reference:**  
    [1] African Union – Inter-African Bureau for Animal Resources (AU-IBAR). (2025). Framework for PPR Eradication in Africa (Draft, 11 September 2025). Nairobi: AU-IBAR.
    """)
    
    # Add parameter controls in sidebar with unique keys
    st.sidebar.markdown("### Scenario Parameters")
    coverage_rate = st.sidebar.slider("Coverage Rate (%)", 50, 100, 80, key="episystem_coverage") / 100
    wastage_rate = st.sidebar.slider("Wastage Rate (%)", 0, 30, 15, key="episystem_wastage") / 100
    cost_per_animal = st.sidebar.slider("Cost per Animal ($)", 0.1, 1.0, 0.25, 0.05, key="episystem_cost")
    psi = st.sidebar.slider("Political Stability Index", -2.5, 2.5, 0.5, 0.1, key="episystem_psi")
    delivery_channel = st.sidebar.selectbox("Delivery Channel", ["Public", "Mixed", "Private"], index=1, key="episystem_delivery")
    
    # Store parameters in session state
    st.session_state.scenario_params = {
        'coverage_rate': coverage_rate,
        'wastage_rate': wastage_rate,
        'cost_per_animal': cost_per_animal,
        'psi': psi,
        'delivery_channel': delivery_channel
    }
    
    # Display the PPR episystems map and episystems info side by side
    col1, col2 = st.columns([1,1])
    
    with col1:
        st.image("./public/pprepisystems.png", caption="PPR Episystems in Africa", width="stretch")
    
    with col2:
        st.markdown("""
        <style>
        .episystem-container {
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-bottom: 10px;
            padding: 10px;
            background-color: #f8f9fa;
        }
        .episystem-title {
            font-size: 1.1em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
        }
        .country-title {
            font-weight: bold;
            color: #34495e;
            margin-top: 5px;
        }
        .region-list {
            margin: 0;
            padding-left: 20px;
            color: #576574;
            font-size: 0.9em;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("### PPR Episystems and Their Regions")
        
        # Define the episystems and their regions in specific order
        episystems_data = {
            "Chad-Sudan (DARFUR)": {
                "Chad": ["Ouaddai", "Sila", "Batha Est", "Batha Ouest", "Biltine"],
                "Sudan": ["North Darfur", "South Darfur", "West Darfur"]
            },
            "Karamoja": {
                "Uganda": ["Kotido", "Kitgum", "Moroto", "Lira", "Soroti"],
                "Kenya": ["Rift Valley"],
                "Ethiopia": ["SNNP"],
                "South Sudan": ["Eastern Equatoria"]
            },
            "Mano River": {
                "Guinea": ["Faranah", "Kankan", "N'Zerekore"],
                "Sierra Leone": ["Northern", "Eastern"],
                "Liberia": ["Lofa", "Nimba", "Bong", "Gbarpolu"],
                "Côte d'Ivoire": ["18 Montagnes", "Denguele", "Bafing", "Haut-Sassandra", "Worodougou"]
            },
            "Sahel": {
                "Senegal": ["Saint-Louis"],
                "Mauritania": ["Brakna", "Tagant", "Assaba", "Gorgol", "Guidimakha", "Hodh Ech Chargi", "Hodh El Gharbi"],
                "Mali": ["Bamako", "Mopti", "Tombouctou", "Gao", "Kidal", "Segou"],
                "Niger": ["Agadez", "Diffa", "Dosso", "Maradi", "Niamey", "Tahoua", "Tillaberi", "Zinder"],
                "Chad": ["Hadjer Lamis", "Lac", "Kanem", "Barh El Gazal"],
                "Burkina Faso": ["Sahel", "Nord", "Centre-Nord", "Est", "Plateau Central", "Centre-Est"],
                "Benin": ["Atacora", "Alibori"],
                "Nigeria": ["Kebbi", "Zamfara", "Sokoto", "Katsina", "Kano", "Jigawa", "Yobe", "Borno"]
            },
            "Southern Protection Zone": {
                "Angola": ["Moxico", "Lunda Sul"],
                "Burundi": ["Bubanza", "Bujumbura-Mairie", "Bujumbura-Rural", "Bururi", "Cankuzo", "Cibitoke",
                           "Gitega", "Karuzi", "Kayanza", "Kirundo", "Makamba", "Muramvya", "Muyinga",
                           "Mwaro", "Ngozi", "Rutana", "Ruyigi", "Waterbody"],
                "Democratic Republic of the Congo": ["Katanga", "Sud-Kivu", "Maniema", "Kasai-Oriental", "Kasai-Occidental"],
                "Rwanda": ["Butare", "Byumba", "Cyangugu", "Gikongoro", "Gisenyi", "Gitarama", "Kibungo",
                          "Kibuye", "Kigali-ngali", "Prefecture De La Ville De Kigali", "Ruhengeri",
                          "Umutara"],
                "United Republic of Tanzania": ["Kigoma", "Rukwa", "Kagera", "Tabora"],
                "Zambia": ["Luapula", "Northern", "North-Western"]
            },
            "Coastal Western Africa": {
                "Ghana": ["Northern"],
                "Togo": ["Centrale", "Kara", "Plateaux", "Savanes"],
                "Benin": ["Borgou", "Donga", "Collines", "Zou"],
                "Nigeria": ["Abia", "Akwa Ibom", "Anambra", "Bayelsa", "Benue", "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti"],
                "Cameroon": ["Sud-Ouest", "Sud", "Littoral", "Ouest", "Nord-Ouest", "Centre", "Est", "Extreme-Nord"],
                "Equatorial Guinea": ["Annobon", "Bioko Norte", "Bioko Sur", "Centro Sur", "Kientem", "Litoral", "Welenzas"],
                "Gabon": ["ESTUAIRE", "WOLEU-NTEM", "MOYEN-OGOOUE", "OGOOUE-IVINDO"],
                "Congo": ["Cuvette Ouest", "Sangha"]
            },
            "Lake Chad Basin": {
                "Nigeria": ["Borno", "Adamawa", "Taraba", "Gombe", "Plateau"],
                "Cameroon": ["Adamaoua", "Nord", "Extreme-Nord"],
                "Chad": ["Logone Occidental", "Tandjile Est", "Tandjile Ouest", "Kanem", "Barh El Gazal", "Lac", "Hadjer Lamis", "Mayo-Dala"],
                "Central African Republic": ["Ouham", "Bamingui-bangora"],
                "Niger": ["Tillaberi", "Zinder"]
            },
            "Nile": {
                "Sudan": ["Khartoum", "Kassala", "Gadaref", "Al Jazeera"],
                "Ethiopia": ["Amhara"]
            },
            "Somali": {
                "Kenya": ["North Eastern Province"],
                "Ethiopia": ["Oromia", "Somali"],
                "Somalia": ["Bay", "Bakool", "Gedo"],
                "Djibouti": ["Ali Sabieh", "Dikhil"],
                "Uganda": ["Kitgum", "Kotido", "Moroto"]
            }
        }
        
        # Display each episystem with custom styling
        for episystem, countries in episystems_data.items():
            with st.expander(episystem, expanded=False):
                for country, regions in countries.items():
                    st.markdown(f"**{country}**")
                    st.markdown(", ".join(regions))
                    st.markdown("")
    
    # Filter subregions_df to only include episystem regions
    episystem_regions = []
    for countries in episystems_data.values():
        for country, regions in countries.items():
            for region in regions:
                episystem_regions.append((country, region))
    
    filtered_df = subregions_df[
        subregions_df.apply(lambda x: (x['Country'], x['Subregion']) in episystem_regions, axis=1)
    ]
    
    # Calculate and display results
    if st.button("Calculate Episystem Costs"):
        display_scenario_results(filtered_df, episystems_data)

def display_scenario_results(selected_regions_data, episystems_data):
    """Display the results of scenario calculations"""
    st.markdown("---")
    st.markdown("**Episystem Analysis Results:**")
    
    # Build results table by processing each unique country-subregion combination
    results_table = []
    
    # Get unique country-subregion pairs
    country_subregions = selected_regions_data[['Country', 'Subregion']].drop_duplicates()
    
    # Process each country-subregion pair
    for _, row in country_subregions.iterrows():
        country = row['Country']
        subregion = row['Subregion']
        
        # Determine if we're using 'Specie' or 'Species' column
        species_col = 'Specie' if 'Specie' in selected_regions_data.columns else 'Species'
        if species_col not in selected_regions_data.columns:
            st.error("Neither 'Specie' nor 'Species' column found in data")
            return
        
        # Get data for both species for this country-subregion
        goats_mask = (
            (selected_regions_data['Country'] == country) & 
            (selected_regions_data['Subregion'] == subregion) & 
            (selected_regions_data[species_col] == 'Goats')
        )
        sheep_mask = (
            (selected_regions_data['Country'] == country) & 
            (selected_regions_data['Subregion'] == subregion) & 
            (selected_regions_data[species_col] == 'Sheep')
        )

        goats_data = selected_regions_data[goats_mask].iloc[0] if len(selected_regions_data[goats_mask]) > 0 else None
        sheep_data = selected_regions_data[sheep_mask].iloc[0] if len(selected_regions_data[sheep_mask]) > 0 else None
        
        result_row = {"Country": country, "Subregion": subregion}
        
        # Calculate for both years
        for year in [1, 2]:
            def calculate_costs(data, year):
                if data is None:
                    return {}
                
                try:
                    # Get scenario parameters from session state
                    params = st.session_state.scenario_params
                    
                    # Initial vaccination calculations with user-defined parameters
                    population = float(data['100%_Coverage'])  # Base population from 100% coverage
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
            goat_results = calculate_costs(goats_data, year) if goats_data is not None else {}
            sheep_results = calculate_costs(sheep_data, year) if sheep_data is not None else {}

            # Extract values with fallbacks to 0
            row[f"Goats Y{year}"] = goat_results.get('animals_vaccinated', 0) if goat_results else 0
            row[f"Sheep Y{year}"] = sheep_results.get('animals_vaccinated', 0) if sheep_results else 0
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
    
    # Display campaign summary in styled containers
    st.markdown("### Campaign Overview")

    params = st.session_state.scenario_params
    total_campaign_cost = total_cost_y1 + total_cost_y2

    # Get regional costs from session state (same as continental_overview.py)
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
                    <div style='font-size:1.2em; font-weight:600; margin-bottom:10px;'>Other Parameters:</div>
                    <div style='font-size:1em; color:#444;'>
                        <div style='margin-bottom:8px;'><b>Coverage Target:</b> {:,.0f}%</div>
                        <div style='margin-bottom:8px;'><b>Wastage Rate:</b> {:,.0f}%</div>
                        <div style='margin-bottom:8px;'><b>Political Stability Index:</b> {:.1f}</div>
                        <div style='margin-bottom:8px;'><b>Delivery Channel:</b> {}</div>
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
        params['coverage_rate']*100,
        params['wastage_rate']*100,
        params['psi'],
        params['delivery_channel']
    ), unsafe_allow_html=True)
    
    # Create episystem level aggregation
    st.markdown("---")
    st.markdown("### Results by Episystem")
    
    # Convert results to DataFrame for aggregation
    results_df_copy = results_df.copy()
    
    # Find episystem for each country-subregion pair
    def get_episystem(row):
        for episystem, countries in episystems_data.items():
            country = row['Country']
            if country in countries:
                if row['Subregion'] in countries[country]:
                    return episystem
        return "Unknown"
    
    results_df_copy['Episystem'] = results_df_copy.apply(get_episystem, axis=1)
    
    # Aggregate by episystem
    episystem_agg = results_df_copy.groupby('Episystem').agg({
        'Total Y1': 'sum',
        'Cost Y1': 'sum',
        'Doses Y1': 'sum',
        'Wasted Y1': 'sum',
        'Total Y2': 'sum',
        'Cost Y2': 'sum',
        'Doses Y2': 'sum',
        'Wasted Y2': 'sum'
    }).reset_index()

    # Add Total Campaign Cost column (Cost Y1 + Cost Y2)
    episystem_agg['Total Campaign Cost'] = episystem_agg['Cost Y1'] + episystem_agg['Cost Y2']
    # Reorder columns to put Episystem first, then Total Campaign Cost
    episystem_agg = episystem_agg[['Episystem', 'Total Campaign Cost', 'Total Y1', 'Cost Y1', 'Doses Y1', 'Wasted Y1', 'Total Y2', 'Cost Y2', 'Doses Y2', 'Wasted Y2']]

    # Format numeric columns for display (no decimals)
    def format_no_decimals(val):
        try:
            return f"{int(round(float(val))):,}"
        except Exception:
            return val

    episystem_display = episystem_agg.copy()
    for col in ['Total Y1', 'Doses Y1', 'Wasted Y1', 'Total Y2', 'Doses Y2', 'Wasted Y2']:
        episystem_display[col] = episystem_display[col].apply(format_no_decimals)
    for col in ['Cost Y1', 'Cost Y2', 'Total Campaign Cost']:
        episystem_display[col] = episystem_display[col].apply(lambda x: f"${int(round(float(x))):,}" if pd.notnull(x) else "$0")

    # Add total row at the bottom
    total_row = {
        'Episystem': 'Total',
        'Total Campaign Cost': f"${int(round(episystem_agg['Total Campaign Cost'].sum())):,}",
        'Total Y1': format_no_decimals(episystem_agg['Total Y1'].sum()),
        'Cost Y1': f"${int(round(episystem_agg['Cost Y1'].sum())):,}",
        'Doses Y1': format_no_decimals(episystem_agg['Doses Y1'].sum()),
        'Wasted Y1': format_no_decimals(episystem_agg['Wasted Y1'].sum()),
        'Total Y2': format_no_decimals(episystem_agg['Total Y2'].sum()),
        'Cost Y2': f"${int(round(episystem_agg['Cost Y2'].sum())):,}",
        'Doses Y2': format_no_decimals(episystem_agg['Doses Y2'].sum()),
        'Wasted Y2': format_no_decimals(episystem_agg['Wasted Y2'].sum())
    }
    episystem_display = pd.concat([episystem_display, pd.DataFrame([total_row])], ignore_index=True)

    st.dataframe(episystem_display, width="stretch")

    # Bar chart of total cost per episystem (exclude total row)
    import plotly.express as px
    chart_df = episystem_display[episystem_display['Episystem'] != 'Total'].copy()
    chart_df['Total Campaign Cost (USD)'] = chart_df['Total Campaign Cost'].replace({'\$': '', ',': ''}, regex=True).astype(float)
    fig = px.bar(
        chart_df,
        x='Episystem',
        y='Total Campaign Cost (USD)',
        title='Total Campaign Cost per Episystem',
        labels={'Total Campaign Cost (USD)': 'Total Campaign Cost (USD)', 'Episystem': 'Episystem'},
        text_auto='.2s'
    )
    fig.update_layout(xaxis_title='Episystem', yaxis_title='Total Campaign Cost (USD)', showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Display detailed results
    st.markdown("---")
    st.markdown("### Detailed Results by Region")

    # Add Episystem column to results_df
    results_df['Episystem'] = results_df.apply(lambda row: get_episystem(row), axis=1)

    display_cols = [
        "Episystem", "Total Campaign Cost", "Country", "Subregion", "Goats Y1", "Sheep Y1", "Total Y1", "Cost Y1",
        "Doses Y1", "Wasted Y1", "Goats Y2", "Sheep Y2", "Total Y2", "Cost Y2",
        "Doses Y2", "Wasted Y2"
    ]
    numeric_cols = [
        "Goats Y1", "Sheep Y1", "Total Y1", "Doses Y1", "Wasted Y1",
        "Goats Y2", "Sheep Y2", "Total Y2", "Doses Y2", "Wasted Y2"
    ]

    # Add Total Campaign Cost column to detailed results
    results_df['Total Campaign Cost'] = results_df['Cost Y1'] + results_df['Cost Y2']

    results_display_df = format_table_values(results_df[display_cols], numeric_cols)
    results_display_df['Cost Y1'] = results_display_df['Cost Y1'].apply(lambda x: f"${float(x):,.2f}" if pd.notnull(x) else "$0.00")
    results_display_df['Cost Y2'] = results_display_df['Cost Y2'].apply(lambda x: f"${float(x):,.2f}" if pd.notnull(x) else "$0.00")
    results_display_df['Total Campaign Cost'] = results_display_df['Total Campaign Cost'].apply(lambda x: f"${float(x):,.2f}" if pd.notnull(x) else "$0.00")

    st.dataframe(results_display_df, width="stretch")
