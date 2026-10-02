from __future__ import annotations

from datetime import date
from typing import Any, Dict, List


TARGET_YEARS = (2030, 2040, 2050)


def safe_div(numerator: float, denominator: float) -> float:
    """Safe division helper."""
    if denominator == 0:
        return 0.0
    return numerator / denominator


def current_year() -> int:
    """Return the current calendar year."""
    return date.today().year


def years_remaining(
    base_year: int,
    target_year: int,
) -> int:
    """Return the number of years between the base and target year."""
    return max(0, int(target_year) - int(base_year))


def build_projection(
    baseline_annual: float,
    base_year: int,
    target_year: int,
    annual_growth_pct: float = 0.0,
    residual_pct: float = 0.0,
    scenario_reduction_pct: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    Build a year-by-year net-zero pathway.

    baseline_annual:
        Current annual emissions in kg CO2e.

    annual_growth_pct:
        Assumed annual growth in baseline emissions.

    residual_pct:
        Percentage of baseline emissions allowed to remain at
        the target year.

    scenario_reduction_pct:
        Additional reduction applied to the forecast scenario.
    """

    base_year = int(base_year)
    target_year = int(target_year)

    if target_year < base_year:
        target_year = base_year

    baseline_annual = max(0.0, float(baseline_annual))
    annual_growth_pct = max(0.0, float(annual_growth_pct))
    residual_pct = min(100.0, max(0.0, float(residual_pct)))
    scenario_reduction_pct = min(
        100.0,
        max(0.0, float(scenario_reduction_pct)),
    )

    years = target_year - base_year

    target_pathway = (
        baseline_annual * residual_pct / 100.0
    )

    rows: List[Dict[str, Any]] = []

    for year in range(base_year, target_year + 1):
        elapsed = year - base_year

        forecast = (
            baseline_annual
            * (1.0 + annual_growth_pct / 100.0) ** elapsed
        )

        if years <= 0:
            pathway = target_pathway
        else:
            progress = elapsed / years

            pathway = (
                baseline_annual
                + (target_pathway - baseline_annual)
                * progress
            )

        scenario = forecast * (
            1.0 - scenario_reduction_pct / 100.0
        )

        gap = max(0.0, scenario - pathway)

        rows.append(
            {
                "year": year,
                "forecast_kg": forecast,
                "pathway_kg": pathway,
                "scenario_kg": scenario,
                "gap_kg": gap,
            }
        )

    return rows


def summarize_pathway(
    projection: List[Dict[str, Any]],
    baseline_annual: float,
    base_year: int,
    target_year: int,
    residual_pct: float = 0.0,
    scenario_reduction_pct: float = 0.0,
) -> Dict[str, Any]:
    """
    Summarize the net-zero pathway and remaining gap.
    """

    baseline_annual = max(0.0, float(baseline_annual))

    base_year = int(base_year)
    target_year = int(target_year)

    years = years_remaining(
        base_year,
        target_year,
    )

    target_pathway = (
        baseline_annual
        * min(100.0, max(0.0, float(residual_pct)))
        / 100.0
    )

    if projection:
        target_row = projection[-1]

        forecast_at_target = float(
            target_row.get("forecast_kg", 0.0)
        )

        pathway_at_target = float(
            target_row.get("pathway_kg", target_pathway)
        )

        scenario_at_target = float(
            target_row.get(
                "scenario_kg",
                forecast_at_target
                * (
                    1.0
                    - float(scenario_reduction_pct) / 100.0
                ),
            )
        )
    else:
        forecast_at_target = baseline_annual
        pathway_at_target = target_pathway
        scenario_at_target = (
            forecast_at_target
            * (
                1.0
                - float(scenario_reduction_pct) / 100.0
            )
        )

    total_reduction_required = max(
        0.0,
        baseline_annual - target_pathway,
    )

    if years > 0:
        required_annual_reduction_kg = (
            total_reduction_required / years
        )
    else:
        required_annual_reduction_kg = (
            total_reduction_required
        )

    required_annual_reduction_pct = safe_div(
        required_annual_reduction_kg * 100.0,
        baseline_annual,
    )

    gap_kg = max(
        0.0,
        forecast_at_target - pathway_at_target,
    )

    scenario_gap_kg = max(
        0.0,
        scenario_at_target - pathway_at_target,
    )

    reduction_needed_pct_of_forecast = safe_div(
        gap_kg * 100.0,
        forecast_at_target,
    )

    return {
        "baseline_kg": baseline_annual,
        "base_year": base_year,
        "target_year": target_year,
        "years_remaining": years,
        "required_annual_reduction_kg": required_annual_reduction_kg,
        "required_annual_reduction_pct": required_annual_reduction_pct,
        "forecast_at_target_kg": forecast_at_target,
        "pathway_at_target_kg": pathway_at_target,
        "gap_kg": gap_kg,
        "gap_open": gap_kg > 0,
        "reduction_needed_pct_of_forecast": reduction_needed_pct_of_forecast,
        "scenario_gap_kg": scenario_gap_kg,
        "scenario_reduction_pct": float(
            scenario_reduction_pct
        ),
    }