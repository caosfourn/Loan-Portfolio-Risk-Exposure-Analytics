from __future__ import annotations

import unittest

import pandas as pd

from src.data_quality import run_full_audit


class DataQualityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        raw = pd.read_csv("data/financial_loan.csv")
        cls.audit = run_full_audit(raw)

    def test_no_core_guardrail_failure(self) -> None:
        self.assertEqual(self.audit["n_fail"], 0)

    def test_source_term_whitespace_is_detected(self) -> None:
        normalization = self.audit["string_normalization"].set_index("column")
        self.assertEqual(int(normalization.loc["term", "affected_rows"]), 38_576)

    def test_temporal_risk_is_not_silently_passed(self) -> None:
        temporal = self.audit["temporal_consistency"].set_index("rule")
        self.assertGreater(int(temporal.loc["last_payment_before_issue", "affected_rows"]), 0)
        self.assertGreater(int(temporal.loc["last_credit_pull_before_issue", "affected_rows"]), 0)


if __name__ == "__main__":
    unittest.main()
