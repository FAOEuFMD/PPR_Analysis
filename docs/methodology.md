# Methodology for PPR Vaccination Cost Estimation

## Data Sources
- **FAOSTAT (2024):** National livestock population figures.
- **VADEMOS:** Forecasting tool for sheep and goat populations (2025 projections).
- **GLW4 (2020):** Gridded Livestock of the World, 10 km resolution, used to allocate populations to subregions (ADM1).
- **Regional and country studies (peer-reviewed + FAO/World Bank reports).**

## Population Forecasting
- Use 2025 projections for goats and sheep.
- Subnational distribution allocated using GLW4 density shares.

## Vaccination Schedule Logic
- **Year 1:** User-selected coverage (default 80%).
- **Year 2:** Vaccinate newborns only (defaults: goats = 60% of Y1 vaccinated, sheep = 40%).
- Users can override newborn percentages.

## Cost Parameters
- Vaccine price range: **$0.06 – $0.30 per dose**.
- Total service costs (logistics, personnel, delivery): **$0.18 – $2.00 per animal**.
- Wastage: **10–33%**, default = **10%**.
- Delivery channels:
  - Public campaigns: higher fixed/overhead costs.
  - Private channels: variable but often cheaper.
  - Mixed systems: balance of both.
- Economies of scale reduce per-animal costs (e.g., Somalia).

## Political Stability Multiplier
- PSI < 0.4 → ×1.0  
- 0.4 ≤ PSI < 0.7 → ×1.5  
- PSI ≥ 0.7 → ×2.0  

## Formula
```
Vaccinated_initial = Population × Coverage
Doses_required = Vaccinated_initial × (1 + Wastage)
Cost = Doses_required × Cost_per_animal × Delivery_multiplier × Political_multiplier
```
