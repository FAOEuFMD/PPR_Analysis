"""
Methodology & Data Sources tab for PPR Vaccination Cost Dashboard
"""

import streamlit as st
import pandas as pd

def render_tab(national_df):
    """Render the Methodology & Data Sources tab"""
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
    The dashboard estimates the cost of PPR vaccination across Africa using a scenario-based macro calculator. Calculations are performed for each region, country, and subregion, based on user-adjustable parameters for coverage, newborn rates, wastage, delivery channel, and cost multipliers.

    **Calculation Steps:**
    1. **Population Estimation:** As a base, we use the FAOSTAT Statistical Database^1^ for sheep and goat populations. To estimate current populations (beyond 2023), we apply machine learning predictive models to project population growth. These national population estimates are then distributed within countries using Gridded Livestock of the World (GLW) density data^2^, allowing us to estimate populations at subnational administrative levels.
    2. **Year 1 Vaccination:** We apply a strategy of one vaccine per animal in the first year, at the chosen coverage rate (default 80%, adjustable). The number of animals to vaccinate is calculated as: Population × Coverage.
    3. **Year 2 Vaccination:** In the second year, only newborns are vaccinated. We estimate newborns as 40% of the initial population for sheep and 60% for goats (defaults, both adjustable). The number of newborns is then multiplied by the coverage rate to get the number to vaccinate in year 2.
    4. **Year 3 Cost:** The cost for year 3 is estimated as 15% of the previous year's (year 2) vaccination cost, representing follow-up and maintenance activities.
    4. **Dosage Calculation:** For both years, the required number of vaccine doses is calculated by adding the wastage rate (adjustable) to the number of animals to vaccinate.
    5. **Cost Calculation:** The total cost is calculated by multiplying the number of doses by the regional cost per animal, which is based on literature and field estimates (also adjustable).
    6. **Delivery Channel Adjustment:** A delivery multiplier is applied to account for differences in cost between public, private, and mixed delivery programs. Mixed programs keep the base price, private programs are cheaper, and public programs are more expensive (all multipliers are adjustable).
    7. **Political Stability Adjustment:** Finally, a political stability multiplier is applied to differentiate between countries with stable conditions and those with war zones or other unstable situations, where vaccination campaigns are more challenging and costly.

    This stepwise approach ensures that all major factors influencing vaccination costs are considered and can be adjusted by the user for scenario analysis.
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
        {"Factor": "Logistics & Personnel", 
         "Impact on Cost": "Often the largest component (>50% of total cost); includes vaccine delivery, transportation, and staff wages."},
        {"Factor": "Channel (Public vs. Private)", 
         "Impact on Cost": "Public campaigns have higher operational costs due to overhead, while private delivery can be cheaper but more variable."},
        {"Factor": "Location & Production System", 
         "Impact on Cost": "Pastoral vs. agropastoral or mixed-crop systems differ in accessibility and farmer participation."},
        {"Factor": "Economies of Scale", 
         "Impact on Cost": "Large campaigns (e.g., Somalia) reduce per-animal costs significantly."},
        {"Factor": "Vaccine Wastage", 
         "Impact on Cost": "Missed shots or leftover doses can add 10–33% to costs."},
        {"Factor": "Farmer Opportunity Cost", 
         "Impact on Cost": "Especially relevant in mixed-crop systems where farmers lose work time to bring animals for vaccination."},
    ])
    st.dataframe(factors_table, height=factors_table.shape[0]*35+40)
    
    st.markdown("""
    Given the significant impact of delivery and logistics challenges on vaccination costs, particularly in 
    regions with varying political stability, we incorporate the Political Stability Index (PSI) as an 
    adjustment factor to account for these operational complexities and their associated cost implications.
    """)
    
    st.markdown("**Political Stability Multiplier Logic:**")
    st.markdown("""
    Political stability index (-2.5 weak; 2.5 strong), 2023: The average for 2023 based on 53 countries was -0.68 points. 
    The indicator is available from 1996 to 2023.

    - Index < Low Threshold: High risk, higher multiplier
    - Low ≤ Index < High: Moderate risk, moderate multiplier
    - Index ≥ High: Low risk, lower multiplier
    """)

    st.markdown("**Example Data Table (National):**")
    # Drop duplicate and None columns before display
    national_df_display = national_df.loc[:,~national_df.columns.duplicated()]
    national_df_display = national_df_display.loc[:,national_df_display.columns.notnull()]
    st.dataframe(national_df_display.head(10), height=350)
    
    st.markdown('<div class="methodology-section">Data Sources</div>', unsafe_allow_html=True)
    st.markdown("""
    ^1^ **Population data:** FAO. 2023. FAOSTAT Statistical Database. Food and Agriculture Organization of the United Nations.  
    Available at: https://www.fao.org/faostat/en/

    ^2^ **Livestock density data:** FAO. 2024. Gridded Livestock of the World (GLW) 4: Gridded Livestock Density (Global - 2020 - 10 km). Food and Agriculture Organization of the United Nations.  
    Available at: https://data.apps.fao.org/catalog/dataset/15f8c56c-5499-45d5-bd89-59ef6c026704

    **Vaccination cost data:** The document draws from peer-reviewed studies and field cost estimates on Peste des Petits Ruminants (PPR) vaccination programs in Africa. Key cited sources include:
    - **Ethiopia:** Lyons NA et al., Prev Vet Med. 2019 – Field-derived cost estimates of PPR vaccination in Ethiopia. [DOI: 10.1016/j.prevetmed.2018.12.007]
    - **Burkina Faso, Senegal, Nigeria:** Ilboudo GS et al., Animals (Basel). 2022 – PPR vaccination cost estimates in Burkina Faso. [DOI: 10.3390/ani12162152]
    - **Somalia:** Jue S et al., Pastoralism. 2018 – Sero-prevalence and vaccination cost analysis.

    **Political stability data:** TheGlobalEconomy.com. 2024. Political stability index for Africa. Available at: https://www.theglobaleconomy.com/rankings/wb_political_stability/Africa/

    **Additional sources:**
    - VADEMOS tool (forecasting)
    - Key Factors document, case studies (cost references)
    - Internal docs: methodology, costs influencers, analysis examples
    """)
    
    st.markdown('<div class="methodology-section">License</div>', unsafe_allow_html=True)
    st.markdown("""
    **Creative Commons License**

    This work is made available under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 IGO license 
    (CC BY-NC-SA 3.0 IGO; [https://creativecommons.org/licenses/by-nc-sa/3.0/igo](https://creativecommons.org/licenses/by-nc-sa/3.0/igo)). 

    In addition to this license, some database specific terms of use are listed: 
    [Terms of Use of Datasets](https://www.fao.org/contact-us/terms/db-terms-of-use/en).

    [![Creative Commons License](https://i.creativecommons.org/l/by-nc-sa/3.0/igo/88x31.png)](https://creativecommons.org/licenses/by-nc-sa/3.0/igo)
    """)
