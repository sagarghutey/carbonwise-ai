"""Lightweight tests for the pure calculation logic (standard library unittest).Run from the repository root:  python -m unittest discover -s tests -v"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from emissions import EmissionsCalculator  # noqa: E402
from hotspots import carbon_intensity, ranked_hotspots, source_emissions_kg  # noqa: E402
from net_zero import build_projection, summarize_pathway  # noqa: E402
from scenarios import apply_levers, build_scenarios, clamp_levers, rule_based_forecast  # noqa: E402
from smart_recommendations import build_smart_recommendations  # noqa: E402
from validation import validate_inputs  # noqa: E402

SAMPLE = {
    "industry": "Manufacturing",
    "electricity_kwh_monthly": 100000.0,
    "fuel_liters_monthly": 5000.0,
    "fuel_type": "Diesel",
    "transport_km_monthly": 15000.0,
    "num_employees": 250,
    "production_units_monthly": 20000.0,
}

ZERO = dict(
    SAMPLE,
    electricity_kwh_monthly=0.0,
    fuel_liters_monthly=0.0,
    transport_km_monthly=0.0,
    num_employees=1,
    production_units_monthly=0.0,
)


class EmissionsTests(unittest.TestCase):
    def setUp(self):
        self.calc = EmissionsCalculator()

    def test_original_totals_unchanged(self):
        em = self.calc.calculate_total_emissions(SAMPLE)
        self.assertAlmostEqual(em["scope1_kg"], 13400.0)
        self.assertAlmostEqual(em["scope2_kg"], 82000.0)
        self.assertAlmostEqual(em["scope3_kg"], 3150.0 + 13200.0 + 3000.0)
        self.assertAlmostEqual(em["total_kg"], 114750.0)

    def test_sources_sum_to_total(self):
        total = self.calc.calculate_total_emissions(SAMPLE)["total_kg"]
        self.assertAlmostEqual(sum(source_emissions_kg(SAMPLE, self.calc).values()), total)

    def test_hotspots_ranked_and_percent(self):
        rows = ranked_hotspots(SAMPLE, self.calc)
        self.assertEqual(rows[0]["source"], "Electricity")
        self.assertAlmostEqual(sum(r["pct"] for r in rows), 100.0)

    def test_zero_inputs_do_not_crash(self):
        rows = ranked_hotspots(ZERO, self.calc)
        self.assertAlmostEqual(sum(r["pct"] for r in rows), 100.0)
        scenarios = build_scenarios(ZERO, {"electricity": 50}, self.calc, None)
        self.assertEqual(len(scenarios), 4)
        self.assertEqual(len(rule_based_forecast(self.calc, ZERO)), 12)

    def test_intensity_handles_zero_denominators(self):
        result = carbon_intensity(1000.0, 0, 0)
        self.assertIsNone(result["per_employee_kg"])
        self.assertIsNone(result["per_unit_kg"])
        result = carbon_intensity(1000.0, 10, 50)
        self.assertAlmostEqual(result["per_employee_kg"], 100.0)
        self.assertAlmostEqual(result["per_unit_kg"], 20.0)


class ScenarioTests(unittest.TestCase):
    def setUp(self):
        self.calc = EmissionsCalculator()

    def test_apply_levers_keeps_baseline(self):
        reduced = apply_levers(SAMPLE, {"electricity": 100})
        self.assertEqual(reduced["electricity_kwh_monthly"], 0.0)
        self.assertEqual(SAMPLE["electricity_kwh_monthly"], 100000.0)

    def test_levers_are_clamped(self):
        levers = clamp_levers(
            {"electricity": 500, "fuel": -5, "transport": 80, "production": 99}
        )
        self.assertEqual(levers["electricity"], 100.0)
        self.assertEqual(levers["fuel"], 0.0)
        self.assertEqual(levers["transport"], 50.0)
        self.assertEqual(levers["production"], 30.0)

    def test_scenario_reduction(self):
        scenarios = build_scenarios(
            SAMPLE, {"electricity": 100}, self.calc, None
        )
        self.assertEqual(scenarios[0]["reduction_kg"], 0)
        custom = scenarios[-1]
        self.assertAlmostEqual(custom["reduction_kg"], 82000.0)
        self.assertAlmostEqual(
            custom["reduction_pct"], 82000.0 / 114750.0 * 100
        )
        moderate = scenarios[1]
        self.assertGreater(moderate["reduction_kg"], 0)
        self.assertLess(moderate["reduction_kg"], scenarios[2]["reduction_kg"])


class NetZeroTests(unittest.TestCase):
    def test_linear_pathway(self):
        rows = build_projection(
            120000.0, 2026, 2030, annual_growth_pct=0.0
        )
        summary = summarize_pathway(rows, 120000.0, 2026, 2030)
        self.assertEqual(summary["years_remaining"], 4)
        self.assertAlmostEqual(summary["required_annual_reduction_kg"], 30000.0)
        self.assertAlmostEqual(rows[2]["pathway_kg"], 60000.0)
        self.assertAlmostEqual(summary["pathway_at_target_kg"], 0.0)
        self.assertAlmostEqual(summary["gap_kg"], 120000.0)
        self.assertTrue(summary["gap_open"])

    def test_zero_baseline(self):
        rows = build_projection(0.0, 2026, 2040)
        summary = summarize_pathway(rows, 0.0, 2026, 2040)
        self.assertEqual(summary["gap_kg"], 0.0)
        self.assertEqual(summary["required_annual_reduction_pct"], 0.0)

    def test_residual_allowance(self):
        rows = build_projection(100000.0, 2026, 2036, residual_pct=10)
        self.assertAlmostEqual(rows[-1]["pathway_kg"], 10000.0)


class ValidationAndRecommendationTests(unittest.TestCase):
    def test_validation_rejects_negative(self):
        raw = dict(SAMPLE, electricity_kwh_monthly=-1)
        clean, errors, _ = validate_inputs(raw)
        self.assertIsNone(clean)
        self.assertTrue(errors)

    def test_validation_accepts_sample(self):
        clean, errors, _ = validate_inputs(SAMPLE)
        self.assertEqual(errors, [])
        self.assertEqual(clean["num_employees"], 250)

    def test_validation_warns_on_zero_activity(self):
        _, errors, warnings = validate_inputs(ZERO)
        self.assertEqual(errors, [])
        self.assertTrue(warnings)

    def test_recommendations_enriched(self):
        calc = EmissionsCalculator()
        breakdown = calc.get_breakdown_percentage(
            calc.calculate_total_emissions(SAMPLE)
        )
        recs = build_smart_recommendations(
            SAMPLE, breakdown, source_emissions_kg(SAMPLE, calc)
        )
        self.assertTrue(recs)
        for rec in recs:
            for key in (
                "why",
                "estimate_text",
                "lever_text",
                "priority",
                "timeframe",
                "investment",
            ):
                self.assertIn(key, rec)
        self.assertEqual(recs[0]["priority"], "High")
        self.assertEqual(recs[-1]["action"], "Track emissions monthly")


if __name__ == "__main__":
    unittest.main()