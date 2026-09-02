"""Canonical Risk Analytics metrics for the bank-loan portfolio.

Every Python notebook, SQL reconciliation check, Power BI measure, and report
should implement the definitions documented in ``docs/metric_contract.md``.
This module is the Python source of truth for those calculations.
"""

from __future__ import annotations

from pathlib import Path
from statistics import NormalDist
from typing import Sequence

import numpy as np
import pandas as pd


VALID_STATUSES = frozenset({"Fully Paid", "Charged Off", "Current"})
RESOLVED_STATUSES = frozenset({"Fully Paid", "Charged Off"})
DATE_FORMAT = "%d-%m-%Y"
DEFAULT_DATA_PATH = Path("data/financial_loan.csv")


def load_loan_data(path: str | Path = DEFAULT_DATA_PATH) -> pd.DataFrame:
    """Load the source extract, normalize stable categories, and add risk flags."""
    data = pd.read_csv(path)
    validate_loan_data(data)

    data = data.copy()
    data["issue_date"] = pd.to_datetime(
        data["issue_date"], format=DATE_FORMAT, errors="raise"
    )
    data["term"] = data["term"].astype("string").str.strip()
    data["is_resolved"] = data["loan_status"].isin(RESOLVED_STATUSES)
    data["is_charged_off"] = data["loan_status"].eq("Charged Off")
    data["is_current"] = data["loan_status"].eq("Current")
    data["issue_month"] = data["issue_date"].dt.to_period("M")
    data["dti_band"] = pd.cut(
        data["dti"],
        bins=[-0.001, 0.15, 0.20, 1.0],
        labels=["≤15%", "15–20%", ">20%"],
        include_lowest=True,
    )
    return data


def validate_loan_data(data: pd.DataFrame) -> None:
    """Raise a clear error when a core KPI guardrail fails."""
    required = {
        "id",
        "loan_status",
        "issue_date",
        "loan_amount",
        "total_payment",
        "int_rate",
        "dti",
        "grade",
        "purpose",
        "term",
    }
    missing = sorted(required.difference(data.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if data["id"].isna().any() or not data["id"].is_unique:
        raise ValueError("Loan ID must be populated and unique at loan grain")
    invalid_statuses = sorted(set(data["loan_status"].dropna()) - VALID_STATUSES)
    if data["loan_status"].isna().any() or invalid_statuses:
        raise ValueError(f"Invalid loan_status values: {invalid_statuses}")
    if (data["loan_amount"] <= 0).any():
        raise ValueError("loan_amount must be positive")
    if (data["total_payment"] < 0).any():
        raise ValueError("total_payment cannot be negative")
    if not data["int_rate"].between(0, 1, inclusive="right").all():
        raise ValueError("int_rate must be stored as a decimal in (0, 1]")
    if not data["dti"].between(0, 1, inclusive="both").all():
        raise ValueError("dti must be stored as a decimal in [0, 1]")
    parsed_issue_date = pd.to_datetime(
        data["issue_date"], format=DATE_FORMAT, errors="coerce"
    )
    if parsed_issue_date.isna().any():
        raise ValueError("issue_date must be populated and parse as dd-mm-yyyy")


def portfolio_kpis(data: pd.DataFrame) -> pd.Series:
    """Return the canonical unfiltered portfolio KPI set."""
    loan_count = int(data["id"].nunique())
    resolved_count = int(data["is_resolved"].sum())
    charged_off_count = int(data["is_charged_off"].sum())
    current_count = int(data["is_current"].sum())
    funded_exposure = float(data["loan_amount"].sum())
    total_collected = float(data["total_payment"].sum())

    return pd.Series(
        {
            "total_applications": loan_count,
            "funded_exposure": funded_exposure,
            "total_amount_collected": total_collected,
            "resolved_loans": resolved_count,
            "charged_off_loans": charged_off_count,
            "current_loans": current_count,
            "charge_off_share": charged_off_count / loan_count,
            "matured_default_rate": charged_off_count / resolved_count,
            "current_loan_share": current_count / loan_count,
            "cash_collection_ratio": total_collected / funded_exposure,
            "average_interest_rate": float(data["int_rate"].mean()),
            "average_dti": float(data["dti"].mean()),
        },
        name="portfolio",
    )


def wilson_interval(
    successes: int | float, total: int | float, confidence: float = 0.95
) -> tuple[float, float]:
    """Return a Wilson confidence interval for a binomial outcome rate."""
    if total <= 0:
        return (np.nan, np.nan)
    z_value = NormalDist().inv_cdf(0.5 + confidence / 2)
    proportion = successes / total
    denominator = 1 + z_value**2 / total
    centre = (proportion + z_value**2 / (2 * total)) / denominator
    margin = (
        z_value
        * np.sqrt(
            (proportion * (1 - proportion) + z_value**2 / (4 * total)) / total
        )
        / denominator
    )
    return (centre - margin, centre + margin)


def segment_summary(
    data: pd.DataFrame, group_columns: str | Sequence[str]
) -> pd.DataFrame:
    """Summarize exposure, outcome risk, uncertainty, and review priority."""
    if isinstance(group_columns, str):
        group_columns = [group_columns]
    group_columns = list(group_columns)

    portfolio = portfolio_kpis(data)
    portfolio_rate = float(portfolio["matured_default_rate"])
    portfolio_exposure = float(portfolio["funded_exposure"])

    summary = (
        data.groupby(group_columns, dropna=False, observed=False)
        .agg(
            loan_count=("id", "nunique"),
            funded_exposure=("loan_amount", "sum"),
            resolved_loans=("is_resolved", "sum"),
            charged_off_loans=("is_charged_off", "sum"),
            current_loans=("is_current", "sum"),
        )
        .reset_index()
    )
    summary["matured_default_rate"] = np.divide(
        summary["charged_off_loans"],
        summary["resolved_loans"],
        out=np.full(len(summary), np.nan, dtype=float),
        where=summary["resolved_loans"].to_numpy() > 0,
    )
    intervals = [
        wilson_interval(charged_off, resolved)
        for charged_off, resolved in zip(
            summary["charged_off_loans"], summary["resolved_loans"]
        )
    ]
    summary[["ci_low", "ci_high"]] = pd.DataFrame(
        intervals, index=summary.index
    )
    summary["funded_exposure_share"] = (
        summary["funded_exposure"] / portfolio_exposure
    )
    summary["default_rate_vs_portfolio_pp"] = (
        summary["matured_default_rate"] - portfolio_rate
    ) * 100
    summary["risk_exposure_proxy"] = (
        summary["funded_exposure"] * summary["matured_default_rate"]
    )
    summary["review_priority"] = summary.apply(
        lambda row: _review_priority(row, portfolio_rate), axis=1
    )
    # Backward-compatible display alias used by the existing EDA notebook.
    summary["priority"] = summary["review_priority"]
    return summary


def _review_priority(row: pd.Series, portfolio_rate: float) -> str:
    if row["resolved_loans"] < 100:
        return "Watch: insufficient evidence"
    if row["loan_count"] < 500:
        return "Watch: small segment"
    if (
        row["matured_default_rate"] >= portfolio_rate + 0.03
        and row["funded_exposure_share"] >= 0.02
    ):
        return "High"
    if row["matured_default_rate"] >= portfolio_rate:
        return "Medium"
    return "Monitor"


def latest_complete_issue_month(data: pd.DataFrame) -> pd.Period:
    """Return the latest fully observed issue month in the extract."""
    maximum_date = pd.Timestamp(data["issue_date"].max())
    maximum_period = maximum_date.to_period("M")
    if maximum_date.normalize() == maximum_period.end_time.normalize():
        return maximum_period
    return maximum_period - 1


def complete_month_comparison(data: pd.DataFrame) -> pd.DataFrame:
    """Compare the latest two complete issue months without calling either MTD."""
    current_period = latest_complete_issue_month(data)
    previous_period = current_period - 1
    rows = []
    for period in [previous_period, current_period]:
        period_data = data.loc[data["issue_month"].eq(period)]
        rows.append(
            {
                "issue_month": str(period),
                "total_applications": int(period_data["id"].nunique()),
                "funded_exposure": float(period_data["loan_amount"].sum()),
                "total_amount_collected": float(period_data["total_payment"].sum()),
                "average_interest_rate": float(period_data["int_rate"].mean()),
                "average_dti": float(period_data["dti"].mean()),
            }
        )
    comparison = pd.DataFrame(rows)
    for metric in [
        "total_applications",
        "funded_exposure",
        "total_amount_collected",
        "average_interest_rate",
        "average_dti",
    ]:
        previous_value = comparison.loc[0, metric]
        comparison.loc[1, f"{metric}_mom"] = (
            (comparison.loc[1, metric] - previous_value) / previous_value
            if previous_value
            else np.nan
        )
    return comparison


def temporal_consistency_profile(data: pd.DataFrame) -> pd.DataFrame:
    """Profile cross-field date contradictions without silently deleting rows."""
    parsed = data.copy()
    date_columns = [
        "issue_date",
        "last_payment_date",
        "last_credit_pull_date",
        "next_payment_date",
    ]
    for column in date_columns:
        parsed[column] = pd.to_datetime(
            parsed[column], format=DATE_FORMAT, errors="coerce"
        )

    rules = [
        (
            "last_payment_before_issue",
            parsed["last_payment_date"] < parsed["issue_date"],
            "Payment timing and vintage analysis",
        ),
        (
            "last_credit_pull_before_issue",
            parsed["last_credit_pull_date"] < parsed["issue_date"],
            "Credit-pull timing and feature chronology",
        ),
        (
            "next_payment_before_last_payment",
            parsed["next_payment_date"] < parsed["last_payment_date"],
            "Payment schedule chronology",
        ),
        (
            "resolved_with_next_payment_date",
            parsed["loan_status"].isin(RESOLVED_STATUSES)
            & parsed["next_payment_date"].notna(),
            "Status/date consistency",
        ),
    ]
    return pd.DataFrame(
        [
            {
                "rule": rule,
                "affected_rows": int(mask.sum()),
                "affected_rate": float(mask.mean()),
                "risk": risk,
            }
            for rule, mask, risk in rules
        ]
    )
