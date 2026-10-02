from copy import deepcopy


# ============================================================
# Scenario configuration
# ============================================================

LEVER_ORDER = (
    "electricity",
    "fuel",
    "transport",
    "production",
)

LEVER_MAX = {
    "electricity": 100.0,
    "fuel": 50.0,
    "transport": 50.0,
    "production": 30.0,
}

PRESETS = {
    "Baseline": {
        "electricity": 0.0,
        "fuel": 0.0,
        "transport": 0.0,
        "production": 0.0,
    },
    "Moderate": {
        "electricity": 15.0,
        "fuel": 10.0,
        "transport": 10.0,
        "production": 5.0,
    },
    "Aggressive": {
        "electricity": 35.0,
        "fuel": 30.0,
        "transport": 25.0,
        "production": 15.0,
    },
}


# ============================================================
# Utility functions
# ============================================================

def clamp_levers(levers):
    """
    Keep all reduction levers inside their allowed ranges.
    """

    if not isinstance(levers, dict):
        levers = {}

    cleaned = {}

    for lever in LEVER_ORDER:
        try:
            value = float(levers.get(lever, 0.0))
        except (TypeError, ValueError):
            value = 0.0

        value = max(
            0.0,
            min(value, LEVER_MAX[lever])
        )

        cleaned[lever] = value

    return cleaned


def apply_levers(data, levers):
    """
    Apply reduction levers to activity data.

    Does not modify the original input dictionary.
    """

    result = deepcopy(data)
    levers = clamp_levers(levers)

    result["electricity_kwh_monthly"] = (
        float(
            result.get(
                "electricity_kwh_monthly",
                0.0
            )
        )
        * (
            1.0
            - levers["electricity"] / 100.0
        )
    )

    result["fuel_liters_monthly"] = (
        float(
            result.get(
                "fuel_liters_monthly",
                0.0
            )
        )
        * (
            1.0
            - levers["fuel"] / 100.0
        )
    )

    result["transport_km_monthly"] = (
        float(
            result.get(
                "transport_km_monthly",
                0.0
            )
        )
        * (
            1.0
            - levers["transport"] / 100.0
        )
    )

    result["production_units_monthly"] = (
        float(
            result.get(
                "production_units_monthly",
                0.0
            )
        )
        * (
            1.0
            - levers["production"] / 100.0
        )
    )

    return result


def key_actions(levers):
    """
    Convert reduction levers into readable actions.
    """

    levers = clamp_levers(levers)

    actions = []

    if levers["electricity"] > 0:
        actions.append(
            f"Reduce electricity demand by "
            f"{levers['electricity']:.0f}%"
        )

    if levers["fuel"] > 0:
        actions.append(
            f"Reduce fuel consumption by "
            f"{levers['fuel']:.0f}%"
        )

    if levers["transport"] > 0:
        actions.append(
            f"Reduce transport emissions by "
            f"{levers['transport']:.0f}%"
        )

    if levers["production"] > 0:
        actions.append(
            f"Improve production efficiency by "
            f"{levers['production']:.0f}%"
        )

    if not actions:
        actions.append(
            "No reduction levers applied."
        )

    return actions


def _extract_total(result):
    """
    Extract total emissions from the original calculator result.
    """

    if isinstance(result, dict):

        if "total_kg" in result:
            return float(
                result["total_kg"]
            )

        if "total" in result:
            return float(
                result["total"]
            )

    return float(result)


# ============================================================
# ML prediction helpers
# ============================================================

def safe_ml_predict(predictor, data):
    """
    Safely run the existing EmissionsPredictor.

    Returns:
        (prediction_kg, error_message)
    """

    if predictor is None:
        return (
            None,
            "ML predictor is unavailable."
        )

    try:
        prediction = predictor.predict_emissions(
            data
        )

        return (
            float(prediction),
            None
        )

    except Exception as exc:
        return (
            None,
            str(exc)
        )


def safe_ml_forecast(
    predictor,
    data,
    months=12,
    growth_rate=0.0,
):
    """
    Safely run the existing ML future forecast.
    """

    if predictor is None:
        return (
            [],
            "ML predictor is unavailable."
        )

    try:
        rows = predictor.predict_future_months(
            data,
            months=months,
            growth_rate=growth_rate,
        )

        normalized = []

        for index, row in enumerate(
            rows,
            start=1
        ):

            if isinstance(row, dict):

                month = row.get(
                    "month",
                    f"Month {index}"
                )

                value = row.get(
                    "prediction_kg",
                    row.get(
                        "predicted_kg",
                        row.get(
                            "predicted_emissions_kg",
                            row.get(
                                "emissions_kg",
                                row.get(
                                    "kg",
                                    0.0
                                )
                            )
                        )
                    )
                )

            else:

                month = (
                    f"Month {index}"
                )

                value = row

            value = float(value)

            normalized.append(
                {
                    "month": month,
                    "prediction_kg": value,
                    "predicted_kg": value,
                    "predicted_emissions_kg": value,
                    "emissions_kg": value,
                }
            )

        return (
            normalized,
            None
        )

    except Exception as exc:

        return (
            [],
            str(exc)
        )


# ============================================================
# Rule-based forecast
# ============================================================

def rule_based_forecast(
    calculator,
    data,
    months=12,
    growth_rate=0.0,
):
    """
    Create a rule-based monthly emissions forecast.

    Electricity, fuel, transport and production are scaled
    using the monthly growth rate.

    Employee count remains unchanged.
    """

    rows = []

    months = max(
        1,
        int(months)
    )

    growth_rate = float(
        growth_rate
    )

    for month in range(
        1,
        months + 1
    ):

        factor = (
            1.0 + growth_rate
        ) ** month

        projected = deepcopy(
            data
        )

        projected[
            "electricity_kwh_monthly"
        ] = (
            float(
                data.get(
                    "electricity_kwh_monthly",
                    0.0
                )
            )
            * factor
        )

        projected[
            "fuel_liters_monthly"
        ] = (
            float(
                data.get(
                    "fuel_liters_monthly",
                    0.0
                )
            )
            * factor
        )

        projected[
            "transport_km_monthly"
        ] = (
            float(
                data.get(
                    "transport_km_monthly",
                    0.0
                )
            )
            * factor
        )

        projected[
            "production_units_monthly"
        ] = (
            float(
                data.get(
                    "production_units_monthly",
                    0.0
                )
            )
            * factor
        )

        projected[
            "num_employees"
        ] = data.get(
            "num_employees",
            0
        )

        result = (
            calculator.calculate_total_emissions(
                projected
            )
        )

        total = _extract_total(
            result
        )

        rows.append(
            {
                "month": month,
                "prediction_kg": total,
                "predicted_kg": total,
                "predicted_emissions_kg": total,
                "emissions_kg": total,
            }
        )

    return rows


# ============================================================
# Source calculations
# ============================================================

def _calculate_sources(
    data,
    calculator
):
    """
    Calculate source-level emissions for a scenario.

    The original calculator remains the source of truth.
    """

    result = (
        calculator.calculate_total_emissions(
            data
        )
    )

    if not isinstance(
        result,
        dict
    ):
        return {}

    sources = {}

    breakdown = result.get(
        "breakdown",
        {}
    )

    if isinstance(
        breakdown,
        dict
    ):

        for key, value in breakdown.items():

            try:
                sources[str(key)] = float(
                    value
                )
            except (
                TypeError,
                ValueError
            ):
                continue

    return sources


# ============================================================
# Scenario evaluation
# ============================================================

def evaluate_scenario(
    name,
    baseline_data,
    levers,
    calculator,
    predictor=None,
):
    """
    Evaluate one reduction scenario.
    """

    clean_levers = clamp_levers(
        levers
    )

    scenario_data = apply_levers(
        baseline_data,
        clean_levers
    )

    # --------------------------------------------------------
    # Original rule-based calculator
    # --------------------------------------------------------

    baseline_result = (
        calculator.calculate_total_emissions(
            baseline_data
        )
    )

    scenario_result = (
        calculator.calculate_total_emissions(
            scenario_data
        )
    )

    baseline_kg = _extract_total(
        baseline_result
    )

    scenario_kg = _extract_total(
        scenario_result
    )

    reduction_kg = max(
        0.0,
        baseline_kg - scenario_kg
    )

    if baseline_kg > 0:

        reduction_pct = (
            reduction_kg
            / baseline_kg
            * 100.0
        )

    else:

        reduction_pct = 0.0

    # --------------------------------------------------------
    # Existing ML model
    # --------------------------------------------------------

    ml_kg = None
    ml_error = None

    if predictor is not None:

        ml_kg, ml_error = (
            safe_ml_predict(
                predictor,
                scenario_data
            )
        )

    # --------------------------------------------------------
    # Source-level emissions
    # --------------------------------------------------------

    sources_kg = _calculate_sources(
        scenario_data,
        calculator
    )

    return {
        "name": name,

        "levers": clean_levers,

        "data": scenario_data,

        "baseline_kg": baseline_kg,

        "scenario_kg": scenario_kg,

        "emissions_kg": scenario_kg,

        "reduction_kg": reduction_kg,

        "reduction_pct": reduction_pct,

        "predicted_kg": ml_kg,

        "ml_kg": ml_kg,

        "ml_error": ml_error,

        "actions": key_actions(
            clean_levers
        ),

        "sources_kg": sources_kg,
    }


# ============================================================
# Build scenarios
# ============================================================

def build_scenarios(
    data,
    arg2=None,
    arg3=None,
    arg4=None,
):
    """
    Build the four scenarios:

    1. Baseline
    2. Moderate
    3. Aggressive
    4. Custom

    The function identifies calculator, predictor and
    custom sliders by their actual object type/methods.

    Intended app.py call:

        build_scenarios(
            input_data,
            custom_levers,
            calc,
            predictor
        )
    """

    calculator = None
    predictor = None
    custom_levers = None

    args = [
        arg2,
        arg3,
        arg4,
    ]

    # --------------------------------------------------------
    # Identify objects safely
    # --------------------------------------------------------

    for arg in args:

        if arg is None:
            continue

        # EmissionsCalculator
        if hasattr(
            arg,
            "calculate_total_emissions"
        ):
            calculator = arg
            continue

        # EmissionsPredictor
        if hasattr(
            arg,
            "predict_emissions"
        ):
            predictor = arg
            continue

        # Custom What-If values
        if isinstance(
            arg,
            dict
        ):
            custom_levers = arg

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if calculator is None:
        raise TypeError(
            "EmissionsCalculator was not found "
            "in build_scenarios()."
        )

    if custom_levers is None:
        custom_levers = {}

    custom_levers = clamp_levers(
        custom_levers
    )

    # --------------------------------------------------------
    # Baseline
    # --------------------------------------------------------

    baseline = evaluate_scenario(
        "Baseline",
        data,
        PRESETS["Baseline"],
        calculator,
        predictor,
    )

    # --------------------------------------------------------
    # Moderate
    # --------------------------------------------------------

    moderate = evaluate_scenario(
        "Moderate",
        data,
        PRESETS["Moderate"],
        calculator,
        predictor,
    )

    # --------------------------------------------------------
    # Aggressive
    # --------------------------------------------------------

    aggressive = evaluate_scenario(
        "Aggressive",
        data,
        PRESETS["Aggressive"],
        calculator,
        predictor,
    )

    # --------------------------------------------------------
    # Custom
    # --------------------------------------------------------

    custom = evaluate_scenario(
        "Custom",
        data,
        custom_levers,
        calculator,
        predictor,
    )

    return [
        baseline,
        moderate,
        aggressive,
        custom,
    ]


# ============================================================
# Public exports
# ============================================================

__all__ = [
    "LEVER_ORDER",
    "LEVER_MAX",
    "PRESETS",
    "clamp_levers",
    "apply_levers",
    "key_actions",
    "safe_ml_predict",
    "safe_ml_forecast",
    "rule_based_forecast",
    "evaluate_scenario",
    "build_scenarios",
]