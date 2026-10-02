import joblib
import pandas as pd


class EmissionsPredictor:
    """ML-based carbon emissions predictor."""

    def __init__(self, model_path, preprocessor_path):
        self.model = joblib.load(model_path)
        self.preprocessor = joblib.load(preprocessor_path)

    def _prepare_data(self, input_data):
        df = pd.DataFrame([input_data])

        # Keep the same feature order used during training
        features = [
            "industry",
            "electricity_kwh_monthly",
            "fuel_liters_monthly",
            "fuel_type",
            "transport_km_monthly",
            "num_employees",
            "production_units_monthly"
        ]

        return df[features]

    def predict(self, input_data):
        df = self._prepare_data(input_data)
        transformed_data = self.preprocessor.transform(df)
        prediction = self.model.predict(transformed_data)[0]
        return max(0, float(prediction))

    def predict_future_months(self, input_data, months=12, growth_rate=0.02):
        predictions = []

        for month in range(1, months + 1):
            future_data = input_data.copy()
            multiplier = (1 + growth_rate) ** month

            future_data["electricity_kwh_monthly"] *= multiplier
            future_data["fuel_liters_monthly"] *= multiplier
            future_data["transport_km_monthly"] *= multiplier
            future_data["production_units_monthly"] *= multiplier

            predicted_emissions = self.predict(future_data)

            predictions.append({
                "month": f"Month {month}",
                "predicted_emissions_kg": predicted_emissions
            })

        return predictions

    def predict_reduction_scenarios(self, input_data):
        scenarios = {}

        base_emissions = self.predict(input_data)

        scenarios["Current Practice"] = {
            "description": "No changes in current business activities",
            "predicted_emissions_kg": base_emissions,
            "reduction_kg": 0,
            "reduction_pct": 0
        }

        moderate_data = input_data.copy()
        moderate_data["electricity_kwh_monthly"] *= 0.85
        moderate_data["fuel_liters_monthly"] *= 0.90
        moderate_data["transport_km_monthly"] *= 0.90

        moderate_emissions = self.predict(moderate_data)

        scenarios["Moderate Reduction"] = {
            "description": "15% electricity, 10% fuel and transport reduction",
            "predicted_emissions_kg": moderate_emissions,
            "reduction_kg": base_emissions - moderate_emissions,
            "reduction_pct": round(
                (base_emissions - moderate_emissions) / base_emissions * 100, 2
            ) if base_emissions else 0
        }

        aggressive_data = input_data.copy()
        aggressive_data["electricity_kwh_monthly"] *= 0.65
        aggressive_data["fuel_liters_monthly"] *= 0.70
        aggressive_data["transport_km_monthly"] *= 0.75

        aggressive_emissions = self.predict(aggressive_data)

        scenarios["Aggressive Reduction"] = {
            "description": "35% electricity, 30% fuel and 25% transport reduction",
            "predicted_emissions_kg": aggressive_emissions,
            "reduction_kg": base_emissions - aggressive_emissions,
            "reduction_pct": round(
                (base_emissions - aggressive_emissions) / base_emissions * 100, 2
            ) if base_emissions else 0
        }

        return scenarios