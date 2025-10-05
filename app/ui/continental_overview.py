"""
Continental Overview tab for PPR Vaccination Cost Dashboard
"""

import streamlit as st

def render_tab(country_stats, national_df):
    """Render the Continental Overview tab"""
    st.markdown("<b>Continental Overview</b>", unsafe_allow_html=True)
    
    # Create two columns for map and country list
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Display WOAH PPR Freedom Map
        st.image("./public/PPR woah.png", caption="WOAH: Official PPR Freedom Map (June 2025)", width="stretch")
    
    with col2:
        st.markdown("""
        <div style='font-size:1.1em; color:#444;'>
        <b>Note:</b> As per the WOAH update of the PPR freedom map (June 2025), the following countries/zones are officially recognized as free from Peste des Petits Ruminants (PPR) and are excluded from this analysis.<br>
        <span style='font-size:0.98em;'>See the <a href=\"https://rr-africa.woah.org/en/official-disease-status-of-african-members/\" target=\"_blank\">WOAH official disease status of African Members</a> for details.</span>
        <ul style="margin-top:10px;">
            <li>Botswana (country-wide)</li>
            <li>eSwatini (country-wide)</li>
            <li>Lesotho (country-wide)</li>
            <li>Madagascar (country-wide)</li>
            <li>Mauritius (country-wide)</li>
            <li>Namibia (zone: south to the Veterinary Cordon Fence)</li>
            <li>South Africa (country-wide)</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # List of countries/zones to exclude as per WOAH June 2025
    ppr_free_countries = {
        "Botswana", "eSwatini", "Eswatini", "Lesotho", "Madagascar", 
        "Mauritius", "Namibia", "South Africa", "Kingdom of eSwatini"
    }
    
    # Track countries for filtering summary
    excluded_countries = []
    included_countries = []
    
    # Filter out PPR-free countries
    filtered_country_stats = {}
    for country, stats in country_stats.items():
        # Normalize country names for comparison
        country_norm = country.lower().replace(" ", "")
        # Create variations of PPR-free country names
        skip = False
        for ppr_free in ppr_free_countries:
            ppr_free_norm = ppr_free.lower().replace(" ", "")
            if country_norm == ppr_free_norm:
                skip = True
                excluded_countries.append(country)
                break
        if not skip:
            included_countries.append(country)
            filtered_country_stats[country] = stats
    
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
            st.markdown("#### Excluded Countries")
            for country in sorted(excluded_countries):
                st.markdown(f"- {country}")
        with col2:
            st.markdown("#### Statistics")
            st.markdown(f"""
            - **Total Countries:** {len(country_stats)}
            - **Excluded:** {len(excluded_countries)}
            - **Included:** {len(filtered_country_stats)}
            """)
    
    # Calculate totals for Y1
    total_goats_y1 = sum(stats['Y1']['Goat'] for stats in filtered_country_stats.values())
    total_sheep_y1 = sum(stats['Y1']['Sheep'] for stats in filtered_country_stats.values())
    total_animals_y1 = total_goats_y1 + total_sheep_y1
    total_doses_y1 = sum(stats['Y1']['doses'] for stats in filtered_country_stats.values())
    total_cost_y1 = sum(stats['Y1']['cost'] for stats in filtered_country_stats.values())
    total_wasted_y1 = sum(stats['Y1']['wasted'] for stats in filtered_country_stats.values())
    
    # Calculate totals for Y2
    total_goats_y2 = sum(stats['Y2']['Goat'] for stats in filtered_country_stats.values())
    total_sheep_y2 = sum(stats['Y2']['Sheep'] for stats in filtered_country_stats.values())
    total_animals_y2 = total_goats_y2 + total_sheep_y2
    total_doses_y2 = sum(stats['Y2']['doses'] for stats in filtered_country_stats.values())
    total_cost_y2 = sum(stats['Y2']['cost'] for stats in filtered_country_stats.values())
    total_wasted_y2 = sum(stats['Y2']['wasted'] for stats in filtered_country_stats.values())
    
    # Calculate weighted cost and total campaign cost
    weighted_cost = total_cost_y1 / total_animals_y1 if total_animals_y1 > 0 else 0
    total_campaign_cost = total_cost_y1 + total_cost_y2
    
    # Display Total Campaign Cost
    # Get regional costs from sliders
    costs = {
        'North Africa': f"${st.session_state.get('cost_slider_North Africa', '')}",
        'West Africa': f"${st.session_state.get('cost_slider_West Africa', '')}",
        'Central Africa': f"${st.session_state.get('cost_slider_Central Africa', '')}",
        'East Africa': f"${st.session_state.get('cost_slider_East Africa', '')}",
        'Southern Africa': f"${st.session_state.get('cost_slider_Southern Africa', '')}"
    }
    
    # Get main parameters from config
    config = st.session_state.get('config', {})
    coverage = f"{config.get('coverage', '')}%"
    wastage = f"{config.get('wastage', '')}%"
    # Format newborn and coverage info
    newborn = (f"Goats: {config.get('newborn_goats', '')}%, " 
              f"Sheep: {config.get('newborn_sheep', '')}%")
    second_year = f"{config.get('second_year_coverage', '')}%"
    
    # Format delivery channel and multipliers
    delivery = config.get('delivery_channel', '')
    multipliers = config.get('delivery_multipliers', {})
    delivery_text = (f"{delivery} "
                    f"(Public: {multipliers.get('Public', '')}, "
                    f"Mixed: {multipliers.get('Mixed', '')}, "
                    f"Private: {multipliers.get('Private', '')})")
    
    # Format risk multipliers
    stability = config.get('political_stability', {})
    risk_mult = (f"High: {stability.get('mult_high_risk', '')}, "
               f"Moderate: {stability.get('mult_moderate_risk', '')}, "
               f"Low: {stability.get('mult_low_risk', '')}")
    
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
                        <div style='margin-bottom:8px;'><b>Coverage Target:</b> {}</div>
                        <div style='margin-bottom:8px;'><b>Newborn Rates:</b> {}</div>
                        <div style='margin-bottom:8px;'><b>Second Year Coverage:</b> {}</div>
                        <div style='margin-bottom:8px;'><b>Wastage Rate:</b> {}</div>
                        <div style='margin-bottom:8px;'><b>Delivery Channel:</b> {}</div>
                        <div style='margin-bottom:8px;'><b>Political Stability Risk:</b> {}</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """.format(
        total_campaign_cost, total_cost_y1, total_cost_y2,
        costs['North Africa'], costs['West Africa'], costs['Central Africa'],
        costs['East Africa'], costs['Southern Africa'],
        coverage,
        newborn,
        second_year,
        wastage,
        delivery_text,
        risk_mult
    ), unsafe_allow_html=True)
    
    # Display Y1 metrics
    cols_y1 = st.columns(3)
    with cols_y1[0]:
        st.markdown(f'<div class="kpi-card">Total Animals Vaccinated (Y1)<br><b>{int(total_animals_y1):,}</b></div>', unsafe_allow_html=True)
    with cols_y1[1]:
        st.markdown(f'<div class="kpi-card">Goats Vaccinated (Y1)<br><b>{int(total_goats_y1):,}</b></div>', unsafe_allow_html=True)
    with cols_y1[2]:
        st.markdown(f'<div class="kpi-card">Sheep Vaccinated (Y1)<br><b>{int(total_sheep_y1):,}</b></div>', unsafe_allow_html=True)

    cols_y1b = st.columns(3)
    with cols_y1b[0]:
        st.markdown(f'<div class="kpi-card">Total Cost (Y1)<br><b>${total_cost_y1:,.2f}</b></div>', unsafe_allow_html=True)
    with cols_y1b[1]:
        st.markdown(f'<div class="kpi-card">Total Doses Required (Y1)<br><b>{int(total_doses_y1):,}</b></div>', unsafe_allow_html=True)
    with cols_y1b[2]:
        st.markdown(f'<div class="kpi-card">Vaccines Wasted (Y1)<br><b>{int(total_wasted_y1):,}</b></div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # Display Y2 metrics
    cols_y2 = st.columns(3)
    with cols_y2[0]:
        st.markdown(f'<div class="kpi-card">Total Animals Vaccinated (Y2)<br><b>{int(total_animals_y2):,}</b></div>', unsafe_allow_html=True)
    with cols_y2[1]:
        st.markdown(f'<div class="kpi-card">Goats Vaccinated (Y2)<br><b>{int(total_goats_y2):,}</b></div>', unsafe_allow_html=True)
    with cols_y2[2]:
        st.markdown(f'<div class="kpi-card">Sheep Vaccinated (Y2)<br><b>{int(total_sheep_y2):,}</b></div>', unsafe_allow_html=True)

    cols_y2b = st.columns(3)
    with cols_y2b[0]:
        st.markdown(f'<div class="kpi-card">Total Cost (Y2)<br><b>${total_cost_y2:,.2f}</b></div>', unsafe_allow_html=True)
    with cols_y2b[1]:
        st.markdown(f'<div class="kpi-card">Total Doses Required (Y2)<br><b>{int(total_doses_y2):,}</b></div>', unsafe_allow_html=True)
    with cols_y2b[2]:
        st.markdown(f'<div class="kpi-card">Vaccines Wasted (Y2)<br><b>{int(total_wasted_y2):,}</b></div>', unsafe_allow_html=True)
