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


# Average national grid emission factor, used for location-based method
GRID_EMISSION_FACTOR = 0.45  # kgCO2e per kWh


def calculate_scope2_emissions(electricity_kwh: float, market_factor: float = None,
                                renewable_kwh: float = 0) -> dict:
    """
    Calculate Scope 2 indirect emissions from purchased electricity.

    electricity_kwh: total electricity consumed (kWh)
    market_factor:   supplier-specific emission factor (kgCO2e/kWh),
                      used for the market-based method if provided
    renewable_kwh:   electricity covered by renewable contracts/RECs,
                      treated as zero-emission under market-based method

    Returns both location-based and market-based emission totals.
    """
    # Location-based: uses the average grid factor, ignores offsets
    location_based = electricity_kwh * GRID_EMISSION_FACTOR

    # Market-based: uses supplier factor (or grid factor as fallback),
    # and subtracts renewable-covered kWh as zero-emission
    factor = market_factor if market_factor is not None else GRID_EMISSION_FACTOR
    non_renewable_kwh = max(electricity_kwh - renewable_kwh, 0)
    market_based = non_renewable_kwh * factor

    return {
        "location_based_kgco2e": round(location_based, 2),
        "market_based_kgco2e": round(market_based, 2),
    }


# Example usage
if __name__ == "__main__":
    sample_data = {
        "diesel_liters": 1000,
        "gasoline_liters": 500,
        "natural_gas_m3": 300,
    }
    print(calculate_scope1_emissions(sample_data))

    print(calculate_scope2_emissions(
        electricity_kwh=10000,
        market_factor=0.30,
        renewable_kwh=2000,
    ))