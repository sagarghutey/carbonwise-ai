from __future__ import annotations

from typing import Any, Dict

import pandas as pd


DISCLAIMER = (
    "CarbonWise AI provides planning estimates based on the project's "
    "configured emission factors and assumptions. Results are not a "
    "verified corporate GHG inventory, audit, certification, or assurance."
)


def build_legacy_summary_df(
    data: Dict[str, Any],
    emissions: Dict[str, Any] | None = None,
) -> pd.DataFrame:
    """
    Build a compact summary table compatible with the original project.
    """

    emissions = emissions or {}

    rows = []

    for key, value in emissions.items():
        if isinstance(value, (int, float)):
            rows.append(
                {
                    "Metric": str(key),
                    "Value": float(value),
                }
            )

    if not rows:
        rows = [
            {
                "Metric": "Industry",
                "Value": data.get(
                    "industry",
                    "",
                ),
            },
            {
                "Metric": "Electricity (kWh/month)",
                "Value": data.get(
                    "electricity_kwh_monthly",
                    0.0,
                ),
            },
            {
                "Metric": "Fuel (L/month)",
                "Value": data.get(
                    "fuel_liters_monthly",
                    0.0,
                ),
            },
            {
                "Metric": "Transport (km/month)",
                "Value": data.get(
                    "transport_km_monthly",
                    0.0,
                ),
            },
            {
                "Metric": "Employees",
                "Value": data.get(
                    "num_employees",
                    0,
                ),
            },
            {
                "Metric": "Production (units/month)",
                "Value": data.get(
                    "production_units_monthly",
                    0.0,
                ),
            },
        ]

    return pd.DataFrame(rows)


def build_report_df(
    data: Dict[str, Any],
    sources_kg: Dict[str, float] | None = None,
    scenarios: list[Dict[str, Any]] | None = None,
) -> pd.DataFrame:
    """
    Build a flat CSV-ready report containing inputs, source emissions,
    and scenario results.
    """

    sources_kg = sources_kg or {}
    scenarios = scenarios or []

    rows = []

    # Input information.
    rows.extend(
        [
            {
                "Section": "Inputs",
                "Metric": "Industry",
                "Value": data.get("industry", ""),
                "Unit": "",
            },
            {
                "Section": "Inputs",
                "Metric": "Electricity",
                "Value": data.get(
                    "electricity_kwh_monthly",
                    0.0,
                ),
                "Unit": "kWh/month",
            },
            {
                "Section": "Inputs",
                "Metric": "Fuel",
                "Value": data.get(
                    "fuel_liters_monthly",
                    0.0,
                ),
                "Unit": "L/month",
            },
            {
                "Section": "Inputs",
                "Metric": "Fuel Type",
                "Value": data.get(
                    "fuel_type",
                    "",
                ),
                "Unit": "",
            },
            {
                "Section": "Inputs",
                "Metric": "Transport",
                "Value": data.get(
                    "transport_km_monthly",
                    0.0,
                ),
                "Unit": "km/month",
            },
            {
                "Section": "Inputs",
                "Metric": "Employees",
                "Value": data.get(
                    "num_employees",
                    0,
                ),
                "Unit": "employees",
            },
            {
                "Section": "Inputs",
                "Metric": "Production",
                "Value": data.get(
                    "production_units_monthly",
                    0.0,
                ),
                "Unit": "units/month",
            },
        ]
    )

    # Source-level emissions.
    for source, emissions in sources_kg.items():
        rows.append(
            {
                "Section": "Emissions",
                "Metric": source,
                "Value": float(emissions),
                "Unit": "kg CO2e/month",
            }
        )

    # Total emissions.
    total = sum(
        float(value)
        for value in sources_kg.values()
    )

    rows.append(
        {
            "Section": "Emissions",
            "Metric": "Total",
            "Value": total,
            "Unit": "kg CO2e/month",
        }
    )

    # Scenario results.
    for scenario in scenarios:
        rows.append(
            {
                "Section": "Scenario",
                "Metric": scenario.get(
                    "name",
                    "Scenario",
                ),
                "Value": float(
                    scenario.get(
                        "emissions_kg",
                        0.0,
                    )
                ),
                "Unit": "kg CO2e/month",
            }
        )

        rows.append(
            {
                "Section": "Scenario",
                "Metric": (
                    f"{scenario.get('name', 'Scenario')} "
                    "reduction"
                ),
                "Value": float(
                    scenario.get(
                        "reduction_pct",
                        0.0,
                    )
                ),
                "Unit": "%",
            }
        )

    df = pd.DataFrame(rows)

    return df


def report_csv_bytes(
    report_df: pd.DataFrame,
) -> bytes:
    """Convert a report DataFrame into downloadable CSV bytes."""

    return report_df.to_csv(
        index=False
    ).encode("utf-8")