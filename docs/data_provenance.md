# Data Provenance and Usage Register

## Current source record

| Item | Current status |
|---|---|
| Project file | `data/financial_loan.csv` |
| SHA-256 | `29F86ECD2A11E9EAC5A97F28692D2437A6AA79B9F07FBFFBD94BEAC2F5FDF578` |
| File size | 7,805,690 bytes |
| Extract grain | One row per loan ID |
| Rows / columns | 38,576 / 24 |
| Issue-date range | 1 January–12 December 2021 after parsing `dd-mm-yyyy` |
| Upstream provider / URL | **Not documented — owner action required** |
| Extraction / snapshot date | **Not documented — owner action required** |
| Dataset license | **Not documented — do not assume the project MIT license covers the CSV** |
| Refresh cadence | Static case-study snapshot |

## Allowed analytical use in this repository

- Portfolio scale, funded exposure, supplied status mix, and descriptive segment comparisons.
- Matured default rate among records labelled `Fully Paid` or `Charged Off`.
- Origination trends based on `issue_date`, with December treated as an incomplete month.
- Review hypotheses that combine outcome risk, funded exposure, and sample size.

## Quarantined or restricted interpretations

- Do not treat `total_payment / loan_amount` as profit, ROI, realized return, or expected loss.
- Do not use `last_payment_date`, `last_credit_pull_date`, or `next_payment_date` for timing analysis until their source/anonymization semantics are verified.
- Do not infer causality, optimal underwriting thresholds, fair-lending conclusions, or automated approval rules.
- Do not redistribute the CSV externally until its provider and license are documented.

## Known chronology anomalies

The current extract contains:

- 15,453 rows where `last_payment_date < issue_date`;
- 20,182 rows where `last_credit_pull_date < issue_date`;
- 37,478 resolved loans with a non-null `next_payment_date`.

These values are retained for auditability. They are warnings about source semantics, not rows to delete automatically.

## Owner completion checklist

- [ ] Record the original dataset page or provider.
- [ ] Record dataset usage and redistribution rights.
- [ ] Record the loan-status observation/as-of date.
- [ ] Explain whether date fields were shifted, synthesized, or anonymized.
- [ ] Replace the SHA-256 entry whenever the source file changes.
