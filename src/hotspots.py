from typing import Any, Dict, List


def safe_div(numerator: float, denominator: float):
    """Safely divide two numbers."""
    if denominator is None or denominator == 0:
        return None

    return float(numerator) / float(denominator)


def source_emissions_kg(data: Dict[str, Any], calculator) -> Dict[str, float]:
    """
    Calculate emissions contribution from individual sources.

    Sources:
    - Electricity
    - Fuel
    - Transport
    - Employee Commute
    - Supply Chain
    """

    electricity = (
        float(data.get("electricity_kwh_monthly", 0.0))
        * float(calculator.EMISSION_FACTORS.get("electricity", 0.82))
    )

    fuel_type = data.get("fuel_type", "Diesel")

    fuel_factor = calculator.EMISSION_FACTORS.get(
        fuel_type,
        calculator.EMISSION_FACTORS.get("Diesel", 2.68),
    )

    fuel = (
        float(data.get("fuel_liters_monthly", 0.0))
        * float(fuel_factor)
    )

    transport = (
        float(data.get("transport_km_monthly", 0.0))
        * float(calculator.EMISSION_FACTORS.get("transport", 0.21))
    )

    employees = float(data.get("num_employees", 0.0))

    commute_trips = employees * 22.0 * 10.0 * 2.0

    commute = (
        commute_trips
        * float(calculator.EMISSION_FACTORS.get("employee_commute", 0.12))
    )

    production = (
        float(data.get("production_units_monthly", 0.0))
        * float(calculator.EMISSION_FACTORS.get("supply_chain", 0.15))
    )

    return {
        "Electricity": electricity,
        "Fuel": fuel,
        "Transport": transport,
        "Employee Commute": commute,
        "Supply Chain": production,
    }


def _scope_for_source(source: str) -> str:
    """Return GHG scope for an emission source."""

    if source == "Electricity":
        return "Scope 2"

    if source == "Fuel":
        return "Scope 1"

    return "Scope 3"


def _normalize_sources(
    sources: Dict[str, float] | List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Normalize source data into the format used by the UI.

    Supports both:
        {"Electricity": 82000, ...}

    and:
        [
            {"source": "Electricity", "kg": 82000, ...}
        ]
    """

    if isinstance(sources, dict):
        items = [
            {
                "source": key,
                "kg": float(value),
            }
            for key, value in sources.items()
        ]
    else:
        items = []

        for row in sources:
            source = row.get("source", "Unknown")

            kg = row.get("kg")

            if kg is None:
                kg = row.get("emissions_kg", 0.0)

            items.append(
                {
                    **row,
                    "source": source,
                    "kg": float(kg),
                }
            )

    total = sum(row["kg"] for row in items)

    normalized = []

    for row in items:
        kg = float(row["kg"])

        pct = (
            kg / total * 100.0
            if total > 0
            else 0.0
        )

        normalized.append(
            {
                **row,
                "source": row["source"],
                "kg": kg,
                "tons": kg / 1000.0,
                "emissions_kg": kg,
                "pct": pct,
                "scope": row.get(
                    "scope",
                    _scope_for_source(row["source"]),
                ),
            }
        )

    normalized.sort(
        key=lambda x: x["kg"],
        reverse=True,
    )

    for index, row in enumerate(normalized, start=1):
        row["rank"] = index

    return normalized


def ranked_hotspots(
    data: Dict[str, Any],
    calculator,
) -> List[Dict[str, Any]]:
    """
    Return emission sources ranked from highest to lowest.
    """

    sources = source_emissions_kg(data, calculator)

    return _normalize_sources(sources)


def top_hotspots(
    data_or_sources,
    calculator_or_limit=None,
    limit=3,
) -> List[Dict[str, Any]]:
    """
    Return top emission hotspots.

    Supports:
        top_hotspots(data, calculator, 3)

    and:

        top_hotspots(sources, 3)
    """

    # Case 1:
    # top_hotspots(raw_data, calculator, limit)
    if isinstance(data_or_sources, dict) and (
        "electricity_kwh_monthly" in data_or_sources
        or "fuel_liters_monthly" in data_or_sources
    ):
        data = data_or_sources
        calculator = calculator_or_limit

        rows = ranked_hotspots(data, calculator)

        return rows[:limit]

    # Case 2:
    # top_hotspots(already_ranked_sources, 3)
    sources = data_or_sources

    if isinstance(calculator_or_limit, int):
        limit = calculator_or_limit

    rows = _normalize_sources(sources)

    return rows[:limit]


def hotspot_insight(sources) -> str:
    """
    Generate a simple insight about the largest emission source.
    """

    rows = _normalize_sources(sources)

    if not rows:
        return "No emission hotspots were identified."

    top = rows[0]

    source = top["source"]
    pct = top["pct"]
    tons = top["tons"]

    if pct <= 0:
        return "No measurable emission hotspot is present in the current activity data."

    return (
        f"{source} is the largest emission source at "
        f"{tons:,.2f} tCO2e/month, representing "
        f"{pct:.1f}% of total estimated emissions."
    )


def carbon_intensity(
    total_emissions_kg,
    num_employees=None,
    production_units=None,
):
    """
    Calculate carbon intensity.

    Returns:
        {
            "per_employee_kg": ...,
            "per_unit_kg": ...
        }

    If denominator is zero, the corresponding value is None.
    """

    per_employee = None
    per_unit = None

    if num_employees is not None and num_employees > 0:
        per_employee = (
            float(total_emissions_kg)
            / float(num_employees)
        )

    if production_units is not None and production_units > 0:
        per_unit = (
            float(total_emissions_kg)
            / float(production_units)
        )

    return {
        "per_employee_kg": per_employee,
        "per_unit_kg": per_unit,
    }


def accounting_table(
    data: Dict[str, Any],
    calculator,
) -> List[Dict[str, Any]]:
    """
    Build an accounting table for the major emission activities.
    """

    fuel_type = data.get("fuel_type", "Diesel")

    fuel_factor = calculator.EMISSION_FACTORS.get(
        fuel_type,
        calculator.EMISSION_FACTORS.get("Diesel", 2.68),
    )

    rows = [
        {
            "Activity": "Purchased Electricity",
            "Quantity": float(
                data.get(
                    "electricity_kwh_monthly",
                    0.0,
                )
            ),
            "Unit": "kWh/month",
            "Emission Factor": float(
                calculator.EMISSION_FACTORS.get(
                    "electricity",
                    0.82,
                )
            ),
            "Emissions (kg)": float(
                data.get(
                    "electricity_kwh_monthly",
                    0.0,
                )
            )
            * float(
                calculator.EMISSION_FACTORS.get(
                    "electricity",
                    0.82,
                )
            ),
            "Scope": "Scope 2",
        },
        {
            "Activity": f"{fuel_type} Consumption",
            "Quantity": float(
                data.get(
                    "fuel_liters_monthly",
                    0.0,
                )
            ),
            "Unit": "L/month",
            "Emission Factor": float(fuel_factor),
            "Emissions (kg)": float(
                data.get(
                    "fuel_liters_monthly",
                    0.0,
                )
            )
            * float(fuel_factor),
            "Scope": "Scope 1",
        },
        {
            "Activity": "Business Transport",
            "Quantity": float(
                data.get(
                    "transport_km_monthly",
                    0.0,
                )
            ),
            "Unit": "km/month",
            "Emission Factor": float(
                calculator.EMISSION_FACTORS.get(
                    "transport",
                    0.21,
                )
            ),
            "Emissions (kg)": float(
                data.get(
                    "transport_km_monthly",
                    0.0,
                )
            )
            * float(
                calculator.EMISSION_FACTORS.get(
                    "transport",
                    0.21,
                )
            ),
            "Scope": "Scope 3",
        },
        {
            "Activity": "Employee Commute",
            "Quantity": float(
                data.get(
                    "num_employees",
                    0.0,
                )
            ),
            "Unit": "employees",
            "Emission Factor": float(
                calculator.EMISSION_FACTORS.get(
                    "employee_commute",
                    0.12,
                )
            ),
            "Emissions (kg)": (
                float(
                    data.get(
                        "num_employees",
                        0.0,
                    )
                )
                * 22.0
                * 10.0
                * 2.0
                * float(
                    calculator.EMISSION_FACTORS.get(
                        "employee_commute",
                        0.12,
                    )
                )
            ),
            "Scope": "Scope 3",
        },
        {
            "Activity": "Supply Chain / Production",
            "Quantity": float(
                data.get(
                    "production_units_monthly",
                    0.0,
                )
            ),
            "Unit": "units/month",
            "Emission Factor": float(
                calculator.EMISSION_FACTORS.get(
                    "supply_chain",
                    0.15,
                )
            ),
            "Emissions (kg)": float(
                data.get(
                    "production_units_monthly",
                    0.0,
                )
            )
            * float(
                calculator.EMISSION_FACTORS.get(
                    "supply_chain",
                    0.15,
                )
            ),
            "Scope": "Scope 3",
        },
    ]

    return rows


def build_insights(*args):
    """
    Build dashboard insights.

    Supports both the compact API:
        build_insights(data, calculator)

    and the UI API:
        build_insights(sources, emissions, breakdown, intensity, ml)
    """

    if len(args) == 2:
        data, calculator = args

        sources = ranked_hotspots(
            data,
            calculator,
        )

        total = sum(
            row["kg"]
            for row in sources
        )

        insights = []

        if sources:
            insights.append(
                hotspot_insight(sources)
            )

        if total > 0:
            insights.append(
                f"Total estimated emissions are "
                f"{total / 1000.0:,.2f} tCO2e/month."
            )

        return insights

    if len(args) >= 5:
        sources = args[0]
        emissions = args[1]
        breakdown = args[2]
        intensity = args[3]
        ml = args[4]

        rows = _normalize_sources(sources)

        insights = []

        if rows:
            insights.append(
                hotspot_insight(rows)
            )

        total = 0.0

        if isinstance(emissions, dict):
            total = float(
                emissions.get(
                    "total_kg",
                    emissions.get("total", 0.0),
                )
            )
        elif isinstance(emissions, (int, float)):
            total = float(emissions)

        if total > 0:
            insights.append(
                f"Current estimated emissions are "
                f"{total / 1000.0:,.2f} tCO2e/month."
            )

        if isinstance(intensity, dict):
            per_unit = intensity.get(
                "per_unit_kg"
            )

            if per_unit is not None:
                insights.append(
                    f"Carbon intensity is "
                    f"{per_unit:.2f} kgCO2e per production unit."
                )

        if isinstance(ml, dict):
            prediction = ml.get(
                "prediction_kg"
            )

            if prediction is not None:
                insights.append(
                    f"The ML estimate for the current month is "
                    f"{float(prediction) / 1000.0:,.2f} tCO2e."
                )

        return insights

    return []