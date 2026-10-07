# SoilSight — Soil Nutrient Deficiency Mapper

Satellite-based soil fertility screening and Soil Health Card (SHC) nutrient-status dashboard for **Sakri Tehsil, Dhule district, Maharashtra, India**.

> **Scope and honesty statement.** This is a decision-support / screening project, not a replacement for laboratory soil testing.
> - Vegetation indices do **not** measure soil N, P or K.
> - The Phase 1 fertility classes are **proxy labels** derived from remote-sensing/environmental thresholds, not laboratory fertility.
> - Model **confidence is not accuracy**, and a high random-split score is not proof of skill.
> - SoilGrids is a modelled reference product, **not** laboratory ground truth. CEC is **not** potassium.
> - The fertilizer table is an **illustrative heuristic**, not validated against laboratory data or current MPKV/Maharashtra recommendations.

## What the project contains

**Phase 1 — satellite fertility mapping (Sakri)**
- Sentinel-2 L2A (B02, B03, B04, B05, B08) and Copernicus 30 m DEM
- Indices: NDVI, NDRE, EVI, SAVI, GNDVI
- Random Forest (primary), Gradient Boosting, Logistic Regression, K-Means baselines
- Feature ablation; the final model uses EVI + SAVI + Elevation (an earlier model was found to leak labels through NDVI/soil-moisture thresholds)
- Hyperparameter search (negligible gain over defaults — reported as such)
- Random-split vs **spatial-block** validation, with sensitivity over 3×3 to 6×6 block grids
- Confidence-calibration analysis (ECE), permutation importance
- Two-date (monsoon vs post-harvest) comparison showing sensitivity to crop growth stage

**Phase 2 — laboratory N/P/K (SHC data)**
- 171 laboratory readings at 50 locations across 41 villages of Sakri Tehsil, rated with the ICAR-IISS SHC limits (source stored in `dashboard/public/shc_status.json`)
- Satellite features did **not** predict N, P or K (negative R² under grouped validation); within-location variance dominates. This is reported as a negative result.
- Satellite-fertility classes were compared with measured nutrient status, and simple IDW interpolation was tested

## Dashboard (React + react-leaflet)

Tabs: Overview, Models, Validation, Temporal, Lab Data (SHC), Fertilizer, plus a Farmer View (pick a lab-tested location or click the map; shows N/P/K status for that location only).
All numbers are read from JSON files in `dashboard/public/`; none are typed into the UI code. Charts are plain SVG.

```bash
cd dashboard
npm install
npm run dev        # http://localhost:5173
```

## Repository layout

| Area | Scripts |
|---|---|
| Data acquisition | `fetch_sakri_imagery.py`, `fetch_sakri_date2.py`, `fetch_elevation.py`, `fetch_sakri_npk_region_*.py`, `fetch_soilgrids*.py`, `sentinel_config.py` |
| Indices | `compute_all_indices.py`, `compute_indices_date2.py`, `compute_indices_npk_region*.py`, `generate_index_overlays.py` |
| Fertility model | `train_model.py`, `train_and_save_clean_model.py`, `ablation_study.py`, `hyperparameter_tuning.py`, `baseline_logreg.py`, `kmeans_baseline.py`, `gradient_boosting_comparison.py` |
| Validation | `spatial_validation.py`, `spatial_sensitivity_and_calibration.py`, `confidence_layer.py`, `explainability.py`, `sanity_check.py` |
| Prediction and maps | `predict_real_raster.py`, `generate_maps.py`, `fertilizer_map*.py`, `export_geotiff.py` |
| Temporal | `compare_temporal_indices.py` |
| SHC / N-P-K | `extract_features_at_npk_points*.py`, `train_npk_regression*.py`, `npk_variance_diagnostic.py`, `shc_nutrient_status.py`, `shc_validation_and_interpolation.py`, `export_npk_points.py` |
| WoSIS / data investigation | `inspect_wosis*.py`, `clean_wosis_nitrogen.py` |
| Dashboard data export | `generate_dashboard_data.py`, `generate_model_evaluation.py`, `update_dashboard_soilgrids.py`, `audit_dashboard_data.py` |
| Dashboard | `dashboard/` |

## Credentials

Sentinel Hub credentials are **not** stored in the repo. Create a `.env` file in the project root:

```
SH_CLIENT_ID=your-client-id
SH_CLIENT_SECRET=your-client-secret
```

`.env` is git-ignored. Never commit credentials.

## Data not included in the repository

Large or non-redistributable data is git-ignored: raw Sentinel-2/DEM rasters, `.npy` arrays, trained `.pkl` models, WoSIS extracts and most `.csv` files. Run the fetch/compute scripts above to regenerate them. Python dependencies used: numpy, pandas, scikit-learn, scipy, matplotlib, rasterio, pyproj, sentinelhub, joblib, python-dotenv, requests.

## Limitations

- Single study area (Sakri Tehsil); results are a regional case study and are not claimed to generalise.
- Phase 1 labels are proxy labels; accuracy figures describe agreement with those proxies.
- Calibration (ECE) was measured on in-distribution test data against proxy labels only.
- Only 50 laboratory locations are available; regression on N/P/K is not reliable at this sample size.
- Satellite-derived fertility classes are sensitive to acquisition date and to domain-shift correction.

## Licence

MIT — see `LICENSE`.
