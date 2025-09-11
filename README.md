# Continental PPR Eradication Cost Dashboard

A professional, production-ready Streamlit dashboard for calculating the cost of continental PPR eradication by vaccination across Africa. Supports scenario testing, editing defaults, aggregated totals (Africa/region/country/subregion), and downloadable reports/charts.

## Features
- Macro-style scenario calculator with editable parameters
- Aggregated results at continent, region, country, and subregion levels
- Scenario builder and comparison
- Downloadable CSV/PDF reports and charts
- Professional FAO/WOAH-style UI
- Data validation, audit logging, and traceability

## Layout
- **Sidebar:** Scenario controls (coverage, cost mode, wastage, delivery channel, political stability, newborn rates, thresholds)
- **Tabs:**
  - Overview (KPI cards, high-level charts)
  - Regions & Countries (tables, drill-down)
  - Subregions (aggregated results)
  - Scenario Builder (compare scenarios)
  - Methodology & Data Sources (summary, links, downloadable appendix)
  - Data (raw tables, export)
  - Export / Reports (CSV/PDF)

## Setup & Installation

1. Clone the repository:
   ```sh
   git clone <your-repo-url>
   cd ppr_dashboard
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Place your data files in the root directory:
   - `analysis_example.docx`
   - `methodology.docx`
   - `costs_influencers.docx`
   - `National.xlsx`
   - `Subregions.xlsx`

4. Run the app locally:
   ```sh
   streamlit run app/streamlit_app.py
   ```

### One-click Streamlit Cloud
- Upload your repo and data files to Streamlit Cloud
- Set the main file to `app/streamlit_app.py`
- Click "Deploy"

## Methodology & Data Sources
- **Population inputs:** FAOSTAT
- **Forecasting:** VADEMOS tool
- **Density allocation:** GLW4 (Gridded Livestock of the World)
- **Cost references:** Key Factors doc, case studies
- **Internal docs:**
  - `analysis_example.docx` (output example)
  - `methodology.docx` (formulas, logic)
  - `costs_influencers.docx` (cost ranges, references)

## Directory Structure
```
ppr_dashboard/
├─ app/
│  ├─ streamlit_app.py
│  ├─ pages/
│  ├─ components/
│  └─ styles/
├─ src/
│  ├─ data_load.py
│  ├─ calculations.py
│  ├─ visuals.py
│  └─ utils.py
├─ tests/
│  ├─ test_calculations.py
│  └─ test_data_validation.py
├─ data/
├─ docs/
│  └─ methodology_summary.md
├─ requirements.txt
├─ Dockerfile
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
