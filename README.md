
# PPR Vaccination Cost Analysis Dashboard

## Overview
This Streamlit dashboard estimates the cost of continental PPR (Peste des Petits Ruminants) eradication by vaccination across Africa. It allows users to test scenarios, edit default parameters, view breakdowns by region/country/subregion, and export results.

## Features
- **Scenario Testing:** Adjust coverage, newborn rates, wastage, delivery channel, and cost multipliers.
- **Editable Defaults:** All key parameters are adjustable in the sidebar.
- **Aggregated Totals:** View results for Africa, regions, countries, and subregions.
- **Breakdown Tables:** Detailed tables for regions, countries, and subregions.
- **Interactive Charts:** Pie and bar charts for cost breakdowns.
- **Markdown Documentation:** Methodology and data sources are included.
- **Export:** Downloadable reports and charts.

## How It Works
1. **Data Loading:**
   - National and subregion data are loaded from Excel files.
   - Only key columns are used: `Country`, `Subregion`, `Specie`, `100%_Coverage`.
2. **Sidebar Controls:**
   - Set scenario name, coverage %, newborn estimation, wastage %, delivery channel, and cost multipliers.
   - Adjust regional vaccination cost sliders (min 0, max 2 USD/animal).
   - Set Political Stability Index thresholds and multipliers.
3. **Calculations:**
   - For each region/country/subregion:
     - Calculate animals to vaccinate (Year 1) using coverage %.
     - Adjust for wastage to get doses required.
     - Estimate cost using selected cost per animal.
     - Apply political stability and delivery channel multipliers.
     - For Year 2, estimate newborns and repeat calculations.
4. **Breakdowns:**
   - **Overview Tab:** Continent-wide totals and KPIs.
   - **Regions & Countries Tab:** Region and country breakdowns, pie/bar charts.
   - **Subregions Tab:** Filter by country, see subregion/specie breakdown.
   - **Methodology & Data Sources Tab:** Markdown documentation.
   - **Export Tab:** Download results.

## Calculation Logic
- **Year 1:**
  - `vaccinated = population * coverage %`
  - `doses = vaccinated / (1 - wastage %)`
  - `base_cost = doses * cost_per_animal`
  - `final_cost = base_cost * political_mult * delivery_mult`
- **Year 2:**
  - `newborns = vaccinated * newborn %`
  - Repeat dose and cost calculations for newborns.
- **Political Stability Multiplier:**
  - User sets thresholds and multipliers in sidebar.
  - Lower/negative index = higher multiplier (higher cost).
- **Delivery Channel Multiplier:**
  - User selects channel and sets multipliers.

## Data Files
- `National.xlsx`: Country-level population and stability data.
- `Subregions.xlsx`: Subregion/specie-level population data.
- `methodology.md`, `regional_costs.md`, `country_case_costs.md`, `data_sources.md`: Documentation.

## Usage
1. Install requirements:
   ```bash
   pip install streamlit pandas numpy openpyxl plotly folium streamlit-folium
   ```
2. Run the app:
   ```bash
   streamlit run app/streamlit_app.py
   ```
3. Adjust parameters in the sidebar and explore results in each tab.

## Customization
- **Regional Costs:** Set min/avg/max and custom values per region.
- **Political Stability:** Adjust thresholds and multipliers.
- **Delivery Channel:** Set multipliers for public, mixed, private.

## Project Structure
```
PPR Analysis/
├── app/
│   └── streamlit_app.py
├── src/
│   ├── data_load.py
│   └── calculations.py
├── data/
│   ├── National.xlsx
│   └── Subregions.xlsx
├── docs/
│   ├── methodology.md
│   ├── regional_costs.md
│   ├── country_case_costs.md
│   └── data_sources.md
└── README.md
```

## Contributing
- Fork the repo and submit pull requests for improvements.
- Report issues or feature requests via GitHub.

## License
This project is provided by FAO EuFMD. See repository for license details.

## Contact
For questions or support, contact the project owner or open an issue on GitHub.
├─ README.md
└─ .github/workflows/ci.yml
```

## Testing
Run unit tests:
```sh
python -m unittest discover tests
```

## License
This project is for demonstration and research purposes. Please cite FAO/WOAH and referenced sources for any public use.
