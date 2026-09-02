from __future__ import annotations

import unittest

from src.risk_metrics import (
    complete_month_comparison,
    latest_complete_issue_month,
    load_loan_data,
    portfolio_kpis,
    segment_summary,
    temporal_consistency_profile,
)


class RiskMetricReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loans = load_loan_data("data/financial_loan.csv")

    def test_portfolio_baseline(self) -> None:
        kpis = portfolio_kpis(self.loans)
        self.assertEqual(int(kpis["total_applications"]), 38_576)
        self.assertEqual(int(kpis["funded_exposure"]), 435_757_075)
        self.assertEqual(int(kpis["total_amount_collected"]), 473_070_933)
        self.assertEqual(int(kpis["resolved_loans"]), 37_478)
        self.assertEqual(int(kpis["charged_off_loans"]), 5_333)
        self.assertEqual(int(kpis["current_loans"]), 1_098)
        self.assertAlmostEqual(kpis["matured_default_rate"], 0.1422968141, places=9)
        self.assertAlmostEqual(kpis["current_loan_share"], 0.0284632932, places=9)
        self.assertAlmostEqual(kpis["cash_collection_ratio"], 1.0856299533, places=9)

    def test_grade_f_reconciliation(self) -> None:
        grade_f = segment_summary(self.loans, "grade").set_index("grade").loc["F"]
        self.assertEqual(int(grade_f["loan_count"]), 1_028)
        self.assertEqual(int(grade_f["resolved_loans"]), 957)
        self.assertEqual(int(grade_f["charged_off_loans"]), 311)
        self.assertEqual(int(grade_f["funded_exposure"]), 18_910_450)
        self.assertAlmostEqual(grade_f["matured_default_rate"], 0.324973877, places=9)

    def test_debt_consolidation_60_month_segment(self) -> None:
        segment = (
            segment_summary(self.loans, ["purpose", "term"])
            .set_index(["purpose", "term"])
            .loc[("Debt consolidation", "60 months")]
        )
        self.assertEqual(int(segment["loan_count"]), 5_391)
        self.assertEqual(int(segment["resolved_loans"]), 4_824)
        self.assertEqual(int(segment["funded_exposure"]), 92_775_900)
        self.assertAlmostEqual(segment["matured_default_rate"], 0.261194030, places=9)

    def test_latest_complete_month_excludes_partial_december(self) -> None:
        self.assertEqual(str(latest_complete_issue_month(self.loans)), "2021-11")
        comparison = complete_month_comparison(self.loans)
        self.assertEqual(comparison["issue_month"].tolist(), ["2021-10", "2021-11"])
        self.assertEqual(comparison["total_applications"].tolist(), [3_796, 4_035])

    def test_temporal_anomalies_are_explicit(self) -> None:
        profile = temporal_consistency_profile(
            self.loans.assign(
                issue_date=self.loans["issue_date"].dt.strftime("%d-%m-%Y")
            )
        ).set_index("rule")
        self.assertEqual(int(profile.loc["last_payment_before_issue", "affected_rows"]), 15_453)
        self.assertEqual(int(profile.loc["last_credit_pull_before_issue", "affected_rows"]), 20_182)
        self.assertEqual(int(profile.loc["resolved_with_next_payment_date", "affected_rows"]), 37_478)

    def test_term_is_normalized_for_cross_tool_grouping(self) -> None:
        self.assertEqual(sorted(self.loans["term"].unique().tolist()), ["36 months", "60 months"])


if __name__ == "__main__":
    unittest.main()
