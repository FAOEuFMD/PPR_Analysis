"""
Regions & Countries tab for PPR Vaccination Cost Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from cost_data import country_region_map

def filter_ppr_free_countries(country_stats):
    """Filter out PPR-free countries and return filtered stats"""
    # List of countries/zones to exclude as per WOAH June 2025
    ppr_free_countries = {
        "Botswana", "eSwatini", "Eswatini", "Lesotho", "Madagascar", 
        "Mauritius", "Namibia", "South Africa", "Kingdom of eSwatini",
        # Never reported
        "Cabo Verde", "Cape Verde", "Sao Tome and Principe", "Malawi", "Mozambique", "Zambia", "Zimbabwe"
    }
    
    # Track excluded countries
    excluded = []
    filtered_stats = {}
    
    # Filter out PPR-free countries
    for country, stats in country_stats.items():
        country_norm = country.lower().replace(" ", "")
        skip = False
        for ppr_free in ppr_free_countries:
            if country_norm == ppr_free.lower().replace(" ", ""):
                excluded.append(country)
                skip = True
                break
        if not skip:
            filtered_stats[country] = stats
            
    return filtered_stats, excluded

def create_region_cost_pie(region_table):
    """Create pie chart showing total campaign costs per region"""
    pie_labels = region_table["Region"]
    pie_values = region_table["Total Campaign Cost"].apply(
        lambda x: float(str(x).replace('$','').replace(',',''))
    )
    
    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=pie_labels, 
        values=pie_values,
        hole=0.3,
        marker=dict(colors=px.colors.qualitative.Plotly[:len(pie_labels)]),
    ))
    fig.update_layout(
        title_text="Total Campaign Cost per Region",
        showlegend=True,
    )
    fig.update_traces(textinfo="label+percent", pull=[0.02]*len(pie_labels))
    return fig

def create_country_cost_bars(country_table_df):
    """Create horizontal bar chart comparing country costs for Y1 and Y2"""
    country_table_df_sorted = country_table_df.copy()
    country_table_df_sorted["Total Campaign Cost Float"] = country_table_df_sorted["Total Campaign Cost"].apply(
        lambda x: float(str(x).replace('$','').replace(',',''))
    )
    country_table_df_sorted = country_table_df_sorted.sort_values("Total Campaign Cost Float", ascending=True)
    country_names = country_table_df_sorted["Country"]
    cost_y1 = country_table_df_sorted["Cost Y1"].apply(
        lambda x: float(str(x).replace('$','').replace(',',''))
    )
    cost_y2 = country_table_df_sorted["Cost Y2"].apply(
        lambda x: float(str(x).replace('$','').replace(',',''))
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=country_names,
        x=cost_y1,
        name="Y1",
        marker_color="#636EFA",
        orientation="h",
        width=0.8
    ))
    fig.add_trace(go.Bar(
        y=country_names,
        x=cost_y2,
        name="Y2",
        marker_color="#EF553B",
        orientation="h",
        width=0.8
    ))
    fig.update_layout(
        barmode="group",
        title="Vaccination Cost by Country (Y1 vs Y2)",
        xaxis_title="Cost (USD)",
        yaxis_title="Country",
        legend_title="Year",
        height=700,
        bargap=0.1,
        bargroupgap=0.05
    )
    return fig

def render_tab(country_stats):
    """Render the Regions & Countries tab"""
    st.subheader("Breakdown by Region")
    
    # Filter out PPR-free countries
    filtered_stats, excluded_countries = filter_ppr_free_countries(country_stats)
    
    # Display filtering summary in expander
    with st.expander("View Country Filtering Summary"):
        st.markdown("""
        <style>
        .filter-summary { padding: 10px; }
        .filter-summary ul { list-style-type: none; padding-left: 0; }
        .filter-summary li { margin: 5px 0; }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Countries Excluded")
            for country in sorted(excluded_countries):
                st.markdown(f"- {country}")
        with col2:
            st.markdown("#### Statistics")
            st.markdown(f"""
            - **Total Countries:** {len(country_stats)}
            - **Excluded:** {len(excluded_countries)}
            - **Included:** {len(filtered_stats)}
            """)
    
    # Build region breakdown table
    region_stats = {}
    for country, stats in filtered_stats.items():
        region = country_region_map.get(country, "West Africa")
        if region not in region_stats:
            region_stats[region] = {
                "Total Campaign Cost": 0,
                "Goats Y1": 0, "Sheep Y1": 0, "Total Y1": 0, "Cost Y1": 0, 
                "Doses Y1": 0, "Wasted Y1": 0, "Goats Y2": 0, "Sheep Y2": 0, 
                "Total Y2": 0, "Cost Y2": 0, "Doses Y2": 0, "Wasted Y2": 0
            }
        
        # Calculate total campaign cost
        region_stats[region]["Total Campaign Cost"] += stats["Y1"]["cost"] + stats["Y2"]["cost"]
        
        # Aggregate Y1 stats
        region_stats[region]["Goats Y1"] += stats["Y1"]["Goat"]
        region_stats[region]["Sheep Y1"] += stats["Y1"]["Sheep"]
        region_stats[region]["Total Y1"] += stats["Y1"]["Goat"] + stats["Y1"]["Sheep"]
        region_stats[region]["Cost Y1"] += stats["Y1"]["cost"]
        region_stats[region]["Doses Y1"] += stats["Y1"]["doses"]
        region_stats[region]["Wasted Y1"] += stats["Y1"]["wasted"]
        
        # Aggregate Y2 stats
        region_stats[region]["Goats Y2"] += stats["Y2"]["Goat"]
        region_stats[region]["Sheep Y2"] += stats["Y2"]["Sheep"]
        region_stats[region]["Total Y2"] += stats["Y2"]["Goat"] + stats["Y2"]["Sheep"]
        region_stats[region]["Cost Y2"] += stats["Y2"]["cost"]
        region_stats[region]["Doses Y2"] += stats["Y2"]["doses"]
        region_stats[region]["Wasted Y2"] += stats["Y2"]["wasted"]

    # Convert to DataFrame and format
    region_table = pd.DataFrame.from_dict(region_stats, orient="index")
    region_table = region_table.reset_index().rename(columns={"index": "Region"})
    
    # Format numeric columns
    numeric_cols = [col for col in region_table.columns if col != "Region"]
    for col in numeric_cols:
        if "Cost" in col:
            region_table[col] = region_table[col].map(lambda x: f"${x:,.2f}")
        else:
            region_table[col] = region_table[col].map(lambda x: f"{int(x):,}")
    
    # Display region table
    st.dataframe(region_table, height=region_table.shape[0]*35+40, width='stretch')

    # Create and display regional cost pie chart
    fig = create_region_cost_pie(region_table)
    st.plotly_chart(fig, width='stretch')

    # Country breakdown section
    st.subheader("Breakdown by Country")
    
    # Build country breakdown table
    country_table = []
    for country, stats in filtered_stats.items():
        row = {
            "Country": country,
            "Total Campaign Cost": f"${stats['Y1']['cost'] + stats['Y2']['cost']:,.2f}",
            "Political_Stability_Index": "0.000",  # This should be populated from national_df
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
        }
        country_table.append(row)
    
    country_table_df = pd.DataFrame(country_table)
    st.dataframe(country_table_df, height=country_table_df.shape[0]*35+40, width='stretch')

    # Create and display country cost bar chart
    bar_fig = create_country_cost_bars(country_table_df)
    st.plotly_chart(bar_fig, width='stretch')
