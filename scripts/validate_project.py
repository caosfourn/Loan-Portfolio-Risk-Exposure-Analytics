"""One-command structural, analytical, and reconciliation validation."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.risk_metrics import load_loan_data, portfolio_kpis  # noqa: E402


REQUIRED_FILES = [
    "README.md",
    "requirements.txt",
    "pyproject.toml",
    "LICENSE",
    "Query.sql",
    "docs/business_scope.md",
    "docs/metric_contract.md",
    "docs/dax_measures.md",
    "docs/data_dictionary.md",
    "docs/data_provenance.md",
    "notebooks/01_data_quality.ipynb",
    "notebooks/02_portfolio_eda.ipynb",
    "notebooks/bank_loan_report.ipynb",
    "src/data_quality.py",
    "src/risk_metrics.py",
]


def check_required_files() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    if missing:
        raise AssertionError(f"Missing required project files: {missing}")


def check_notebooks() -> None:
    required_sections = ["## tl;dr", "## Context & Methods", "## Data", "## Results", "## Takeaways"]
    for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload.get("nbformat") == 4, f"{path.name}: invalid nbformat"
        markdown_text = "\n".join(
            "".join(cell.get("source", []))
            for cell in payload["cells"]
            if cell.get("cell_type") == "markdown"
        )
        positions = [markdown_text.find(section) for section in required_sections]
        if any(position < 0 for position in positions) or positions != sorted(positions):
            raise AssertionError(f"{path.name}: required analytical section order is missing")
        for index, cell in enumerate(payload["cells"], start=1):
            if cell.get("cell_type") == "code":
                source = "".join(cell.get("source", []))
                compile(source, f"{path.name}:cell_{index}", "exec")


def check_sql_contract() -> None:
    sql = (ROOT / "Query.sql").read_text(encoding="utf-8").lower()
    required_terms = [
        "matured_default_rate",
        "current_loan_share",
        "resolved_loans",
        "risk_exposure_proxy",
        "latest complete month",
        "reconciliation",
    ]
    missing = [term for term in required_terms if term not in sql]
    if missing:
        raise AssertionError(f"Query.sql is missing canonical concepts: {missing}")
    forbidden = ["month(issue_date) = 12", "good_loan_percentage", "bad_loan_percentage"]
    found = [term for term in forbidden if term in sql]
    if found:
        raise AssertionError(f"Query.sql still contains legacy logic: {found}")


def check_baseline() -> None:
    loans = load_loan_data(ROOT / "data" / "financial_loan.csv")
    kpis = portfolio_kpis(loans)
    expected = {
        "total_applications": 38_576,
        "funded_exposure": 435_757_075,
        "total_amount_collected": 473_070_933,
        "resolved_loans": 37_478,
        "charged_off_loans": 5_333,
        "current_loans": 1_098,
    }
    for metric, value in expected.items():
        if int(kpis[metric]) != value:
            raise AssertionError(f"{metric}: expected {value}, received {kpis[metric]}")


def run_tests() -> None:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise AssertionError("Automated tests failed")


def main() -> None:
    check_required_files()
    check_notebooks()
    check_sql_contract()
    check_baseline()
    run_tests()
    print("\nPROJECT VALIDATION PASSED")
    print("- Canonical KPI baseline reconciled")
    print("- SQL contract checks passed")
    print("- Notebook JSON and code cells are structurally valid")
    print("- Automated tests passed")
    print("Note: execute notebooks with Jupyter before publishing rendered outputs.")


if __name__ == "__main__":
    main()
