import pandas as pd
import joblib

from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error


DATA_PATH = Path("data/emissions_data.csv")
MODEL_DIR = Path("models")


def train_model():
    df = pd.read_csv(DATA_PATH)

    X = df.drop(columns=["total_emissions_kg"])
    y = df["total_emissions_kg"]

    categorical_features = ["industry", "fuel_type"]

    numerical_features = [
        "electricity_kwh_monthly",
        "fuel_liters_monthly",
        "transport_km_monthly",
        "num_employees",
        "production_units_monthly"
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features
            ),
            (
                "numerical",
                "passthrough",
                numerical_features
            )
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)

    model = GradientBoostingRegressor(
        n_estimators=150,
        learning_rate=0.05,
        max_depth=4,
        random_state=42
    )

    model.fit(X_train_processed, y_train)

    predictions = model.predict(X_test_processed)

    r2 = r2_score(y_test, predictions)
    mae = mean_absolute_error(y_test, predictions)

    MODEL_DIR.mkdir(exist_ok=True)

    joblib.dump(model, MODEL_DIR / "carbon_predictor.joblib")
    joblib.dump(preprocessor, MODEL_DIR / "preprocessor.joblib")

    print("Model trained successfully!")
    print(f"R2 Score: {r2:.4f}")
    print(f"Mean Absolute Error: {mae:.2f}")
    print("Model files saved in models/")

    return model, preprocessor


if __name__ == "__main__":
    train_model()