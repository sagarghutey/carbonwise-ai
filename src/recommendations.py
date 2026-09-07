class RecommendationEngine:
    """Generate actionable carbon reduction recommendations."""

    def get_recommendations(self, input_data, breakdown):
        recommendations = []

        if breakdown["scope2_pct"] >= 30:
            recommendations.append({
                "action": "Switch to renewable electricity",
                "category": "Energy",
                "description": "Install solar panels or purchase renewable energy to reduce electricity-related emissions.",
                "potential_reduction": "20–40% of Scope 2 emissions",
                "investment": "Medium to High",
                "timeframe": "6–18 months",
                "priority": "High"
            })

        if input_data["electricity_kwh_monthly"] > 50000:
            recommendations.append({
                "action": "Improve energy efficiency",
                "category": "Energy",
                "description": "Use LED lighting, energy-efficient equipment, smart meters, and automated power management.",
                "potential_reduction": "10–20% electricity consumption",
                "investment": "Low to Medium",
                "timeframe": "1–6 months",
                "priority": "High"
            })

        if breakdown["scope1_pct"] >= 20:
            recommendations.append({
                "action": "Reduce fossil fuel usage",
                "category": "Fuel",
                "description": "Replace old equipment with efficient alternatives and consider electric or hybrid vehicles.",
                "potential_reduction": "15–30% of Scope 1 emissions",
                "investment": "Medium",
                "timeframe": "3–12 months",
                "priority": "High"
            })

        if input_data["transport_km_monthly"] > 10000:
            recommendations.append({
                "action": "Optimize transportation routes",
                "category": "Transport",
                "description": "Use route optimization, combine deliveries, and reduce unnecessary trips.",
                "potential_reduction": "10–25% transport emissions",
                "investment": "Low",
                "timeframe": "1–3 months",
                "priority": "Medium"
            })

        if input_data["num_employees"] > 50:
            recommendations.append({
                "action": "Promote employee commuting alternatives",
                "category": "Employee Commute",
                "description": "Encourage public transport, carpooling, cycling, and remote or hybrid work.",
                "potential_reduction": "5–15% commute emissions",
                "investment": "Low",
                "timeframe": "1–3 months",
                "priority": "Medium"
            })

        if input_data["production_units_monthly"] > 0:
            recommendations.append({
                "action": "Improve material and production efficiency",
                "category": "Operations",
                "description": "Reduce material waste, reuse resources, and improve production processes.",
                "potential_reduction": "5–15% indirect emissions",
                "investment": "Medium",
                "timeframe": "3–9 months",
                "priority": "Medium"
            })

        recommendations.append({
            "action": "Track emissions monthly",
            "category": "Monitoring",
            "description": "Maintain monthly records of electricity, fuel, transport, and production data.",
            "potential_reduction": "Better long-term decision making",
            "investment": "Low",
            "timeframe": "Immediate",
            "priority": "Low"
        })

        return recommendations