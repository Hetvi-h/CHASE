# CHASE: Crime Hotspot Analytics for Safer Environments

## Project Methodology & Data Provenance

This section exists because the project's data went through a real validation process worth being transparent about — it is a strength of the methodology, not a flaw to hide.

1. **Base incident data**: Kaggle "Indian Crimes Dataset" (40,160 rows, 29 Indian cities, 2020–2024, 14 crime-type categories, victim demographics, weapon, police deployed, case status).
2. **Validation finding**: cross-checking this dataset's per-city row counts against real NCRB "Crime in India 2023" official figures showed the Kaggle dataset's absolute volume is only 0.1%–1.9% of real crime volume per city. Testing across the FULL range of matched cities revealed a real, moderate correlation (r ≈ 0.73) between Kaggle row counts and real NCRB totals — so the dataset is a **small, realistic-but-imperfect illustrative sample**, not fabricated noise, and not raw government microdata either (India does not publish real incident-level crime data publicly at street-address granularity).
3. **Correction applied**: incident counts per city were rescaled so each city's SHARE of the fixed total matches its real NCRB share.
4. **Result**: every row carries an `Is_Synthetic_Row` flag — `False` for original Kaggle rows, `True` for rows added during rescaling. This makes the real-vs-added split auditable at the row level.
5. **Sub-city positioning**: since no public dataset gives street-level incident coordinates for India, every row's exact `Latitude`/`Longitude` within its city is synthetically assigned via a weighted hotspot-mixture model — this applies to ALL rows, real and added alike.

> *"Incident-level crime microdata is not publicly available in India. We used a Kaggle-sourced illustrative incident dataset, validated its per-city distribution against official NCRB 2023 statistics (initial correlation r≈0.73 across 27 matched cities), and rescaled city-level row counts to match real NCRB proportions while preserving realistic per-incident attribute patterns. Sub-city coordinates are synthetically assigned via a hotspot-mixture model, since no public source provides street-level incident locations. A row-level `Is_Synthetic_Row` flag distinguishes original from rescaling-added records throughout."*
