/*
Bank Loan Portfolio — Canonical Risk Analytics SQL (SQL Server)
================================================================
Source table: dbo.bank_loan_data
Grain: one row per unique loan id
Governance: docs/metric_contract.md

Important:
- Current loans are unresolved and excluded from matured default rate.
- total_payment / loan_amount is a cash-collection ratio, not profit.
- Month comparisons use year + month and only complete issue months.
- Payment/credit-pull chronology is ungoverned until source semantics are verified.
*/

SET NOCOUNT ON;

/* 0. Source guardrails ---------------------------------------------------- */
SELECT
    COUNT(*) AS row_count,
    COUNT(DISTINCT id) AS distinct_loan_ids,
    SUM(CASE WHEN id IS NULL THEN 1 ELSE 0 END) AS null_loan_ids,
    SUM(CASE WHEN issue_date IS NULL THEN 1 ELSE 0 END) AS null_issue_dates,
    SUM(CASE WHEN loan_status NOT IN ('Fully Paid', 'Charged Off', 'Current')
             OR loan_status IS NULL THEN 1 ELSE 0 END) AS invalid_status_rows
FROM dbo.bank_loan_data;

/* 1. Canonical portfolio KPIs -------------------------------------------- */
WITH portfolio AS (
    SELECT
        COUNT(DISTINCT id) AS total_applications,
        SUM(CAST(loan_amount AS decimal(19, 2))) AS funded_exposure,
        SUM(CAST(total_payment AS decimal(19, 2))) AS total_amount_collected,
        COUNT(DISTINCT CASE
            WHEN loan_status IN ('Fully Paid', 'Charged Off') THEN id END)
            AS resolved_loans,
        COUNT(DISTINCT CASE WHEN loan_status = 'Charged Off' THEN id END)
            AS charged_off_loans,
        COUNT(DISTINCT CASE WHEN loan_status = 'Current' THEN id END)
            AS current_loans,
        AVG(CAST(int_rate AS decimal(19, 8))) AS average_interest_rate,
        AVG(CAST(dti AS decimal(19, 8))) AS average_dti
    FROM dbo.bank_loan_data
)
SELECT
    total_applications,
    funded_exposure,
    total_amount_collected,
    resolved_loans,
    charged_off_loans,
    current_loans,
    CAST(charged_off_loans AS decimal(19, 8)) / NULLIF(total_applications, 0)
        AS charge_off_share,
    CAST(charged_off_loans AS decimal(19, 8)) / NULLIF(resolved_loans, 0)
        AS matured_default_rate,
    CAST(current_loans AS decimal(19, 8)) / NULLIF(total_applications, 0)
        AS current_loan_share,
    total_amount_collected / NULLIF(funded_exposure, 0)
        AS cash_collection_ratio,
    average_interest_rate,
    average_dti
FROM portfolio;

/* 2. Latest two complete issue months ------------------------------------ */
DECLARE @MaxIssueDate date = (SELECT MAX(issue_date) FROM dbo.bank_loan_data);
DECLARE @LatestCompleteMonthEnd date =
    CASE
        WHEN @MaxIssueDate = EOMONTH(@MaxIssueDate) THEN EOMONTH(@MaxIssueDate)
        ELSE EOMONTH(@MaxIssueDate, -1)
    END;
DECLARE @LatestCompleteMonthStart date =
    DATEFROMPARTS(YEAR(@LatestCompleteMonthEnd), MONTH(@LatestCompleteMonthEnd), 1);
DECLARE @PreviousCompleteMonthEnd date = EOMONTH(@LatestCompleteMonthEnd, -1);
DECLARE @PreviousCompleteMonthStart date =
    DATEFROMPARTS(YEAR(@PreviousCompleteMonthEnd), MONTH(@PreviousCompleteMonthEnd), 1);

WITH complete_months AS (
    SELECT
        CASE
            WHEN issue_date >= @LatestCompleteMonthStart
             AND issue_date <= @LatestCompleteMonthEnd THEN 'Latest complete month'
            WHEN issue_date >= @PreviousCompleteMonthStart
             AND issue_date <= @PreviousCompleteMonthEnd THEN 'Previous complete month'
        END AS period_label,
        CASE
            WHEN issue_date >= @LatestCompleteMonthStart
             AND issue_date <= @LatestCompleteMonthEnd THEN @LatestCompleteMonthStart
            WHEN issue_date >= @PreviousCompleteMonthStart
             AND issue_date <= @PreviousCompleteMonthEnd THEN @PreviousCompleteMonthStart
        END AS period_start,
        id, loan_amount, total_payment, int_rate, dti
    FROM dbo.bank_loan_data
    WHERE issue_date >= @PreviousCompleteMonthStart
      AND issue_date <= @LatestCompleteMonthEnd
)
SELECT
    period_label,
    period_start,
    COUNT(DISTINCT id) AS total_applications,
    SUM(loan_amount) AS funded_exposure,
    SUM(total_payment) AS total_amount_collected,
    AVG(int_rate) AS average_interest_rate,
    AVG(dti) AS average_dti
FROM complete_months
GROUP BY period_label, period_start
ORDER BY period_start;

/* 3. Issue-month origination trend (not payment cash flow) ---------------- */
SELECT
    DATEFROMPARTS(YEAR(issue_date), MONTH(issue_date), 1) AS issue_month,
    COUNT(DISTINCT id) AS total_applications,
    SUM(loan_amount) AS funded_exposure,
    SUM(total_payment) AS recorded_payment_for_originated_loans
FROM dbo.bank_loan_data
GROUP BY DATEFROMPARTS(YEAR(issue_date), MONTH(issue_date), 1)
ORDER BY issue_month;

/* 4. Grade risk matrix ----------------------------------------------------- */
WITH portfolio AS (
    SELECT
        SUM(CAST(loan_amount AS decimal(19, 2))) AS portfolio_exposure,
        CAST(COUNT(DISTINCT CASE WHEN loan_status = 'Charged Off' THEN id END)
             AS decimal(19, 8))
        / NULLIF(COUNT(DISTINCT CASE
            WHEN loan_status IN ('Fully Paid', 'Charged Off') THEN id END), 0)
            AS portfolio_matured_default_rate
    FROM dbo.bank_loan_data
), grade_base AS (
    SELECT
        grade,
        COUNT(DISTINCT id) AS loan_count,
        SUM(CAST(loan_amount AS decimal(19, 2))) AS funded_exposure,
        COUNT(DISTINCT CASE
            WHEN loan_status IN ('Fully Paid', 'Charged Off') THEN id END)
            AS resolved_loans,
        COUNT(DISTINCT CASE WHEN loan_status = 'Charged Off' THEN id END)
            AS charged_off_loans
    FROM dbo.bank_loan_data
    GROUP BY grade
), grade_metrics AS (
    SELECT
        grade_base.*,
        CAST(charged_off_loans AS decimal(19, 8)) / NULLIF(resolved_loans, 0)
            AS matured_default_rate,
        funded_exposure / NULLIF(portfolio.portfolio_exposure, 0)
            AS funded_exposure_share,
        portfolio.portfolio_matured_default_rate
    FROM grade_base
    CROSS JOIN portfolio
)
SELECT
    grade,
    loan_count,
    funded_exposure,
    funded_exposure_share,
    resolved_loans,
    charged_off_loans,
    matured_default_rate,
    (matured_default_rate - portfolio_matured_default_rate) * 100
        AS default_rate_vs_portfolio_pp,
    funded_exposure * matured_default_rate AS risk_exposure_proxy,
    CASE
        WHEN resolved_loans < 100 THEN 'Watch: insufficient evidence'
        WHEN loan_count < 500 THEN 'Watch: small segment'
        WHEN matured_default_rate >= portfolio_matured_default_rate + 0.03
         AND funded_exposure_share >= 0.02 THEN 'High'
        WHEN matured_default_rate >= portfolio_matured_default_rate THEN 'Medium'
        ELSE 'Monitor'
    END AS review_priority
FROM grade_metrics
ORDER BY grade;

/* 5. State concentration and outcome risk -------------------------------- */
WITH portfolio AS (
    SELECT
        SUM(CAST(loan_amount AS decimal(19, 2))) AS portfolio_exposure,
        CAST(COUNT(DISTINCT CASE WHEN loan_status = 'Charged Off' THEN id END)
             AS decimal(19, 8))
        / NULLIF(COUNT(DISTINCT CASE
            WHEN loan_status IN ('Fully Paid', 'Charged Off') THEN id END), 0)
            AS portfolio_matured_default_rate
    FROM dbo.bank_loan_data
), state_base AS (
    SELECT
        address_state,
        COUNT(DISTINCT id) AS loan_count,
        SUM(CAST(loan_amount AS decimal(19, 2))) AS funded_exposure,
        COUNT(DISTINCT CASE
            WHEN loan_status IN ('Fully Paid', 'Charged Off') THEN id END)
            AS resolved_loans,
        COUNT(DISTINCT CASE WHEN loan_status = 'Charged Off' THEN id END)
            AS charged_off_loans
    FROM dbo.bank_loan_data
    GROUP BY address_state
)
SELECT
    address_state,
    loan_count,
    funded_exposure,
    funded_exposure / NULLIF(portfolio.portfolio_exposure, 0)
        AS funded_exposure_share,
    resolved_loans,
    charged_off_loans,
    CAST(charged_off_loans AS decimal(19, 8)) / NULLIF(resolved_loans, 0)
        AS matured_default_rate,
    (CAST(charged_off_loans AS decimal(19, 8)) / NULLIF(resolved_loans, 0)
        - portfolio.portfolio_matured_default_rate) * 100
        AS default_rate_vs_portfolio_pp
FROM state_base
CROSS JOIN portfolio
ORDER BY funded_exposure DESC;

/* 6. Purpose × term review matrix ---------------------------------------- */
WITH portfolio AS (
    SELECT
        SUM(CAST(loan_amount AS decimal(19, 2))) AS portfolio_exposure,
        CAST(COUNT(DISTINCT CASE WHEN loan_status = 'Charged Off' THEN id END)
             AS decimal(19, 8))
        / NULLIF(COUNT(DISTINCT CASE
            WHEN loan_status IN ('Fully Paid', 'Charged Off') THEN id END), 0)
            AS portfolio_matured_default_rate
    FROM dbo.bank_loan_data
), segment_base AS (
    SELECT
        purpose,
        LTRIM(RTRIM(term)) AS term,
        COUNT(DISTINCT id) AS loan_count,
        SUM(CAST(loan_amount AS decimal(19, 2))) AS funded_exposure,
        COUNT(DISTINCT CASE
            WHEN loan_status IN ('Fully Paid', 'Charged Off') THEN id END)
            AS resolved_loans,
        COUNT(DISTINCT CASE WHEN loan_status = 'Charged Off' THEN id END)
            AS charged_off_loans
    FROM dbo.bank_loan_data
    GROUP BY purpose, LTRIM(RTRIM(term))
), segment_metrics AS (
    SELECT
        segment_base.*,
        CAST(charged_off_loans AS decimal(19, 8)) / NULLIF(resolved_loans, 0)
            AS matured_default_rate,
        funded_exposure / NULLIF(portfolio.portfolio_exposure, 0)
            AS funded_exposure_share,
        portfolio.portfolio_matured_default_rate
    FROM segment_base
    CROSS JOIN portfolio
)
SELECT
    purpose,
    term,
    loan_count,
    funded_exposure,
    funded_exposure_share,
    resolved_loans,
    charged_off_loans,
    matured_default_rate,
    (matured_default_rate - portfolio_matured_default_rate) * 100
        AS default_rate_vs_portfolio_pp,
    funded_exposure * matured_default_rate AS risk_exposure_proxy
FROM segment_metrics
ORDER BY risk_exposure_proxy DESC;

/* 7. DTI monitoring bands ------------------------------------------------- */
WITH dti_base AS (
    SELECT
        CASE
            WHEN dti <= 0.15 THEN N'≤15%'
            WHEN dti <= 0.20 THEN N'15–20%'
            ELSE N'>20%'
        END AS dti_band,
        id, loan_amount, loan_status
    FROM dbo.bank_loan_data
)
SELECT
    dti_band,
    COUNT(DISTINCT id) AS loan_count,
    SUM(loan_amount) AS funded_exposure,
    COUNT(DISTINCT CASE
        WHEN loan_status IN ('Fully Paid', 'Charged Off') THEN id END)
        AS resolved_loans,
    COUNT(DISTINCT CASE WHEN loan_status = 'Charged Off' THEN id END)
        AS charged_off_loans,
    CAST(COUNT(DISTINCT CASE WHEN loan_status = 'Charged Off' THEN id END)
         AS decimal(19, 8))
    / NULLIF(COUNT(DISTINCT CASE
        WHEN loan_status IN ('Fully Paid', 'Charged Off') THEN id END), 0)
        AS matured_default_rate
FROM dti_base
GROUP BY dti_band
ORDER BY CASE dti_band WHEN N'≤15%' THEN 1 WHEN N'15–20%' THEN 2 ELSE 3 END;

/* 8. Known temporal-consistency warnings --------------------------------- */
SELECT
    SUM(CASE WHEN last_payment_date < issue_date THEN 1 ELSE 0 END)
        AS last_payment_before_issue,
    SUM(CASE WHEN last_credit_pull_date < issue_date THEN 1 ELSE 0 END)
        AS last_credit_pull_before_issue,
    SUM(CASE WHEN next_payment_date < last_payment_date THEN 1 ELSE 0 END)
        AS next_payment_before_last_payment,
    SUM(CASE
        WHEN loan_status IN ('Fully Paid', 'Charged Off')
         AND next_payment_date IS NOT NULL THEN 1 ELSE 0 END)
        AS resolved_with_next_payment_date
FROM dbo.bank_loan_data;

/* 9. Baseline reconciliation — differences must be zero ------------------ */
WITH actual AS (
    SELECT
        COUNT(DISTINCT id) AS total_applications,
        SUM(CAST(loan_amount AS decimal(19, 2))) AS funded_exposure,
        SUM(CAST(total_payment AS decimal(19, 2))) AS total_amount_collected,
        COUNT(DISTINCT CASE
            WHEN loan_status IN ('Fully Paid', 'Charged Off') THEN id END)
            AS resolved_loans,
        COUNT(DISTINCT CASE WHEN loan_status = 'Charged Off' THEN id END)
            AS charged_off_loans,
        COUNT(DISTINCT CASE WHEN loan_status = 'Current' THEN id END)
            AS current_loans
    FROM dbo.bank_loan_data
)
SELECT
    total_applications - 38576 AS total_applications_difference,
    funded_exposure - CAST(435757075 AS decimal(19, 2))
        AS funded_exposure_difference,
    total_amount_collected - CAST(473070933 AS decimal(19, 2))
        AS total_amount_collected_difference,
    resolved_loans - 37478 AS resolved_loans_difference,
    charged_off_loans - 5333 AS charged_off_loans_difference,
    current_loans - 1098 AS current_loans_difference
FROM actual;

/* 10. Detail table for investigation, not an underwriting decision view --- */
SELECT
    id,
    issue_date,
    loan_status,
    CASE WHEN loan_status = 'Current' THEN 'Current (unresolved)' ELSE 'Resolved' END
        AS outcome_state,
    purpose,
    grade,
    sub_grade,
    LTRIM(RTRIM(term)) AS term,
    address_state,
    home_ownership,
    verification_status,
    emp_length,
    annual_income,
    dti,
    int_rate,
    loan_amount AS funded_exposure,
    installment,
    total_payment AS recorded_payment
FROM dbo.bank_loan_data;
