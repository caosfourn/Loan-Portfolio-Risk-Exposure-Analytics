# Changelog

## 1.0.0 — Risk Analytics alignment

- Added one canonical Python KPI implementation in `src/risk_metrics.py`.
- Rebuilt notebooks around matured outcome risk, exposure, sample size, and uncertainty.
- Archived the legacy reporting-era notebook under `notebooks/legacy/`.
- Replaced month-only/Good-vs-Bad SQL with governed Risk Analytics queries and reconciliation checks.
- Expanded data-quality checks to include category normalization and cross-field date chronology.
- Added automated KPI and data-quality tests plus a one-command validator.
- Added environment metadata, code license, data dictionary, provenance register, and Power BI release checklist.
- Rewrote README around portfolio-risk decisions and corrected stale claims.
