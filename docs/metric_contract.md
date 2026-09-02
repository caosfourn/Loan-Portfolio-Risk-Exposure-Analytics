# Bank Loan Portfolio Analytics — KPI Contract

## 1. Purpose and governance

This document is the canonical definition of portfolio metrics for the project. The Python notebook, SQL queries, Power BI measures, README, and final report must use these definitions. If a visual requires a different definition, it must be labelled as a separate metric rather than silently reusing a name.

**Decision cadence:** monthly portfolio review.  
**Data source:** `data/financial_loan.csv` at loan ID grain.  
**Time convention:** parse `issue_date` as `dd-mm-yyyy`; all monthly comparisons use both year and month.  
**Baseline:** calculated from the supplied extract; recalculate after any data refresh.

**Canonical implementations:** Python uses `src/risk_metrics.py`; SQL uses `Query.sql`; Power BI uses `docs/dax_measures.md`. Notebook cells must import the Python implementation rather than redefine core KPI formulas.

## 2. Status taxonomy

| Status | Contract meaning | Treatment in metrics |
|---|---|---|
| `Fully Paid` | Loan is recorded as fully repaid in the supplied snapshot. | Resolved positive outcome. |
| `Charged Off` | Loan is recorded as charged off in the supplied snapshot. | Resolved adverse outcome. |
| `Current` | Loan is active/unresolved in the supplied snapshot. | Include in portfolio-scale metrics; exclude from matured-outcome rates. |

Do not use **Good Loan Rate** as the primary risk metric. It groups `Fully Paid` with unresolved `Current` loans and can obscure outcome risk. It may be retained as a descriptive status-mix metric only.

## 3. Recommended KPI framework

### Primary portfolio KPIs

| KPI | Definition / formula | Baseline from supplied extract | Why it matters | Decision use |
|---|---|---:|---|---|
| Total applications | `COUNT(DISTINCT id)` | 38,576 | Portfolio scale and denominator for status mix. | Context only; not a risk decision metric on its own. |
| Funded exposure | `SUM(loan_amount)` | $435,757,075 | Capital committed to the portfolio or segment. | Prioritize risk review where exposure is material. |
| Charge-off share | `COUNT(status = 'Charged Off') / COUNT(all loan IDs)` | 13.82% | Snapshot view of adverse status in the full portfolio. | Monitor overall portfolio status mix. |
| Matured default rate | `COUNT(Charged Off) / COUNT(Charged Off + Fully Paid)` | 14.23% | Outcome rate among loans with a resolved status. | Primary descriptive risk benchmark for segment comparison. |
| Current-loan share | `COUNT(Current) / COUNT(all loan IDs)` | 2.85% | Size of unresolved population excluded from matured default rate. | Qualify the reliability of outcome comparisons. |

### Financial and pricing diagnostics

| KPI | Definition / formula | Baseline from supplied extract | Interpretation rule |
|---|---|---:|---|
| Total amount collected | `SUM(total_payment)` | $473,070,933 | Cash received in the supplied record, not necessarily cash collected during the issue period. |
| Cash collection ratio | `SUM(total_payment) / SUM(loan_amount)` | 108.56% | May exceed 100% because payments can include interest. It **must not** be labelled profit, net revenue, or full economic recovery. |
| Average interest rate | `AVG(int_rate)` | 12.05% | Descriptive pricing diagnostic; assess with risk and exposure, not in isolation. |
| Average DTI | `AVG(dti)` | 13.33% | Portfolio borrower-capacity diagnostic; not an approval threshold or causal risk estimate. |

### Risk and concentration drivers

| KPI | Definition / formula | Use |
|---|---|---|
| Segment matured default rate | `Charged Off / (Charged Off + Fully Paid)` within a segment | Compare outcome risk by grade, state, purpose, term, DTI band, or employment length. Always show the resolved-loan denominator. |
| Segment funded-exposure share | `SUM(segment loan_amount) / SUM(all loan_amount)` | Distinguish material exposure from high-rate but small segments. |
| Segment charge-off exposure | `SUM(loan_amount where status = 'Charged Off')` | Rank financial exposure associated with charged-off status; do not call it realized loss. |
| Top-3 concentration | `SUM(funded exposure of top 3 selected segments) / total funded exposure` | Portfolio concentration alert by state, grade, or purpose. The selected dimension must be stated. |
| Risk-review priority | A descriptive matrix of exposure, matured default rate, and resolved-loan count | Prioritize investigation; it is not a credit-decision score. |

## 4. Driver and guardrail metrics

| Type | Metric | Definition | Guardrail / operating rule |
|---|---|---|---|
| Driver | Issuance growth | `(current issue-month applications - previous issue-month applications) / previous issue-month applications` | Compare the same calendar convention and display `N/A` when prior period is zero. |
| Driver | Exposure growth | Same formula using funded exposure | Diagnose whether rising risk is paired with rising capital allocation. |
| Driver | Segment sample size | Count of resolved loans in the segment | Do not flag a segment based on rate alone when resolved count is under 100; label it `watch / insufficient evidence`. |
| Guardrail | Loan-ID uniqueness | `COUNT(DISTINCT id) = COUNT(id)` | Must equal 100% before reporting metrics. |
| Guardrail | Valid issue dates | `% of rows with parsed issue_date` | Must equal 100%; otherwise block period-based reporting. |
| Guardrail | Status coverage | `% of rows in the approved status taxonomy` | Must equal 100%; otherwise investigate before publishing. |
| Guardrail | Cross-tool reconciliation | Python = SQL = Power BI for a fixed filter set | Differences must be 0 for count and within $1 / 0.01 percentage points for rounded display. |
| Guardrail | Temporal consistency disclosure | Payment/credit-pull date contradictions are counted and disclosed | These fields are quarantined from timing, maturity, and feature-chronology claims until source semantics are verified. |

## 5. Provisional monitoring thresholds

No firm business-risk target can be set from this single extract because there is no policy benchmark, historical series, loss tolerance, or profitability data. The following are **review triggers**, not success targets or automatic policy rules:

| Trigger | Proposed rule | Required follow-up |
|---|---|---|
| Segment risk alert | Resolved-loan count >= 100 and segment matured default rate >= portfolio matured default rate + 3 percentage points | Review grade, purpose, DTI, and exposure; do not infer causality. |
| Concentration alert | A segment is in the top 3 by funded exposure and has an above-portfolio matured default rate | Add to monthly risk-review agenda. |
| Data-quality alert | Any required data-quality guardrail fails | Stop dashboard/report refresh until reconciled. |

Future targets should be anchored to documented risk appetite, expected loss, cost of funds, and a multi-period historical baseline.

## 6. Filter, time, and formatting rules

- **Numerator and denominator:** apply the same slicers unless the measure explicitly states otherwise.
- **Date:** issue-month trends use `issue_date`; status and payment fields are snapshot values, not event dates.
- **Date quarantine:** do not use `last_payment_date`, `last_credit_pull_date`, or `next_payment_date` for analytical timing claims in the current extract.
- **MTD naming:** in this historical dataset, use `Latest issue-month` instead of real-time `MTD` unless a refresh/as-of-date process is implemented.
- **Percentages:** store as decimals, display as percentages with one decimal place (for example, `0.1201` displays as `12.0%`).
- **Currency:** display USD rounded to $K/$M in cards and full USD in detail/reconciliation tables.
- **Missing `emp_title`:** fill with `Unknown` only for display/grouping; retain a missingness flag for data-quality reporting.

## 7. Explicitly prohibited interpretations

- `Cash collection ratio > 100%` does not prove net profitability.
- A high raw default rate with a small denominator does not justify a restrictive policy.
- A segment association does not establish that the segment attribute causes default.
- Results must not be described as a predictive default model or a production credit policy.

## 8. Metric ownership and acceptance test

| Artifact | Required action |
|---|---|
| Python notebook | Compute all primary KPIs from these definitions and display the denominator for outcome rates. |
| SQL | Replace month-only filters with year-month logic and implement the same formulas. |
| Power BI | Create named DAX measures matching the formulas and publish a measure dictionary. |
| README/report | Cite only reconciled KPI values and include the limitations above. |

The contract is accepted only after the baseline figures reconcile across Python, SQL, and Power BI for the unfiltered portfolio and a selected segment filter.
