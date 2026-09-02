# Power BI DAX Measure Dictionary

## Purpose

This document is the implementation companion to [KPI Contract](metric_contract.md). It defines the Power BI measures used in `dashboard/Bank_loan.pbix` so that dashboard values reconcile with Python, SQL, and the executive summary.

**Model assumption:** the fact table is named `bank_loan_data`. Replace this name consistently if the Power BI model uses another name.  
**Data grain:** one row per loan ID (`id`).  
**Status taxonomy:** `Fully Paid`, `Charged Off`, and `Current`.

## Model setup

### Date table

Create a dedicated date table and mark it as a date table. Use an active one-to-many relationship from `Dim Date[Date]` to `bank_loan_data[issue_date]`.

```DAX
Dim Date =
VAR StartDate =
    MINX ( ALL ( bank_loan_data ), bank_loan_data[issue_date] )
VAR EndDate =
    MAXX ( ALL ( bank_loan_data ), bank_loan_data[issue_date] )
RETURN
ADDCOLUMNS (
    CALENDAR ( StartDate, EndDate ),
    "Year", YEAR ( [Date] ),
    "Month Number", MONTH ( [Date] ),
    "Month Name", FORMAT ( [Date], "MMM" ),
    "Year Month", FORMAT ( [Date], "YYYY-MM" ),
    "Year Month Sort", YEAR ( [Date] ) * 100 + MONTH ( [Date] )
)
```

Sort `Dim Date[Year Month]` by `Dim Date[Year Month Sort]`. Do not use `MONTH(issue_date)` by itself for a time comparison because it mixes years.

### Optional calculated columns for risk visuals

```DAX
Resolved Status =
IF (
    bank_loan_data[loan_status] = "Current",
    "Current (unresolved)",
    "Resolved"
)

DTI Band =
SWITCH (
    TRUE (),
    bank_loan_data[dti] <= 0.15, "≤15%",
    bank_loan_data[dti] <= 0.20, "15–20%",
    ">20%"
)
```

Use `Resolved Status` and `DTI Band` only as descriptive dimensions. They are not approval or decline rules.

## Core portfolio measures

```DAX
Total Applications =
DISTINCTCOUNT ( bank_loan_data[id] )

Funded Exposure =
SUM ( bank_loan_data[loan_amount] )

Total Amount Collected =
SUM ( bank_loan_data[total_payment] )

Average Interest Rate =
AVERAGE ( bank_loan_data[int_rate] )

Average DTI =
AVERAGE ( bank_loan_data[dti] )
```

| Measure | Display format | Interpretation |
|---|---|---|
| Total Applications | `#,0` | Distinct loan IDs in the active filter context. |
| Funded Exposure | `$#,0,,.0M;-$#,0,,.0M;$0` | Capital funded in the active filter context. |
| Total Amount Collected | `$#,0,,.0M;-$#,0,,.0M;$0` | Payments recorded in the extract; not a period cash-flow measure unless a payment-date filter is explicitly introduced. |
| Average Interest Rate | `0.0%` | Descriptive pricing metric only. |
| Average DTI | `0.0%` | Descriptive borrower-capacity metric only. |

## Status and outcome measures

```DAX
Resolved Loans =
CALCULATE (
    [Total Applications],
    KEEPFILTERS (
        bank_loan_data[loan_status]
            IN { "Fully Paid", "Charged Off" }
    )
)

Charged-Off Loans =
CALCULATE (
    [Total Applications],
    KEEPFILTERS ( bank_loan_data[loan_status] = "Charged Off" )
)

Current Loans =
CALCULATE (
    [Total Applications],
    KEEPFILTERS ( bank_loan_data[loan_status] = "Current" )
)

Fully Paid Loans =
CALCULATE (
    [Total Applications],
    KEEPFILTERS ( bank_loan_data[loan_status] = "Fully Paid" )
)

Charge-Off Share =
DIVIDE ( [Charged-Off Loans], [Total Applications] )

Matured Default Rate =
DIVIDE ( [Charged-Off Loans], [Resolved Loans] )

Current Loan Share =
DIVIDE ( [Current Loans], [Total Applications] )

Cash Collection Ratio =
DIVIDE ( [Total Amount Collected], [Funded Exposure] )
```

| Measure | Display format | Required label / caveat |
|---|---|---|
| Charge-Off Share | `0.0%` | Snapshot share of all loans recorded as charged off. |
| Matured Default Rate | `0.0%` | `Charged Off / (Charged Off + Fully Paid)`; excludes unresolved Current loans. This is the primary outcome-risk measure. |
| Current Loan Share | `0.0%` | Share of loans whose outcome is unresolved in the supplied extract. |
| Cash Collection Ratio | `0.0%` | Payments divided by funded amount. Do **not** label this as profit, net revenue, realised return, or complete recovery. |

Do not use `Good Loan Rate` as the principal risk KPI because it combines `Current` with `Fully Paid`. If retained for a status-mix visual, name it `Fully Paid + Current Status Share` and add a tooltip that `Current` loans are unresolved.

## Risk and concentration measures

```DAX
Charged-Off Funded Exposure =
CALCULATE (
    [Funded Exposure],
    KEEPFILTERS ( bank_loan_data[loan_status] = "Charged Off" )
)

Risk-Exposure Proxy =
[Funded Exposure] * [Matured Default Rate]

Portfolio Matured Default Rate (All Data) =
CALCULATE (
    [Matured Default Rate],
    REMOVEFILTERS ( bank_loan_data ),
    REMOVEFILTERS ( 'Dim Date' )
)

Matured Default Rate vs Portfolio (pp) =
([Matured Default Rate] - [Portfolio Matured Default Rate (All Data)]) * 100

Funded Exposure Share by Grade =
DIVIDE (
    [Funded Exposure],
    CALCULATE ( [Funded Exposure], REMOVEFILTERS ( bank_loan_data[grade] ) )
)
```

`Risk-Exposure Proxy` is for review prioritization only. It is not expected loss or realised loss because the dataset does not contain loss-given-default, recovery timing, cost of funds, or operating cost.

### Grade-matrix review label

Use this measure only in a matrix grouped by `grade` or `sub_grade`.

```DAX
Grade Review Status =
VAR LoanCount = [Total Applications]
VAR ResolvedCount = [Resolved Loans]
VAR Rate = [Matured Default Rate]
VAR ExposureShare = [Funded Exposure Share by Grade]
VAR Benchmark = [Portfolio Matured Default Rate (All Data)]
RETURN
SWITCH (
    TRUE (),
    LoanCount < 500, "Watch: small segment",
    ResolvedCount < 100, "Watch: insufficient evidence",
    Rate >= Benchmark + 0.03 && ExposureShare >= 0.02, "High",
    Rate >= Benchmark, "Medium",
    "Monitor"
)
```

This is a monitoring label. It must not drive an automated credit-decision rule.

## Latest complete issue-month measures

The supplied extract ends on 12 December 2021. Therefore, do **not** label December as MTD or compare it with a complete November month without an explicit partial-period rule.

Use `Latest Complete Issue Month` for historical reporting:

```DAX
Max Issue Date =
CALCULATE (
    MAX ( bank_loan_data[issue_date] ),
    REMOVEFILTERS ( 'Dim Date' )
)

Latest Complete Issue Month End =
EOMONTH ( [Max Issue Date], -1 )

Applications — Latest Complete Issue Month =
VAR MonthEnd = [Latest Complete Issue Month End]
VAR MonthStart = DATE ( YEAR ( MonthEnd ), MONTH ( MonthEnd ), 1 )
RETURN
CALCULATE (
    [Total Applications],
    REMOVEFILTERS ( 'Dim Date' ),
    DATESBETWEEN ( 'Dim Date'[Date], MonthStart, MonthEnd )
)

Applications — Previous Complete Issue Month =
VAR MonthEnd = EOMONTH ( [Latest Complete Issue Month End], -1 )
VAR MonthStart = DATE ( YEAR ( MonthEnd ), MONTH ( MonthEnd ), 1 )
RETURN
CALCULATE (
    [Total Applications],
    REMOVEFILTERS ( 'Dim Date' ),
    DATESBETWEEN ( 'Dim Date'[Date], MonthStart, MonthEnd )
)

Applications MoM — Latest Complete Month =
DIVIDE (
    [Applications — Latest Complete Issue Month]
        - [Applications — Previous Complete Issue Month],
    [Applications — Previous Complete Issue Month]
)
```

Repeat the same complete-month pattern for funded exposure and collected amount if a period comparison is needed. Display the label `Latest Complete Issue Month`, not `MTD`.

## Visual mapping

| Dashboard area | Required measures | Design rule |
|---|---|---|
| Summary cards | Total Applications, Funded Exposure, Matured Default Rate, Current Loan Share, Cash Collection Ratio | Keep one metric per card; show status definition in a tooltip or footer. |
| Loan-status visual | Total Applications, Funded Exposure, Current Loan Share | Treat as a status mix; do not call Current a good outcome. |
| Grade matrix | Funded Exposure, Matured Default Rate, Resolved Loans, Risk-Exposure Proxy, Grade Review Status | Show denominator and review label. |
| State risk matrix | Funded Exposure, Matured Default Rate, Resolved Loans | Use state as a monitoring dimension, not a causal claim. |
| Purpose × term visual | Matured Default Rate, Funded Exposure, Resolved Loans | Compare risk with exposure; avoid rate-only ranking. |
| Detail table | Interest rate, DTI, Issue Month, Resolved Status | Format rates as percentages, never decimals such as `0.12`. |

The Details page must be an investigation view, not a legacy MTD scorecard. Remove the `Good vs Bad Loan` slicer, expose the supplied status plus `Resolved Status`, and do not compare partial December with a complete prior month.

For home-ownership and other category risk bars, bind the unscaled decimal `[Matured Default Rate]` measure and format it as `0.0%`. Do not apply display units such as thousands or millions to percentage measures.

## Baseline reconciliation tests

Validate the unfiltered dashboard against the supplied CSV before publishing any screenshot or Power BI Service link.

| Measure | Expected baseline |
|---|---:|
| Total Applications | 38,576 |
| Funded Exposure | $435,757,075 |
| Total Amount Collected | $473,070,933 |
| Charge-Off Share | 13.82% |
| Resolved Loans | 37,478 |
| Matured Default Rate | 14.23% |
| Current Loan Share | 2.85% |
| Cash Collection Ratio | 108.56% |
| Average Interest Rate | 12.05% |
| Average DTI | 13.33% |

Spot checks:

| Filter context | Matured Default Rate | Resolved Loans |
|---|---:|---:|
| Grade F | 32.5% | 957 |
| Grade G | 33.1% | 296 |
| California | 15.7% | 6,751 |
| DTI >20% | 16.2% | 6,986 |

## Dashboard QA checklist

- [ ] Every percentage uses a `%` format string.
- [ ] `Matured Default Rate` excludes `Current` loans in all visuals.
- [ ] No visual claims Cash Collection Ratio is profitability or net revenue.
- [ ] `MTD` labels are removed unless a valid refresh/as-of-date process is implemented.
- [ ] Slicers apply consistently; status slicers cannot silently change the outcome denominator without visible context.
- [ ] Summary, Overview, and Details pages reconcile for the same filter context.
- [ ] Risk visuals display funded exposure and resolved-loan count alongside rate.
- [ ] The title is spelled `Summary`, not `Sumary`.
