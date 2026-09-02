# Bank Loan Analysis — Business Problem Statement

> **Canonical governance documents:** [Business Scope](../docs/business_scope.md) and [KPI Contract](../docs/metric_contract.md). These documents supersede any conflicting KPI labels, targets, or interpretations below.

## 1. Executive Summary & Business Context

Financial institutions need a consistent view of portfolio scale, risk concentration, and loan-status outcomes before prioritizing credit-policy reviews. This project analyzes **38,576 unique loan records** issued in 2021 and supports monthly portfolio monitoring for Credit Risk and Portfolio Management.

The work is retrospective portfolio analytics. It identifies descriptive associations and review hypotheses; it is not a default-prediction model, automated underwriting policy, or profitability analysis.

---

## 2. Business Objectives
1. **Monitor portfolio scale and status:** Track applications, funded exposure, collected cash, loan status mix, and issue-month trends.
2. **Assess observed outcome performance:** Separate resolved loans (`Fully Paid`, `Charged Off`) from unresolved `Current` loans when comparing outcomes.
3. **Identify risk concentration for review:** Compare funded exposure, outcome rates, and sample sizes across:
   - Credit Rating Grades & Sub-grades (Grades A through G).
   - Geographic regions (US State level).
   - Employment length & home ownership status.
4. **Identify issuance trends:** Detect changes in application and funding volume to inform monitoring and liquidity-planning discussions.

---

## 3. KPI Contract

The project uses the following primary KPI categories:

- Portfolio scale: total applications and funded exposure.
- Outcome/status: charge-off share, matured default rate, and current-loan share.
- Financial diagnostics: collected cash, cash collection ratio, average interest rate, and average DTI.
- Risk concentration: segment-level exposure, matured default rate, charged-off exposure, and top-3 concentration.

All formulas, baselines, caveats, formatting rules, and proposed review triggers are maintained in the [KPI Contract](../docs/metric_contract.md). There are no firm business-risk targets in the current project because risk appetite, cost, loss-timing, and multi-period benchmark data are unavailable.

---

## 4. Dataset Overview
- **Source File:** `financial_loan.csv`
- **Total Records:** 38,576 rows
- **Columns:** 24 supplied features. Analysis notebooks may derive date fields for period reporting.
- **Key Fields:** `id`, `loan_amount`, `total_payment`, `loan_status`, `int_rate`, `dti`, `grade`, `sub_grade`, `emp_length`, `home_ownership`, `issue_date`, `address_state`.

---

## 5. Deliverables & Project Architecture
1. **Data-quality notebook (`notebooks/01_data_quality.ipynb`):** Governed source checks, temporal-consistency warnings, and limitations register.
2. **Risk Analyst notebook (`notebooks/bank_loan_report.ipynb`):** Canonical portfolio KPI, exposure-risk, segment, and complete-month analysis.
3. **Deep segment EDA (`notebooks/02_portfolio_eda.ipynb`):** Confidence intervals and grade, state, purpose-term, DTI, employment, and vintage views.
4. **Interactive Power BI Dashboard (`dashboard/Bank_loan.pbix`):** Summary, portfolio-risk overview, and investigation details.
5. **Canonical SQL (`Query.sql`):** SQL Server implementation of the KPI contract plus cross-tool reconciliation tests.
6. **Reusable Python (`src/risk_metrics.py`):** Single Python source of truth imported by notebooks and automated tests.
