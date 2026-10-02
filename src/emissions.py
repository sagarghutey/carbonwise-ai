class EmissionsCalculator:
    """Calculate carbon emissions using standard emission factors."""

    EMISSION_FACTORS = {
        "electricity": 0.82,
        "Diesel": 2.68,
        "Petrol": 2.31,
        "Natural Gas": 2.02,
        "Coal": 2.42,
        "LPG": 1.51,
        "transport": 0.21,
        "employee_commute": 0.12,
        "supply_chain": 0.15
    }

    def calculate_scope1(self, fuel_liters, fuel_type):
        factor = self.EMISSION_FACTORS.get(fuel_type, 2.68)
        return fuel_liters * factor

    def calculate_scope2(self, electricity_kwh):
        return electricity_kwh * self.EMISSION_FACTORS["electricity"]

    def calculate_scope3(self, transport_km, num_employees, production_units):
        transport_emissions = (
            transport_km * self.EMISSION_FACTORS["transport"]
        )
        commute_emissions = (
            num_employees * 22 * 10 * 2 * self.EMISSION_FACTORS["employee_commute"]
        )
        supply_chain_emissions = (
            production_units * self.EMISSION_FACTORS["supply_chain"]
        )

        return (
            transport_emissions
            + commute_emissions
            + supply_chain_emissions
        )

    def calculate_total_emissions(self, input_data):
        scope1 = self.calculate_scope1(
            input_data["fuel_liters_monthly"],
            input_data["fuel_type"]
        )

        scope2 = self.calculate_scope2(
            input_data["electricity_kwh_monthly"]
        )

        scope3 = self.calculate_scope3(
            input_data["transport_km_monthly"],
            input_data["num_employees"],
            input_data["production_units_monthly"]
        )

        total = scope1 + scope2 + scope3

        return {
            "scope1_kg": scope1,
            "scope2_kg": scope2,
            "scope3_kg": scope3,
            "total_kg": total,
            "total_tons": total / 1000
        }

    def get_breakdown_percentage(self, emissions):
        total = emissions["total_kg"]

        if total == 0:
            return {
                "scope1_pct": 0,
                "scope2_pct": 0,
                "scope3_pct": 0
            }

        return {
            "scope1_pct": round(emissions["scope1_kg"] / total * 100, 2),
            "scope2_pct": round(emissions["scope2_kg"] / total * 100, 2),
            "scope3_pct": round(emissions["scope3_kg"] / total * 100, 2)
        }

    def identify_top_contributor(self, emissions):
        scopes = {
            "Scope 1 (Direct Fuel)": emissions["scope1_kg"],
            "Scope 2 (Electricity)": emissions["scope2_kg"],
            "Scope 3 (Indirect)": emissions["scope3_kg"]
        }

        return max(scopes, key=scopes.get)