"""ResistAI MVP smoke tests — no API key required."""

from __future__ import annotations

import os
import unittest

from data import get_country_baseline, get_country_metadata, list_supported_countries
from simulation import (
    RecoveryInputs,
    SimulationInputs,
    compare_scenarios,
    run_recovery_comparison,
)


class TestCountryData(unittest.TestCase):
    def test_all_seven_countries_load_baselines(self) -> None:
        expected = ["Global", "USA", "India", "Brazil", "Peru", "Nigeria", "UK"]
        self.assertEqual(list_supported_countries(), expected)

        for country in expected:
            baseline = get_country_baseline(country)
            self.assertEqual(baseline["country"], country)
            self.assertGreater(baseline["baseline_deaths"], 0)
            self.assertGreater(baseline["rbi_0"], 0)
            self.assertGreater(baseline["gdp_per_capita"], 0)
            self.assertGreater(baseline["cost_per_death"], 0)

    def test_country_metadata_available(self) -> None:
        for country in list_supported_countries():
            meta = get_country_metadata(country)
            self.assertEqual(meta["country"], country)
            self.assertIn("data_vintage", meta)


class TestSimulation(unittest.TestCase):
    def test_compare_scenarios_all_countries(self) -> None:
        for country in list_supported_countries():
            result = compare_scenarios(
                SimulationInputs(
                    country=country,
                    delay_years=5,
                    funding_level="Medium",
                    stewardship_rate=50.0,
                    rd_investment="Medium",
                )
            )
            self.assertGreater(result.delayed.summary["additional_deaths_from_delay"], 0)
            self.assertIn(
                result.delayed.summary["risk_level"],
                {"Low", "Medium", "High", "Critical"},
            )

    def test_recovery_comparison(self) -> None:
        recovery = run_recovery_comparison(
            RecoveryInputs(
                country="Peru",
                prior_delay_years=5,
                funding_level="High",
                stewardship_rate=75.0,
                rd_investment="High",
                projection_years=10,
            )
        )
        self.assertGreater(recovery.comparison_summary["lives_saved_by_recovery"], 0)
        self.assertIn("damage_at_delay_end", recovery.comparison_summary)


class TestAIDemoFallback(unittest.TestCase):
    def test_demo_recommendation_without_api_key(self) -> None:
        os.environ.pop("ANTHROPIC_API_KEY", None)
        from ai.recommendation_engine import generate_recommendation

        text, source = generate_recommendation(
            country="Peru",
            delay_years=5,
            funding_level="Medium",
            stewardship_rate=50.0,
            rd_investment="Medium",
            deaths=12_000,
            healthcare_cost=120.5,
            gdp_loss=900.0,
            risk_level="High",
            intervention_strength=0.55,
            lives_saved_vs_no_action=50_000,
            critical_year=2032,
        )
        self.assertEqual(source, "demo")
        self.assertIn("SITUATION SUMMARY", text)
        self.assertGreater(len(text), 500)


class TestReportExport(unittest.TestCase):
    def test_html_report_is_self_contained(self) -> None:
        from report_export import build_downloadable_html_report

        inputs = SimulationInputs(
            country="Peru",
            delay_years=5,
            funding_level="Medium",
            stewardship_rate=50.0,
            rd_investment="Medium",
        )
        comparison = compare_scenarios(inputs)
        recovery = run_recovery_comparison(
            RecoveryInputs(
                country="Peru",
                prior_delay_years=5,
                funding_level="High",
                stewardship_rate=75.0,
                rd_investment="High",
            )
        )
        from ai.demo_recommendation import generate_demo_recommendation

        ai_text = generate_demo_recommendation(
            country="Peru",
            delay_years=5,
            funding_level="Medium",
            stewardship_rate=50.0,
            rd_investment="Medium",
            additional_deaths=comparison.delayed.summary["additional_deaths_from_delay"],
            healthcare_cost=comparison.delayed.summary["healthcare_cost_increase_usd_m"],
            gdp_loss=comparison.delayed.summary["gdp_loss_usd_m"],
            risk_level=comparison.delayed.summary["risk_level"],
            intervention_strength=comparison.delayed.summary["intervention_strength"],
            lives_saved_vs_no_action=comparison.early.summary["lives_saved_vs_no_action"],
            critical_year=comparison.delayed.summary["critical_year"],
        )
        html = build_downloadable_html_report(
            inputs=inputs,
            comparison=comparison,
            ai_text=ai_text,
            ai_source="demo",
            recovery=recovery,
            recovery_settings={
                "funding_level": "High",
                "stewardship_rate": 75.0,
                "rd_investment": "High",
                "projection_years": 10,
            },
            effective_prior_delay=5,
        )
        self.assertTrue(html.startswith("<!DOCTYPE html>"))
        self.assertIn("<style>", html)
        self.assertIn("Scenario Comparison", html)
        self.assertIn("Disclaimer", html)


if __name__ == "__main__":
    unittest.main()
