# Bank Loan Data Dictionary

Source grain: one row per loan ID. Percent-like fields are stored as decimal ratios.

| Column | Type / unit | Risk Analytics role | Governance note |
|---|---|---|---|
| `id` | Integer ID | Primary loan key | Required, non-null, unique. |
| `member_id` | Integer ID | Borrower/member reference | Not used as a person-level longitudinal key without source confirmation. |
| `application_type` | Category | Population descriptor | Current extract contains only `INDIVIDUAL`; it cannot support type comparisons. |
| `issue_date` | Date, `dd-mm-yyyy` | Origination trend and complete-month logic | Required; December 2021 is incomplete. |
| `loan_status` | Category | Outcome/status taxonomy | Allowed: `Fully Paid`, `Charged Off`, `Current`. |
| `loan_amount` | USD | Funded exposure | Positive; not outstanding balance or realized loss. |
| `total_payment` | USD | Recorded payment diagnostic | Timing/as-of date unknown; not revenue or profit. |
| `installment` | USD | Scheduled-payment descriptor | Positive; payment frequency/source semantics should be confirmed. |
| `int_rate` | Decimal ratio | Pricing diagnostic | Display as percentage; not evidence that pricing compensates for risk. |
| `dti` | Decimal ratio | Borrower-capacity segmentation | Descriptive only; not a policy threshold. |
| `annual_income` | USD/year | Borrower-capacity context | High outliers retained; median is preferred for segment comparisons. |
| `grade` | A–G | Credit-risk segmentation | Association, not an internally validated scorecard. |
| `sub_grade` | Category | Finer credit segmentation | Always show resolved-loan sample size. |
| `purpose` | Category | Product/use-case segmentation | Normalize labels for presentation; do not infer causality. |
| `term` | Text duration | Product structure | Source has leading spaces; canonical Python/SQL trims them. |
| `address_state` | US state code | Geographic concentration | Monitoring dimension only; not causal evidence. |
| `home_ownership` | Category | Borrower-profile segmentation | `NONE`/`OTHER` require source interpretation. |
| `emp_length` | Category | Borrower-profile segmentation | Descriptive; missing/unknown handling must remain visible. |
| `emp_title` | Text | Optional descriptive field | 1,438 missing; fill only for display and retain a missingness flag. |
| `verification_status` | Category | Verification segmentation | Does not prove verification quality or causality. |
| `total_acc` | Count | Credit-file descriptor | Definition and observation date are not documented. |
| `last_payment_date` | Date | Quarantined timing field | Chronology fails for 15,453 rows. |
| `next_payment_date` | Date | Quarantined schedule field | Non-null for all resolved loans in this extract. |
| `last_credit_pull_date` | Date | Quarantined credit-file timing field | Chronology fails for 20,182 rows. |

Derived fields such as `is_resolved`, `is_charged_off`, `issue_month`, `dti_band`, confidence intervals, and review priority are defined in `src/risk_metrics.py` and `docs/metric_contract.md`.
