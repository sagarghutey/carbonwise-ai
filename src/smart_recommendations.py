from __future__ import annotations

from typing import Any, Dict, List

from recommendations import RecommendationEngine


PRIORITY_ORDER = {
    "High": 0,
    "Medium": 1,
    "Low": 2,
}


def _normalise_recommendation(item: Any) -> Dict[str, Any]:
    """Convert different recommendation formats into a dictionary."""

    if isinstance(item, dict):
        return dict(item)

    return {
        "action": str(item),
        "description": str(item),
    }


def _priority_for_source(
    emissions: float,
    total: float,
) -> str:
    """Assign a simple priority based on contribution."""

    if total <= 0:
        return "Low"

    share = emissions / total * 100.0

    if share >= 30:
        return "High"

    if share >= 10:
        return "Medium"

    return "Low"


def _lever_for_action(action: str) -> str:
    """Map a recommendation to the corresponding What-If lever."""

    text = action.lower()

    if "electric" in text or "renewable" in text or "energy" in text:
        return "electricity"

    if "fuel" in text or "fossil" in text:
        return "fuel"

    if "transport" in text or "route" in text or "commute" in text:
        return "transport"

    if "production" in text or "efficiency" in text:
        return "production"

    return "electricity"


def _estimate_for_lever(
    lever: str,
    sources: Dict[str, float],
) -> str:
    """
    Provide a conservative indicative reduction range.

    These are planning ranges, not guaranteed savings.
    """

    source_map = {
        "electricity": "Electricity",
        "fuel": "Fuel",
        "transport": "Transport",
        "production": "Supply Chain",
    }

    source = source_map.get(lever)

    if source is None:
        return "Indicative impact varies by implementation."

    emissions = float(sources.get(source, 0.0))

    if emissions <= 0:
        return "No measurable baseline impact from this source."

    if lever == "electricity":
        low, high = 5, 20
    elif lever == "fuel":
        low, high = 5, 15
    elif lever == "transport":
        low, high = 5, 15
    else:
        low, high = 3, 10

    low_kg = emissions * low / 100.0
    high_kg = emissions * high / 100.0

    return (
        f"Indicative {low}–{high}% reduction of this source "
        f"(about {low_kg:,.0f}–{high_kg:,.0f} kg CO2e/month)."
    )


def _why_for_action(
    action: str,
    lever: str,
    sources: Dict[str, float],
) -> str:
    """Explain why the recommendation appears."""

    source_map = {
        "electricity": "Electricity",
        "fuel": "Fuel",
        "transport": "Transport",
        "production": "Supply Chain",
    }

    source = source_map.get(lever)

    if source and float(sources.get(source, 0.0)) > 0:
        return (
            f"{source} is contributing to the current footprint, "
            "so reducing this activity can directly lower calculated emissions."
        )

    if "track" in action.lower():
        return (
            "Regular monthly tracking helps identify changes in activity "
            "and whether reduction measures are working."
        )

    return (
        "This action targets an emissions source or operational activity "
        "that can influence the calculated footprint."
    )


def _timeframe_for_priority(priority: str) -> str:
    """Return a practical implementation timeframe."""

    if priority == "High":
        return "Start now"

    if priority == "Medium":
        return "Next 3–6 months"

    return "Ongoing"


def _fallback_recommendations(
    data: Dict[str, Any],
    sources: Dict[str, float],
) -> List[Dict[str, Any]]:
    """
    Fallback recommendation rules matching the original project's
    major recommendation themes.
    """

    recommendations: List[Dict[str, Any]] = []

    electricity = float(
        data.get("electricity_kwh_monthly", 0.0)
    )
    fuel = float(
        data.get("fuel_liters_monthly", 0.0)
    )
    transport = float(
        data.get("transport_km_monthly", 0.0)
    )
    employees = int(
        data.get("num_employees", 0)
    )
    production = float(
        data.get("production_units_monthly", 0.0)
    )

    total = sum(sources.values())

    if sources.get("Electricity", 0.0) > 0:
        recommendations.append(
            {
                "action": "Increase renewable electricity",
                "category": "Energy",
                "description": (
                    "Explore renewable electricity procurement or "
                    "on-site renewable generation."
                ),
                "source": "Electricity",
            }
        )

    if electricity > 50000:
        recommendations.append(
            {
                "action": "Improve energy efficiency",
                "category": "Energy",
                "description": (
                    "Audit major electrical loads and improve "
                    "equipment and operating efficiency."
                ),
                "source": "Electricity",
            }
        )

    if sources.get("Fuel", 0.0) >= 20:
        recommendations.append(
            {
                "action": "Reduce fossil fuel consumption",
                "category": "Fuel",
                "description": (
                    "Reduce direct fossil-fuel use through efficiency, "
                    "electrification, or cleaner alternatives where practical."
                ),
                "source": "Fuel",
            }
        )

    if transport > 10000:
        recommendations.append(
            {
                "action": "Optimize transport routes",
                "category": "Transport",
                "description": (
                    "Improve routing, trip consolidation, and "
                    "vehicle utilization."
                ),
                "source": "Transport",
            }
        )

    if employees > 50:
        recommendations.append(
            {
                "action": "Offer commute alternatives",
                "category": "Transport",
                "description": (
                    "Consider public transport, shared mobility, "
                    "remote-work options, or organized employee transport."
                ),
                "source": "Employee Commute",
            }
        )

    if production > 0:
        recommendations.append(
            {
                "action": "Improve production efficiency",
                "category": "Operations",
                "description": (
                    "Reduce material and process intensity per unit "
                    "of production."
                ),
                "source": "Supply Chain",
            }
        )

    # Keep this as the final recommendation.
    recommendations.append(
        {
            "action": "Track emissions monthly",
            "category": "Measurement",
            "description": (
                "Track activity and emissions every month to measure "
                "progress and identify new hotspots."
            ),
            "source": None,
        }
    )

    return recommendations


def build_smart_recommendations(
    data: Dict[str, Any],
    breakdown: Any = None,
    sources_kg: Dict[str, float] | None = None,
) -> List[Dict[str, Any]]:
    """
    Build enriched recommendations using the original recommendation
    engine where possible, with a compatible fallback.
    """

    sources = sources_kg or {}

    total = sum(
        float(value)
        for value in sources.values()
    )

    raw_recommendations: List[Any] = []

    # Try the original RecommendationEngine first.
    try:
        engine = RecommendationEngine()

        # Support common method names without changing the original
        # recommendation module.
        if hasattr(engine, "generate_recommendations"):
            try:
                raw_recommendations = engine.generate_recommendations(
                    data,
                    breakdown,
                )
            except TypeError:
                raw_recommendations = engine.generate_recommendations(
                    data
                )

        elif hasattr(engine, "get_recommendations"):
            try:
                raw_recommendations = engine.get_recommendations(
                    data,
                    breakdown,
                )
            except TypeError:
                raw_recommendations = engine.get_recommendations(
                    data
                )

    except Exception:
        raw_recommendations = []

    # If the original engine could not be called, use the compatible
    # rule set above.
    if not raw_recommendations:
        raw_recommendations = _fallback_recommendations(
            data,
            sources,
        )

    enriched: List[Dict[str, Any]] = []

    for item in raw_recommendations:
        rec = _normalise_recommendation(item)

        action = str(
            rec.get(
                "action",
                rec.get("title", "Recommendation"),
            )
        )

        description = str(
            rec.get(
                "description",
                rec.get("reason", ""),
            )
        )

        # Identify source/lever.
        source = rec.get("source")

        lever = _lever_for_action(action)

        if source is None:
            source_map = {
                "electricity": "Electricity",
                "fuel": "Fuel",
                "transport": "Transport",
                "production": "Supply Chain",
            }
            source = source_map.get(lever)

        source_emissions = float(
            sources.get(source, 0.0)
            if source
            else 0.0
        )

        priority = _priority_for_source(
            source_emissions,
            total,
        )

        # Tracking is deliberately a low-priority recurring action.
        if "track" in action.lower():
            priority = "Low"

        enriched.append(
            {
                **rec,
                "action": action,
                "category": rec.get(
                    "category",
                    "Operations",
                ),
                "description": description,
                "why": _why_for_action(
                    action,
                    lever,
                    sources,
                ),
                "estimate_text": _estimate_for_lever(
                    lever,
                    sources,
                ),
                "lever_text": (
                    f"What-If lever: {lever.replace('_', ' ').title()}"
                ),
                "lever": lever,
                "priority": priority,
                "timeframe": _timeframe_for_priority(
                    priority
                ),
                "investment": rec.get(
                    "investment",
                    "Varies by implementation",
                ),
            }
        )

    # Ensure monthly tracking exists.
    if not any(
        "track" in str(item.get("action", "")).lower()
        for item in enriched
    ):
        enriched.append(
            {
                "action": "Track emissions monthly",
                "category": "Measurement",
                "description": (
                    "Track activity and emissions every month to "
                    "measure progress."
                ),
                "why": (
                    "Regular measurement makes it easier to identify "
                    "changes and evaluate reduction actions."
                ),
                "estimate_text": (
                    "Measurement action; no direct reduction estimate."
                ),
                "lever_text": "Monitoring action",
                "lever": None,
                "priority": "Low",
                "timeframe": "Ongoing",
                "investment": "Low",
            }
        )

    # Sort by priority while keeping the tracking action at the end.
    tracking = [
        item
        for item in enriched
        if "track" in str(item.get("action", "")).lower()
    ]

    normal = [
        item
        for item in enriched
        if "track" not in str(item.get("action", "")).lower()
    ]

    normal.sort(
        key=lambda item: PRIORITY_ORDER.get(
            item.get("priority", "Low"),
            2,
        )
    )

    return normal + tracking