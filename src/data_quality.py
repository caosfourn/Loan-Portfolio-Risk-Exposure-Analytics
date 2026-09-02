"""
src/data_quality.py
===================
Reusable data-quality audit functions for the Bank Loan Portfolio project.

Governance:  docs/metric_contract.md  |  docs/business_scope.md
Data grain:  one row per loan ID (column `id`)
Date format: dd-mm-yyyy  (issue_date, last_payment_date, …)
Status taxonomy:  Fully Paid | Charged Off | Current
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from .risk_metrics import (
    temporal_consistency_profile,
    validate_loan_data as validate_canonical_loan_data,
)

# ── logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("data_quality")

# ── constants (aligned with metric_contract.md) ──────────────────────────────
VALID_STATUSES = {"Fully Paid", "Charged Off", "Current"}
DATE_FORMAT = "%d-%m-%Y"
DATE_COLS = ["issue_date", "last_payment_date", "last_credit_pull_date", "next_payment_date"]
NUMERIC_POSITIVE_COLS = ["loan_amount", "installment", "annual_income", "total_payment"]
OUTLIER_COLS = ["annual_income", "loan_amount", "int_rate", "dti"]
EXPECTED_ROWS = 38_576
REQUIRED_COLS = [
    "id", "loan_status", "issue_date", "loan_amount", "int_rate",
    "dti", "annual_income", "grade", "term", "purpose", "total_payment",
]


# ── result container ──────────────────────────────────────────────────────────
@dataclass
class DQResult:
    """Aggregates all data-quality findings from a single audit run."""
    checks: list[dict[str, Any]] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    fixes_log: list[str] = field(default_factory=list)

    def add_check(
        self,
        check: str,
        status: str,          # "PASS" | "WARN" | "FAIL"
        detail: str,
        value: Any = None,
    ) -> None:
        self.checks.append({"check": check, "status": status, "detail": detail, "value": value})
        level = {"PASS": logging.INFO, "WARN": logging.WARNING, "FAIL": logging.ERROR}.get(status, logging.DEBUG)
        log.log(level, "[%s] %s — %s", status, check, detail)

    def summary_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.checks)[["check", "status", "detail", "value"]]

    def has_blocking_failures(self) -> bool:
        return any(c["status"] == "FAIL" for c in self.checks)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. SCHEMA & BASIC STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════════

def check_shape(df: pd.DataFrame, result: DQResult) -> None:
    """Report extract shape and warn on any drift from the governed snapshot."""
    n_rows, n_cols = df.shape
    status = "PASS" if n_rows == EXPECTED_ROWS else "WARN"
    result.add_check(
        "Row count",
        status,
        f"{n_rows:,} rows, {n_cols} columns (governed snapshot: {EXPECTED_ROWS:,})",
        {"rows": n_rows, "cols": n_cols},
    )


def check_required_columns(df: pd.DataFrame, result: DQResult) -> None:
    """Verify all required columns exist."""
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        result.add_check("Required columns", "FAIL", f"Missing columns: {missing}", missing)
    else:
        result.add_check("Required columns", "PASS", "All required columns present")


def check_duplicates(df: pd.DataFrame, result: DQResult) -> None:
    """Check for duplicate rows and duplicate loan IDs (guardrail in section 4 of metric_contract)."""
    dup_rows = int(df.duplicated().sum())
    if dup_rows:
        result.add_check("Duplicate rows", "FAIL", f"{dup_rows:,} fully-duplicated rows found", dup_rows)
    else:
        result.add_check("Duplicate rows", "PASS", "No fully-duplicated rows")

    if "id" in df.columns:
        dup_ids = int(df["id"].duplicated().sum())
        if dup_ids:
            result.add_check("Duplicate loan IDs", "FAIL", f"{dup_ids:,} duplicate IDs -- guardrail violated", dup_ids)
        else:
            result.add_check("Duplicate loan IDs", "PASS", "All loan IDs unique (guardrail satisfied)")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. MISSING VALUES
# ═══════════════════════════════════════════════════════════════════════════════

def check_missing(df: pd.DataFrame, result: DQResult) -> pd.DataFrame:
    """
    Compute missing-value profile.  Returns a DataFrame with counts, pct,
    and recommended handling strategy.

    Strategy rules (aligned with section 6 of metric_contract.md):
    - issue_date / loan_status / id / loan_amount / int_rate / dti -> FAIL (block reporting)
    - emp_title -> fill 'Unknown' for display only; retain missingness flag
    - next_payment_date -> expected missing for Fully Paid / Charged Off
    - others < 1% -> impute or drop with log
    - others >= 1% -> WARN, investigate before imputing
    """
    n = len(df)
    mv = (
        df.isnull().sum()
        .rename("missing_count")
        .to_frame()
        .assign(missing_pct=lambda x: x["missing_count"] / n * 100)
    )
    mv = mv[mv["missing_count"] > 0].sort_values("missing_pct", ascending=False)

    blocking = {"id", "loan_status", "issue_date", "loan_amount", "int_rate", "dti"}
    strategy_map = {
        "emp_title": "Fill 'Unknown' for grouping display; retain `emp_title_missing` flag",
        "next_payment_date": "Expected missing for Fully Paid / Charged Off -- no action needed",
        "last_payment_date": "WARN if > 5% missing; check for data extract issue",
        "annual_income": "WARN -- required for DTI context; impute median by grade only if < 2%",
        "emp_length": "WARN -- retain as-is; treat blank as separate category in segmentation",
    }
    strategies = []
    for col in mv.index:
        pct = mv.loc[col, "missing_pct"]
        if col in blocking:
            s = "FAIL -- block reporting until resolved"
            result.add_check(f"Missing: {col}", "FAIL", f"{mv.loc[col,'missing_count']:,} missing ({pct:.2f}%)")
        elif col in strategy_map:
            s = strategy_map[col]
            status = "WARN" if pct >= 1 else "PASS"
            result.add_check(f"Missing: {col}", status, f"{mv.loc[col,'missing_count']:,} missing ({pct:.2f}%)")
        elif pct >= 1:
            s = "WARN -- investigate before imputing; flag in limitations"
            result.add_check(f"Missing: {col}", "WARN", f"{mv.loc[col,'missing_count']:,} missing ({pct:.2f}%)")
        else:
            s = "Low impact (< 1%) -- impute or drop with log"
            result.add_check(f"Missing: {col}", "PASS", f"{mv.loc[col,'missing_count']:,} missing ({pct:.2f}%)")
        strategies.append(s)

    mv["strategy"] = strategies
    return mv.reset_index().rename(columns={"index": "column"})


# ═══════════════════════════════════════════════════════════════════════════════
# 3. DOMAIN VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def validate_loan_data(df: pd.DataFrame) -> None:
    """
    Hard assertions -- must all pass before any KPI is computed.
    (Specification from metric_contract.md section 4 guardrails.)
    """
    validate_canonical_loan_data(df)


def check_domain_rules(df: pd.DataFrame, result: DQResult) -> pd.DataFrame:
    """
    Soft domain checks: amount > 0, DTI range, int_rate range, date parse.
    Returns a summary DataFrame of violations per rule.
    """
    violations: list[dict] = []

    def _check(name: str, mask: pd.Series, fail_level: str = "FAIL") -> None:
        bad = int(mask.sum())
        pct = bad / len(df) * 100
        status = fail_level if bad > 0 else "PASS"
        result.add_check(name, status, f"{bad:,} violations ({pct:.2f}%)", bad)
        if bad > 0:
            violations.append({"rule": name, "violations": bad, "pct": round(pct, 4)})

    # Positive amounts
    for col in NUMERIC_POSITIVE_COLS:
        if col in df.columns:
            _check(f"{col} > 0", df[col] <= 0)

    # Interest rate: 0 < int_rate <= 1 (stored as decimal, e.g. 0.1527)
    if "int_rate" in df.columns:
        _check("int_rate in (0, 1]", ~df["int_rate"].between(0.001, 1.0, inclusive="both"))

    # DTI: 0 <= dti <= 1 (stored as decimal ratio)
    if "dti" in df.columns:
        _check("dti in [0, 1]", ~df["dti"].between(0.0, 1.0, inclusive="both"), fail_level="WARN")

    # Date parse
    for col in DATE_COLS:
        if col in df.columns:
            parsed = pd.to_datetime(df[col], format=DATE_FORMAT, errors="coerce")
            bad_dates = parsed.isna() & df[col].notna()
            n_bad = int(bad_dates.sum())
            status = "FAIL" if (col == "issue_date" and n_bad > 0) else ("WARN" if n_bad > 0 else "PASS")
            result.add_check(
                f"Date parse: {col}",
                status,
                f"{n_bad:,} unparseable values",
                n_bad,
            )
            if n_bad > 0:
                violations.append({"rule": f"date_parse:{col}", "violations": n_bad, "pct": round(n_bad / len(df) * 100, 4)})

    # Status taxonomy (guardrail section 4)
    if "loan_status" in df.columns:
        bad_status = ~df["loan_status"].isin(VALID_STATUSES)
        n_bad = int(bad_status.sum())
        status = "FAIL" if n_bad > 0 else "PASS"
        result.add_check("loan_status taxonomy", status, f"{n_bad:,} out-of-taxonomy values", n_bad)

    return pd.DataFrame(violations) if violations else pd.DataFrame(columns=["rule", "violations", "pct"])


def check_string_normalization(df: pd.DataFrame, result: DQResult) -> pd.DataFrame:
    """Find categorical values whose whitespace can split dashboard groups."""
    rows: list[dict[str, Any]] = []
    for column in ["term", "grade", "purpose", "emp_length", "home_ownership"]:
        if column not in df.columns:
            continue
        values = df[column].dropna().astype("string")
        affected = int(values.ne(values.str.strip()).sum())
        status = "WARN" if affected else "PASS"
        result.add_check(
            f"String normalization: {column}",
            status,
            f"{affected:,} rows contain leading or trailing whitespace",
            affected,
        )
        rows.append(
            {
                "column": column,
                "affected_rows": affected,
                "affected_rate": affected / len(df) if len(df) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def check_temporal_consistency(df: pd.DataFrame, result: DQResult) -> pd.DataFrame:
    """Flag cross-field chronology issues without assuming how dates were anonymized."""
    required_dates = {
        "issue_date",
        "last_payment_date",
        "last_credit_pull_date",
        "next_payment_date",
        "loan_status",
    }
    if not required_dates.issubset(df.columns):
        missing = sorted(required_dates.difference(df.columns))
        result.add_check(
            "Temporal consistency",
            "WARN",
            f"Could not run cross-field chronology checks; missing: {missing}",
        )
        return pd.DataFrame()

    profile = temporal_consistency_profile(df)
    for row in profile.itertuples(index=False):
        status = "WARN" if row.affected_rows else "PASS"
        result.add_check(
            f"Temporal rule: {row.rule}",
            status,
            f"{row.affected_rows:,} rows ({row.affected_rate:.2%}) — impacts {row.risk}",
            row.affected_rows,
        )
    if int(profile["affected_rows"].sum()) > 0:
        result.limitations.append(
            "Cross-field date chronology is inconsistent. Treat payment, credit-pull, "
            "and maturity timing as ungoverned until the source/anonymization process is verified."
        )
    return profile


# ═══════════════════════════════════════════════════════════════════════════════
# 4. OUTLIER ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class OutlierReport:
    column: str
    p01: float
    p25: float
    p50: float
    p75: float
    p99: float
    iqr: float
    lower_fence: float
    upper_fence: float
    n_below_fence: int
    n_above_fence: int
    classification: str   # "data_error" | "valid_extreme" | "needs_business_validation"
    recommendation: str


def classify_outliers(
    df: pd.DataFrame,
    col: str,
    result: DQResult,
) -> OutlierReport:
    """
    IQR-fence outlier analysis for a single numeric column.

    Classification rules (do NOT auto-delete):
      data_error              -> log + fix/remove with log
      valid_extreme           -> keep; use log-scale / percentile cap
      needs_business_validation -> add to limitations
    """
    s = df[col].dropna()
    p01, p25, p50, p75, p99 = np.percentile(s, [1, 25, 50, 75, 99])
    iqr = p75 - p25
    lower = p25 - 1.5 * iqr
    upper = p75 + 1.5 * iqr
    n_below = int((s < lower).sum())
    n_above = int((s > upper).sum())

    # Column-specific classification rules
    if col == "annual_income":
        n_zero = int((s <= 0).sum())
        if n_zero > 0:
            classification = "data_error"
            rec = f"Remove / investigate {n_zero:,} rows with annual_income <= 0 (log each drop)"
            result.fixes_log.append(f"annual_income: {n_zero} rows <= 0 found -- must be reviewed")
        elif n_above > 0:
            classification = "needs_business_validation"
            rec = (
                f"{n_above:,} records exceed upper fence (${upper:,.0f}). "
                "Retain; use log-scale or 99th-pct cap in visualisations. "
                "Validate whether high-income outliers skew average-income KPIs."
            )
            result.limitations.append(
                f"`annual_income`: {n_above:,} extreme-high values (> ${upper:,.0f}) kept. "
                "Average income may be pulled upward; consider median for segment comparisons."
            )
        else:
            classification = "valid_extreme"
            rec = "Distribution looks reasonable; retain all values."

    elif col == "loan_amount":
        n_neg = int((s <= 0).sum())
        if n_neg > 0:
            classification = "data_error"
            rec = f"{n_neg:,} rows with loan_amount <= 0 -- remove with log"
            result.fixes_log.append(f"loan_amount: {n_neg} rows <= 0 -- domain violation, remove")
        else:
            classification = "valid_extreme"
            rec = "Large loan amounts are product-design valid; retain. Use log-scale in histograms."

    elif col == "int_rate":
        n_bad = int((s > 1.0).sum())
        if n_bad > 0:
            classification = "data_error"
            rec = f"{n_bad:,} int_rate > 1.0 -- likely entered as percentage, divide by 100"
            result.fixes_log.append(f"int_rate: {n_bad} values > 1.0 -- check unit encoding")
        else:
            classification = "valid_extreme"
            rec = "Interest-rate extremes plausible for sub-prime grades; retain."

    elif col == "dti":
        n_high = int((s > 0.50).sum())
        if n_high > 0:
            classification = "needs_business_validation"
            rec = (
                f"{n_high:,} borrowers with DTI > 50%. "
                "Retain; flag in limitations -- may indicate data-entry errors or underserved segments."
            )
            result.limitations.append(
                f"`dti`: {n_high:,} records with DTI > 50% kept pending business validation."
            )
        else:
            classification = "valid_extreme"
            rec = "DTI distribution within expected range."
    else:
        classification = "valid_extreme"
        rec = "Retain all values; apply log-scale / percentile cap in visualisations."

    n_outliers = n_below + n_above
    status = "WARN" if n_outliers > 0 else "PASS"
    result.add_check(
        f"Outlier: {col}",
        status,
        f"{n_outliers:,} IQR-fence outliers ({n_below} below, {n_above} above) -> {classification}",
        {"n_outliers": n_outliers, "classification": classification},
    )

    return OutlierReport(
        column=col, p01=p01, p25=p25, p50=p50, p75=p75, p99=p99,
        iqr=iqr, lower_fence=lower, upper_fence=upper,
        n_below_fence=n_below, n_above_fence=n_above,
        classification=classification, recommendation=rec,
    )


def outlier_summary_df(reports: list[OutlierReport]) -> pd.DataFrame:
    """Convert a list of OutlierReport objects into a printable DataFrame."""
    rows = []
    for r in reports:
        rows.append({
            "column": r.column,
            "p01": round(r.p01, 4),
            "p25": round(r.p25, 4),
            "p50 (median)": round(r.p50, 4),
            "p75": round(r.p75, 4),
            "p99": round(r.p99, 4),
            "IQR fence [lower, upper]": f"[{r.lower_fence:,.2f}, {r.upper_fence:,.2f}]",
            "n_below_fence": r.n_below_fence,
            "n_above_fence": r.n_above_fence,
            "classification": r.classification,
            "recommendation": r.recommendation,
        })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. LOAN STATUS DISTRIBUTION
# ═══════════════════════════════════════════════════════════════════════════════

def loan_status_distribution(df: pd.DataFrame, result: DQResult) -> pd.DataFrame:
    """
    Distribution of loan_status (contract section 2).
    Also computes matured_default_rate as per KPI contract section 3.
    """
    if "loan_status" not in df.columns:
        result.add_check(
            "Loan status coverage", "FAIL", "loan_status is missing; outcome metrics cannot run"
        )
        return pd.DataFrame(columns=["loan_status", "count", "pct_of_portfolio"])

    counts = df["loan_status"].value_counts().rename("count")
    pct = (counts / len(df) * 100).round(2).rename("pct_of_portfolio")
    dist = pd.concat([counts, pct], axis=1).reset_index().rename(columns={"index": "loan_status"})

    resolved = df[df["loan_status"].isin(["Fully Paid", "Charged Off"])]
    n_resolved = len(resolved)
    n_charged_off = int((resolved["loan_status"] == "Charged Off").sum())
    matured_default_rate = (n_charged_off / n_resolved * 100) if n_resolved > 0 else None

    result.add_check(
        "Loan status coverage",
        "PASS" if dist["loan_status"].isin(list(VALID_STATUSES)).all() else "FAIL",
        f"Statuses present: {sorted(df['loan_status'].unique().tolist())}",
    )
    result.add_check(
        "Matured default rate",
        "PASS",
        f"{matured_default_rate:.2f}% (Charged Off / resolved loans, n={n_resolved:,})",
        round(matured_default_rate, 4) if matured_default_rate else None,
    )

    return dist


# ═══════════════════════════════════════════════════════════════════════════════
# 6. TEMPORAL COLUMN AVAILABILITY
# ═══════════════════════════════════════════════════════════════════════════════

def column_availability_by_issue_month(df: pd.DataFrame, result: DQResult) -> pd.DataFrame:
    """
    For each column, compute % non-null by issue_date month.
    Flags columns whose availability drops below 95% in any month.
    Addresses: 'Tinh san co cua tung cot theo thoi diem cap khoan vay.'
    """
    if "issue_date" not in df.columns:
        result.add_check("Temporal availability", "FAIL", "issue_date missing -- cannot compute")
        return pd.DataFrame()

    work = df.copy()
    work["_issue_ym"] = pd.to_datetime(work["issue_date"], format=DATE_FORMAT, errors="coerce").dt.to_period("M")

    avail_rows = []
    for col in df.columns:
        if col in ("id", "issue_date", "_issue_ym"):
            continue
        monthly = (
            work.groupby("_issue_ym")[col]
            .apply(lambda s: s.notna().mean() * 100)
            .rename("availability_pct")
            .reset_index()
            .rename(columns={"_issue_ym": "issue_month"})
        )
        monthly["column"] = col
        min_avail = monthly["availability_pct"].min()
        monthly["below_95_pct"] = monthly["availability_pct"] < 95
        avail_rows.append(monthly)

        if min_avail < 95:
            result.add_check(
                f"Temporal avail: {col}",
                "WARN",
                f"Availability drops to {min_avail:.1f}% in at least one month",
                round(min_avail, 2),
            )

    if not avail_rows:
        return pd.DataFrame()

    return pd.concat(avail_rows, ignore_index=True)[["column", "issue_month", "availability_pct", "below_95_pct"]]


# ═══════════════════════════════════════════════════════════════════════════════
# 7. FULL AUDIT RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def run_full_audit(df: pd.DataFrame) -> dict[str, Any]:
    """
    Run all data-quality checks in sequence.
    Returns a dict of all artifacts produced during the audit.

    Usage
    -----
    >>> import pandas as pd
    >>> from src.data_quality import run_full_audit
    >>> df = pd.read_csv("data/financial_loan.csv")
    >>> results = run_full_audit(df)
    >>> results["dq_summary"]
    """
    result = DQResult()

    log.info("=" * 60)
    log.info("DATA QUALITY AUDIT -- Bank Loan Portfolio")
    log.info("=" * 60)

    # 1. Shape & schema
    check_shape(df, result)
    check_required_columns(df, result)

    # 2. Duplicates (guardrails)
    check_duplicates(df, result)

    # 3. Missing values
    mv_df = check_missing(df, result)

    # 4. Domain validation
    violations_df = check_domain_rules(df, result)

    # 5. Category normalization and temporal consistency
    normalization_df = check_string_normalization(df, result)
    temporal_consistency_df = check_temporal_consistency(df, result)

    # 6. Outliers
    outlier_reports = [classify_outliers(df, col, result) for col in OUTLIER_COLS if col in df.columns]
    ol_df = outlier_summary_df(outlier_reports)

    # 7. Status distribution
    status_df = loan_status_distribution(df, result)

    # 8. Temporal availability
    temporal_df = column_availability_by_issue_month(df, result)

    # -- final summary --------------------------------------------------------
    dq_summary = result.summary_df()
    n_pass = int((dq_summary["status"] == "PASS").sum())
    n_warn = int((dq_summary["status"] == "WARN").sum())
    n_fail = int((dq_summary["status"] == "FAIL").sum())
    log.info("AUDIT COMPLETE: %d PASS | %d WARN | %d FAIL", n_pass, n_warn, n_fail)

    if result.fixes_log:
        log.warning("FIXES REQUIRED:\n  " + "\n  ".join(result.fixes_log))
    if result.limitations:
        log.info("LIMITATIONS:\n  " + "\n  ".join(result.limitations))

    return {
        "dq_summary": dq_summary,
        "missing_values": mv_df,
        "domain_violations": violations_df,
        "string_normalization": normalization_df,
        "temporal_consistency": temporal_consistency_df,
        "outlier_reports": outlier_reports,
        "outlier_summary": ol_df,
        "status_distribution": status_df,
        "temporal_availability": temporal_df,
        "result_obj": result,
        "n_pass": n_pass,
        "n_warn": n_warn,
        "n_fail": n_fail,
    }
