"""
ESG Calculator
Step 1: Scope 1 - Direct Emissions (Diesel, Gasoline, Natural Gas)
"""

# Emission factors in kgCO2e per unit of fuel (industry-standard averages)
SCOPE1_EMISSION_FACTORS = {
    "diesel_liters": 2.68,        # kgCO2e per liter
    "gasoline_liters": 2.31,      # kgCO2e per liter
    "natural_gas_m3": 1.89,       # kgCO2e per cubic meter
}


def calculate_scope1_emissions(fuel_usage: dict) -> dict:
    """
    Calculate Scope 1 direct emissions from fuel consumption.

    fuel_usage: dict with keys like 'diesel_liters', 'gasoline_liters',
                'natural_gas_m3' mapped to quantity consumed.

    Returns a breakdown per fuel type plus the total emissions (kgCO2e).
    """
    breakdown = {}
    total_emissions = 0.0

    # Multiply each fuel's usage by its emission factor
    for fuel_type, quantity in fuel_usage.items():
        factor = SCOPE1_EMISSION_FACTORS.get(fuel_type, 0)
        emissions = quantity * factor
        breakdown[fuel_type] = round(emissions, 2)
        total_emissions += emissions

    breakdown["total_scope1_emissions_kgco2e"] = round(total_emissions, 2)
    return breakdown


# Example usage
if __name__ == "__main__":
    sample_data = {
        "diesel_liters": 1000,
        "gasoline_liters": 500,
        "natural_gas_m3": 300,
    }
    print(calculate_scope1_emissions(sample_data))