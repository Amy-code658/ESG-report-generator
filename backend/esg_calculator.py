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


# Business travel emission factors (kgCO2e per km, by mode)
TRAVEL_EMISSION_FACTORS = {
    "air_km": 0.150,
    "rail_km": 0.041,
    "car_km": 0.171,
}

# Waste disposal emission factors (kgCO2e per kg)
LANDFILL_FACTOR = 0.58   # waste sent to landfill
RECYCLING_FACTOR = 0.02  # waste diverted to recycling


def calculate_scope3_emissions(travel_data: dict, waste_data: dict) -> dict:
    """
    Calculate Scope 3 value chain emissions from business travel and waste.

    travel_data: dict with keys like 'air_km', 'rail_km', 'car_km'
    waste_data:  dict with 'total_waste_kg' and 'recycled_kg'

    Returns emissions breakdown for travel and waste, plus the combined total.
    """
    # Sum emissions across all travel modes provided
    travel_emissions = sum(
        distance * TRAVEL_EMISSION_FACTORS.get(mode, 0)
        for mode, distance in travel_data.items()
    )

    # Split waste into recycled vs landfill portions, each with its own factor
    total_waste = waste_data.get("total_waste_kg", 0)
    recycled = waste_data.get("recycled_kg", 0)
    landfill = max(total_waste - recycled, 0)

    waste_emissions = (recycled * RECYCLING_FACTOR) + (landfill * LANDFILL_FACTOR)
    diversion_rate = (recycled / total_waste * 100) if total_waste > 0 else 0

    return {
        "travel_emissions_kgco2e": round(travel_emissions, 2),
        "waste_emissions_kgco2e": round(waste_emissions, 2),
        "waste_diversion_rate_pct": round(diversion_rate, 2),
        "total_scope3_emissions_kgco2e": round(travel_emissions + waste_emissions, 2),
    }


def calculate_social_metrics(social_data: dict) -> dict:
    """
    Calculate key Social (S) metrics for ESG reporting.

    Expected keys in social_data:
        total_employees, diverse_employees, total_executives,
        female_executives, total_training_hours,
        lost_time_injuries, total_hours_worked

    Returns diversity %, executive female ratio %, avg training hours,
    and LTIFR (Lost Time Injury Frequency Rate).
    """
    total_employees = social_data.get("total_employees", 0)
    total_executives = social_data.get("total_executives", 0)
    total_hours_worked = social_data.get("total_hours_worked", 0)

    # Overall workforce diversity percentage
    diversity_pct = (
        social_data.get("diverse_employees", 0) / total_employees * 100
        if total_employees > 0 else 0
    )

    # Share of female employees in executive roles
    exec_female_ratio = (
        social_data.get("female_executives", 0) / total_executives * 100
        if total_executives > 0 else 0
    )

    # Average training hours per employee
    avg_training_hours = (
        social_data.get("total_training_hours", 0) / total_employees
        if total_employees > 0 else 0
    )

    # LTIFR: lost time injuries per 1,000,000 hours worked (standard safety metric)
    ltifr = (
        social_data.get("lost_time_injuries", 0) * 1_000_000 / total_hours_worked
        if total_hours_worked > 0 else 0
    )

    return {
        "diversity_pct": round(diversity_pct, 2),
        "executive_female_ratio_pct": round(exec_female_ratio, 2),
        "avg_training_hours": round(avg_training_hours, 2),
        "ltifr": round(ltifr, 2),
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

    print(calculate_scope3_emissions(
        travel_data={"air_km": 5000, "rail_km": 1200, "car_km": 800},
        waste_data={"total_waste_kg": 2000, "recycled_kg": 1200},
    ))

    print(calculate_social_metrics({
        "total_employees": 500,
        "diverse_employees": 210,
        "total_executives": 20,
        "female_executives": 7,
        "total_training_hours": 8000,
        "lost_time_injuries": 3,
        "total_hours_worked": 1_000_000,
    }))