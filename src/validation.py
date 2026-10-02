from __future__ import annotations

from typing import Any, Dict, List, Tuple


# Keep these aligned with the original project / ML training inputs.
INDUSTRIES = [
    "Manufacturing",
    "IT Services",
    "Construction",
    "Retail",
    "Healthcare",
    "Hospitality",
    "Logistics",
    "Agriculture",
    "Other",
]

FUEL_TYPES = [
    "Diesel",
    "Petrol",
    "Natural Gas",
    "Coal",
    "LPG",
]


# Approximate ranges used only to warn users when inputs are far
# outside the range normally expected by the original ML model.
TRAINING_RANGES = {
    "electricity_kwh_monthly": (0.0, 500000.0),
    "fuel_liters_monthly": (0.0, 100000.0),
    "transport_km_monthly": (0.0, 500000.0),
    "num_employees": (1, 10000),
    "production_units_monthly": (0.0, 1000000.0),
}


NUMERIC_FIELDS = [
    "electricity_kwh_monthly",
    "fuel_liters_monthly",
    "transport_km_monthly",
    "num_employees",
    "production_units_monthly",
]


def _to_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 1) -> int:
    """Safely convert a value to integer."""
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def validate_inputs(
    raw: Dict[str, Any],
) -> Tuple[Dict[str, Any] | None, List[str], List[str]]:
    """
    Validate and normalize the main CarbonWise input dictionary.

    Returns:
        clean_data:
            Normalized input dictionary, or None when validation fails.
        errors:
            Blocking validation errors.
        warnings:
            Non-blocking warnings.
    """

    errors: List[str] = []
    warnings: List[str] = []

    industry = str(raw.get("industry", "Manufacturing")).strip()
    fuel_type = str(raw.get("fuel_type", "Diesel")).strip()

    # Normalize numeric values.
    clean = {
        "industry": industry,
        "electricity_kwh_monthly": _to_float(
            raw.get("electricity_kwh_monthly", 0.0)
        ),
        "fuel_liters_monthly": _to_float(
            raw.get("fuel_liters_monthly", 0.0)
        ),
        "fuel_type": fuel_type,
        "transport_km_monthly": _to_float(
            raw.get("transport_km_monthly", 0.0)
        ),
        "num_employees": _to_int(
            raw.get("num_employees", 1),
            default=1,
        ),
        "production_units_monthly": _to_float(
            raw.get("production_units_monthly", 0.0)
        ),
    }

    # Basic categorical validation.
    if industry not in INDUSTRIES:
        errors.append(
            f"Industry '{industry}' is not supported."
        )

    if fuel_type not in FUEL_TYPES:
        errors.append(
            f"Fuel type '{fuel_type}' is not supported."
        )

    # Negative values are invalid.
    for field in NUMERIC_FIELDS:
        value = clean[field]

        if value < 0:
            errors.append(
                f"{field} cannot be negative."
            )

    # Employees must be at least 1.
    if clean["num_employees"] < 1:
        errors.append(
            "Number of employees must be at least 1."
        )

    if errors:
        return None, errors, warnings

    # Warn when all activity values are zero.
    activity_fields = [
        "electricity_kwh_monthly",
        "fuel_liters_monthly",
        "transport_km_monthly",
        "production_units_monthly",
    ]

    if all(clean[field] == 0 for field in activity_fields):
        warnings.append(
            "All activity inputs are zero. Carbon emissions will be zero "
            "for the activity-based calculation."
        )

    # ML training-range warnings.
    for field, (minimum, maximum) in TRAINING_RANGES.items():
        value = clean[field]

        if value < minimum or value > maximum:
            warnings.append(
                f"{field} is outside the approximate ML training range "
                f"({minimum:g}–{maximum:g}). The ML prediction may be less reliable."
            )

    # Additional useful data-quality warnings.
    if clean["electricity_kwh_monthly"] == 0:
        warnings.append(
            "Electricity consumption is zero; Scope 2 emissions will be zero."
        )

    if clean["fuel_liters_monthly"] == 0:
        warnings.append(
            "Fuel consumption is zero; Scope 1 fuel emissions will be zero."
        )

    if clean["transport_km_monthly"] == 0:
        warnings.append(
            "Transport activity is zero; transport-related Scope 3 emissions will be zero."
        )

    if clean["production_units_monthly"] == 0:
        warnings.append(
            "Production volume is zero; supply-chain production emissions will be zero."
        )

    return clean, errors, warnings