# Bank Loan Portfolio Analytics — Business Scope

## 1. Initiative summary

This project is a retrospective **portfolio analytics** case study for a consumer-lending portfolio. It uses loan-level records issued during 2021 to help a Credit Risk and Portfolio Management audience identify risk concentration, monitor portfolio health, and prioritize review actions.

It is **not** a credit-scoring or default-prediction model. No result in this project should be interpreted as an automated approval, decline, pricing, or profitability decision.

## 2. Decision to support

The analysis supports the following operating decision:

> Which loan segments should Credit Risk monitor or review first, given their combination of funded exposure, observed charge-off performance, and concentration?

The intended users and actions are:

| User | Review cadence | Decision enabled |
|---|---|---|
| Credit Risk Manager | Monthly portfolio review | Prioritize underwriting-policy or segment-review investigations. |
| Portfolio Manager | Monthly portfolio review | Monitor funded-exposure concentration and set escalation alerts. |
| Collections / Finance Analyst | Monthly reconciliation | Reconcile loan status, payments, and portfolio cash collection. |

## 3. Business questions

1. What are the portfolio's scale, status mix, funded exposure, and cash-collection profile?
2. Which grades, purposes, terms, states, and borrower-profile segments show both material exposure and above-baseline observed risk?
3. Is exposure concentrated in a small number of segments or geographies that merit monitoring?
4. Which findings are strong enough to justify a policy-review hypothesis, and which require more data before action?

## 4. Scope and grain

| Item | Contract |
|---|---|
| Source of truth | `data/financial_loan.csv` until a governed warehouse source is available. |
| Grain | One row per loan application / loan ID (`id`). |
| Portfolio period | Loans with `issue_date` from 2021-01-01 through 2021-12-12 after parsing dates as `dd-mm-yyyy`. |
| Population | 38,576 unique loan IDs in the supplied CSV. |
| Currency | USD, as implied by the supplied loan and payment fields. |
| Status snapshot | The extract's loan status as provided; its exact observation/as-of date is not documented. |
| Canonical Python implementation | `src/risk_metrics.py`; notebooks must import it rather than redefine KPI formulas. |

## 5. In-scope dimensions

- Loan status, issued month, grade and sub-grade.
- State, purpose, term, home ownership, employment length, verification status.
- Loan amount, installment, interest rate, DTI, annual income, total payment.

## 6. Explicitly out of scope

- Default prediction, automated underwriting, and causal claims.
- Net profit, ROI, expected loss, or recovery economics. The dataset lacks cost of funds, operating costs, recovery timing, loss-given-default, and an as-of date.
- Fair-lending/fairness assessment. The available data does not establish protected-class fields, an approved methodology, or policy context.
- Claims that a segment characteristic *causes* default. Results are descriptive associations only.

## 7. Analysis principles

1. Compare risk with exposure and sample size; never rank a segment on rate alone.
2. Treat `Current` loans as unresolved when assessing observed outcome performance.
3. Use `issue_date` for origination trends. Never use `MONTH(issue_date)` without the year in SQL or DAX time comparisons.
4. Reconcile Python, SQL, and Power BI outputs to the definitions in `docs/metric_contract.md`.
5. Label every recommendation as a review hypothesis unless it is validated through policy backtesting or an experiment.

## 8. Key limitations and required disclosures

- The status observation date and loan maturity horizon are unavailable. `Current` loans may later become either Fully Paid or Charged Off, so outcome metrics are subject to right-censoring.
- Cross-field payment and credit-pull dates are internally inconsistent. Only `issue_date` is approved for origination trends until the source/anonymization process is verified.
- `total_payment / loan_amount` is a cash-collection ratio, not profit or a complete recovery/economic-return measure.
- State, grade, DTI, employment length, and purpose may be correlated. Segment comparisons do not control for confounding factors.
- The dataset source, refresh cadence, and collection methodology must be documented before external publication.

## 9. Completion criteria for this phase

The project is release-ready when the KPI definitions in `docs/metric_contract.md` are the only authoritative definitions used by Python, SQL, Power BI, README, and the executive summary; automated reconciliation passes; and the Power BI release checklist is complete.
