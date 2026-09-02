# 2021 Loan Portfolio — Priority Risk Actions

**Decision supported:** Prioritize portfolio-review actions using observed outcome risk, funded exposure, and sample size.  
**Audience:** Credit Risk Manager, Portfolio Manager, and Underwriting Lead.  
**Scope:** 38,576 unique loans issued from 1 January to 12 December 2021. This is a retrospective portfolio analysis, not a credit-scoring model or an approval/decline policy.

## Executive Summary

- **Prioritize Debt consolidation × 60 months for a policy-review backtest.** This segment accounts for $92.8M of funded exposure (21.3% of the portfolio) and has a 26.1% matured default rate across 4,824 resolved loans—11.9 percentage points above the 14.2% portfolio benchmark. It has the largest descriptive risk-exposure proxy in the reviewed segment set ($24.2M).

- **Investigate why the lowest-risk grade carries less exposure than Grades B and C.** Grade A has the lowest matured default rate (5.7%) but only $84.3M of funded exposure, compared with $130.7M for Grade B and $87.5M for Grade C. Grade A has more loans than Grade C, but its smaller average loan amount ($8.7K vs. $11.1K) results in lower total exposure. This is a capital-allocation hypothesis, not a recommendation to expand Grade A lending without demand, approval, pricing, and profitability evidence.

- **Treat Florida as the stronger state-level risk-monitoring signal.** Florida has a 17.8% matured default rate on $30.0M of exposure. Its rate is approximately 3.75 percentage points above the rate expected from its grade mix, so the signal warrants composition analysis rather than being dismissed as a simple consequence of lower grades.

- **Treat California primarily as a concentration watch item.** California carries the largest state exposure ($78.5M; 18.0% of portfolio funding), but its 15.7% matured default rate is only approximately 1.18 percentage points above its grade-mix expectation. The main operational concern is concentration, not evidence of unusually poor state credit quality.

**Supporting finding:** Loans with DTI >20% have a 16.2% matured default rate, approximately 1.28 percentage points above their grade-mix expectation. Retain DTI as a monitoring guardrail, but do not introduce a hard cutoff from this descriptive analysis.

## How to read the evidence

**Matured default rate** is the share of resolved loans recorded as `Charged Off`: `Charged Off / (Charged Off + Fully Paid)`. It excludes the 1,098 `Current` loans (2.85% of the portfolio) because their outcome is unresolved.

**Risk-exposure proxy** is funded exposure multiplied by the matured default rate. It is a prioritization proxy only—not expected loss, realised loss, profit, or savings. The extract does not provide the as-of date, maturity horizon, cost of funds, loss-given-default, or recovery timing needed for those measures.

Portfolio benchmark: **14.23% matured default rate**, based on **37,478 resolved loans**.

## Insight hierarchy

| Role | Insight | Status |
|---|---|---|
| **P0 · Headline risk** | Debt consolidation × 60 months | Decision-driving backtest candidate |
| **P1 · Opportunity hypothesis** | Grade A exposure gap | Requires demand, approval, pricing, and profitability evidence |
| **P1 · Risk monitoring** | Florida | Stronger state residual after accounting for grade mix |
| **P2 · Concentration monitoring** | California | Large exposure; modest residual risk |
| **Supporting guardrail** | DTI >20% | Monitor; insufficient basis for a hard cutoff |

## Why Debt consolidation × 60 months is the first review hypothesis

**The segment combines material scale and elevated observed risk.** The 60-month debt-consolidation segment has 5,391 loans, $92.8M funded exposure, and a 26.1% matured default rate (1,260 charge-offs out of 4,824 resolved loans). Its rate is 11.9 percentage points above the portfolio benchmark and its risk-exposure proxy is $24.2M.

For comparison, 36-month debt-consolidation loans have a 10.8% matured default rate across 12,823 resolved loans. This contrast warrants a backtest of purpose, term, grade, DTI, and pricing interactions; it does **not** prove that the 60-month term or debt-consolidation purpose causes charge-offs.

## Grade A combines the lowest observed risk with lower dollar exposure

**The exposure pattern is not explained by loan count alone.** Grade A has 9,689 loans, $84.3M of funded exposure, an $8.7K average loan amount, and a 5.7% matured default rate. Grade B has both more loans (11,674) and a larger average amount ($11.2K), producing $130.7M of exposure. More notably, Grade C has fewer loans than Grade A (7,904) but greater exposure ($87.5M) because its average loan amount is approximately $11.1K.

The appropriate next step is to decompose the Grade A exposure gap across application demand, approval rate, requested amount, approved amount, term, purpose, and pricing. Expected loss and risk-adjusted return are also required before concluding that the portfolio should allocate more capital to Grade A borrowers.

## Florida is the stronger state-level risk signal

Florida has 2,773 loans, $30.0M of exposure, and a 17.8% matured default rate across 2,691 resolved loans. A grade-mix benchmark implies an expected rate of approximately 14.05%, leaving a +3.75 percentage-point residual. This does not establish that geography causes defaults, but it makes Florida the more credible state-level risk-monitoring hypothesis.

The next step is to test whether term, purpose, loan size, verification status, or other borrower mix explains the residual before any policy escalation.

## California is primarily a concentration watch item

California has 6,894 loans, $78.5M of funded exposure, and a 15.7% matured default rate across 6,751 resolved loans. Its grade-mix expected rate is approximately 14.48%, leaving a more modest +1.18 percentage-point residual. California remains operationally important because it represents 18.0% of portfolio funding, but the evidence supports a concentration alert more strongly than an abnormal-risk claim.

## Supporting finding — DTI above 20%

Loans with DTI above 20% have $84.0M of exposure and a 16.2% matured default rate across 6,986 resolved loans. Their grade-mix expected rate is approximately 14.95%, leaving a +1.28 percentage-point residual. This is useful as a monitoring variable and a control in deeper analysis, but it is not strong enough to support a hard underwriting cutoff.

## Recommended actions

| Priority | Evidence | Recommended action | Owner | Expected impact | Risk / limitation |
|---|---|---|---|---|---|
| **P0** | **Debt consolidation × 60 months:** $92.8M exposure (21.3% of portfolio), 26.1% matured default rate, resolved `n=4,824`, +11.9 pp vs portfolio, $24.2M risk-exposure proxy. | Run a policy/pricing backtest segmented by grade, DTI, verification status, and loan amount; test whether a revised term, pricing, or review workflow improves the risk mix. | Underwriting Lead + Credit Risk | Focuses the first review on the largest observed risk-exposure proxy. | Descriptive result only; no loss, cost, or causal data. Do not automatically restrict this segment before backtesting. |
| **P1** | **Grade A exposure gap:** 9,689 loans, $84.3M exposure, $8.7K average loan amount, and 5.7% matured default rate. Exposure is below Grade B ($130.7M) and Grade C ($87.5M); Grade C has fewer loans but a larger $11.1K average amount. | Decompose the gap by application volume, approval rate, requested and approved amount, purpose, term, and pricing; then compare expected loss and risk-adjusted return before proposing an allocation change. | Credit Risk + Lending Strategy | Tests whether the safest observed grade represents a responsible growth opportunity or simply reflects demand and product mix. | The extract contains originated loans only and cannot distinguish demand, approval policy, selection effects, or profitability. |
| **P1** | **Florida:** $30.0M exposure, 17.8% matured default rate (`n=2,691`), approximately +3.75 pp vs grade-mix expectation. | Add a monthly state-risk alert and decompose the residual by term, purpose, loan size, and verification status before escalation. | Portfolio Manager + Credit Risk | Tests a non-obvious state signal that is not explained by grade mix alone. | Geography is not causal; omitted borrower or macro factors may explain the residual. |
| **P2** | **California:** $78.5M exposure (18.0% of portfolio), 15.7% matured default rate (`n=6,751`), approximately +1.18 pp vs grade-mix expectation. | Add a concentration threshold and exposure trend alert; investigate credit risk only if the residual or rate deteriorates. | Portfolio Manager | Controls the portfolio's largest geographic concentration without overstating abnormal risk. | Concentration tolerance is not documented; the residual is descriptive and modest. |
| **P2 · Supporting** | **DTI >20%:** $84.0M exposure, 16.2% matured default rate, resolved `n=6,986`, approximately +1.28 pp vs grade-mix expectation. | Retain DTI in monitoring and controlled backtests; do **not** impose a hard cutoff from this EDA. | Underwriting Lead + Analytics | Provides a guardrail without prematurely reducing approvals. | DTI is correlated with other borrower and loan attributes; the observed difference is not an optimal-policy estimate. |

## Exposure decomposition — why Grade A is below Grades B and C

Funded exposure can be decomposed as `loan count × average loan amount`. This separates a volume effect from a loan-sizing effect.

| Grade | Loans | Average loan amount | Funded exposure | Matured default rate |
|---|---:|---:|---:|---:|
| A | 9,689 | $8.7K | $84.3M | 5.7% |
| B | 11,674 | $11.2K | $130.7M | 11.8% |
| C | 7,904 | $11.1K | $87.5M | 16.6% |

**Interpretation:** Grade B's higher exposure reflects both greater volume and larger loans. Grade C's higher exposure is different: it has 1,785 fewer loans than Grade A, but its average loan amount is approximately 27% larger. The pattern suggests that Grade A is underrepresented in funded dollars, especially through loan size. It does not show whether the cause is borrower demand, requested amounts, underwriting limits, product mix, or pricing—and therefore does not by itself justify expanding Grade A exposure.

## Further questions before a policy decision

1. Does the 60-month debt-consolidation signal persist after controlling for grade, DTI, income, verification status, and loan amount?
2. What is the status observation date and minimum maturity window for each loan cohort? This is required to make fair vintage comparisons.
3. What are loss-given-default, recovery timing, cost of funds, and operating costs? These are required to estimate expected loss or profitability.
4. Does Grade A's lower exposure originate from application demand, approval rates, requested amounts, policy limits, or product and purpose mix?
5. What is the documented risk appetite and policy constraint for grade, term, DTI, and state concentration?

## Caveats and assumptions

- The CSV is a single supplied extract of 2021-originated loans; the source, refresh cadence, and status as-of date are not documented.
- Payment and credit-pull date chronology is inconsistent in the supplied extract. These fields are excluded from timing and maturity claims until source semantics are verified.
- The analysis measures association, not causality. Segment outcomes may be confounded by loan and borrower mix.
- `Current` loans are excluded from matured default-rate denominators; later issue cohorts may be less mature and therefore not directly comparable.
- Cash collection, default-rate, and risk-exposure proxy metrics are not profitability or expected-loss measures.
- All numeric evidence is implemented in `src/risk_metrics.py`, reproduced in `notebooks/bank_loan_report.ipynb` and `notebooks/02_portfolio_eda.ipynb`, and governed by `docs/metric_contract.md`.
