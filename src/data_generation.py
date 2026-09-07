import pandas as pd
import numpy as np
from pathlib import Path


def generate_data(n_samples=5000):
    np.random.seed(42)

    industries = [
        "Manufacturing",
        "IT Services",
        "Logistics",
        "Retail",
        "Food Processing",
        "Textiles",
        "Chemicals",
        "Construction",
        "Hospitality",
        "Healthcare"
    ]

    fuel_types = [
        "Diesel",
        "Petrol",
        "Natural Gas",
        "Coal",
        "LPG"
    ]

    data = []

    for _ in range(n_samples):
        industry = np.random.choice(industries)
        fuel_type = np.random.choice(fuel_types)

        electricity = np.random.uniform(5000, 500000)
        fuel = np.random.uniform(100, 50000)
        transport = np.random.uniform(500, 100000)
        employees = np.random.randint(5, 2000)
        production = np.random.uniform(100, 100000)

        electricity_emissions = electricity * 0.82

        fuel_factors = {
            "Diesel": 2.68,
            "Petrol": 2.31,
            "Natural Gas": 2.02,
            "Coal": 2.42,
            "LPG": 1.51
        }

        fuel_emissions = fuel * fuel_factors[fuel_type]
        transport_emissions = transport * 0.21
        commute_emissions = employees * 22 * 10 * 2 * 0.12
        supply_chain_emissions = production * 0.15

        total_emissions = (
            electricity_emissions
            + fuel_emissions
            + transport_emissions
            + commute_emissions
            + supply_chain_emissions
        )

        data.append({
            "industry": industry,
            "electricity_kwh_monthly": electricity,
            "fuel_liters_monthly": fuel,
            "fuel_type": fuel_type,
            "transport_km_monthly": transport,
            "num_employees": employees,
            "production_units_monthly": production,
            "total_emissions_kg": total_emissions
        })

    return pd.DataFrame(data)


if __name__ == "__main__":
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)

    df = generate_data()
    df.to_csv(output_dir / "emissions_data.csv", index=False)

    print(f"Generated {len(df)} records")
    print("Saved to data/emissions_data.csv")