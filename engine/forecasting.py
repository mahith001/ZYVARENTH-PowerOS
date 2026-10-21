import pandas as pd


# ============================================================
# ZYVARENTH POWEROS
# FORECASTING ENGINE V1
# ============================================================


def forecast_power_demand(
    jobs: pd.DataFrame,
    horizon_hours: int = 24
) -> list:
    """
    Estimate AI compute power demand for each future hour.

    The forecast is based on the workloads currently known
    to PowerOS.

    Returns:
        List containing estimated demand in kW for each hour.
    """

    forecast = [0.0] * horizon_hours

    if jobs.empty:
        return forecast

    for _, job in jobs.iterrows():

        duration = int(
            job["duration_hours"]
        )

        power = float(
            job["power_kw"]
        )

        deadline = int(
            job["deadline"]
        )

        # Spread workload demand across the
        # available planning horizon.

        latest_start = min(
            max(0, deadline - duration),
            horizon_hours - duration
        )

        if latest_start < 0:
            continue

        # Estimate demand using the earliest
        # feasible position as the planning signal.

        for hour in range(
            duration
        ):

            target_hour = hour

            if target_hour >= horizon_hours:
                break

            forecast[target_hour] += power

    return forecast


# ============================================================
# ELECTRICITY PRICE FORECAST
# ============================================================

def forecast_electricity_prices(
    prices: list
) -> dict:
    """
    Analyze the supplied electricity-price profile.

    Returns hourly prices plus useful statistics.
    """

    if not prices:
        return {
            "hourly_prices": [],
            "average_price": 0.0,
            "minimum_price": 0.0,
            "maximum_price": 0.0,
            "cheapest_hours": [],
            "expensive_hours": [],
        }

    average_price = (
        sum(prices) /
        len(prices)
    )

    minimum_price = min(prices)
    maximum_price = max(prices)

    cheapest_hours = [
        hour
        for hour, price in enumerate(prices)
        if price == minimum_price
    ]

    expensive_hours = [
        hour
        for hour, price in enumerate(prices)
        if price == maximum_price
    ]

    return {
        "hourly_prices": prices,
        "average_price": average_price,
        "minimum_price": minimum_price,
        "maximum_price": maximum_price,
        "cheapest_hours": cheapest_hours,
        "expensive_hours": expensive_hours,
    }


# ============================================================
# SOLAR FORECAST
# ============================================================

def forecast_solar_generation(
    solar_power: list
) -> dict:
    """
    Analyze expected solar generation.
    """

    if not solar_power:
        return {
            "hourly_solar": [],
            "total_solar_kwh": 0.0,
            "peak_solar_kw": 0.0,
            "solar_hours": [],
        }

    total_solar = sum(
        float(value)
        for value in solar_power
    )

    peak_solar = max(
        float(value)
        for value in solar_power
    )

    solar_hours = [
        hour
        for hour, value in enumerate(
            solar_power
        )
        if float(value) > 0
    ]

    return {
        "hourly_solar": solar_power,
        "total_solar_kwh": total_solar,
        "peak_solar_kw": peak_solar,
        "solar_hours": solar_hours,
    }


# ============================================================
# GRID CAPACITY FORECAST
# ============================================================

def forecast_grid_capacity(
    grid_capacity: list
) -> dict:
    """
    Analyze future grid availability.
    """

    if not grid_capacity:
        return {
            "hourly_capacity": [],
            "minimum_capacity_kw": 0.0,
            "maximum_capacity_kw": 0.0,
            "average_capacity_kw": 0.0,
            "constrained_hours": [],
        }

    numeric_capacity = [
        float(value)
        for value in grid_capacity
    ]

    minimum_capacity = min(
        numeric_capacity
    )

    maximum_capacity = max(
        numeric_capacity
    )

    average_capacity = (
        sum(numeric_capacity) /
        len(numeric_capacity)
    )

    constrained_hours = [
        hour
        for hour, value in enumerate(
            numeric_capacity
        )
        if value < 60.0
    ]

    return {
        "hourly_capacity": numeric_capacity,
        "minimum_capacity_kw":
            minimum_capacity,
        "maximum_capacity_kw":
            maximum_capacity,
        "average_capacity_kw":
            average_capacity,
        "constrained_hours":
            constrained_hours,
    }


# ============================================================
# ENERGY OPPORTUNITY ANALYSIS
# ============================================================

def identify_energy_opportunities(
    prices: list,
    solar_power: list,
    grid_capacity: list
) -> pd.DataFrame:
    """
    Identify favorable and unfavorable operating periods.

    This is an analysis layer for the optimizer.
    """

    rows = []

    hours = min(
        len(prices),
        len(solar_power),
        len(grid_capacity)
    )

    for hour in range(hours):

        price = float(
            prices[hour]
        )

        solar = float(
            solar_power[hour]
        )

        grid = float(
            grid_capacity[hour]
        )

        # ----------------------------------------------------
        # Classify electricity price
        # ----------------------------------------------------

        if price <= 6.0:
            price_status = "CHEAP"

        elif price >= 10.0:
            price_status = "EXPENSIVE"

        else:
            price_status = "NORMAL"

        # ----------------------------------------------------
        # Solar status
        # ----------------------------------------------------

        if solar >= 8.0:
            solar_status = "HIGH"

        elif solar > 0:
            solar_status = "AVAILABLE"

        else:
            solar_status = "NONE"

        # ----------------------------------------------------
        # Grid status
        # ----------------------------------------------------

        if grid < 55.0:
            grid_status = "CONSTRAINED"

        elif grid < 65.0:
            grid_status = "LIMITED"

        else:
            grid_status = "AVAILABLE"

        # ----------------------------------------------------
        # Overall opportunity
        # ----------------------------------------------------

        if (
            price_status == "CHEAP"
            and solar_status == "HIGH"
            and grid_status == "AVAILABLE"
        ):
            opportunity = "EXCELLENT"

        elif (
            price_status == "CHEAP"
            or solar_status in [
                "HIGH",
                "AVAILABLE"
            ]
        ):
            opportunity = "GOOD"

        elif (
            price_status == "EXPENSIVE"
            or grid_status == "CONSTRAINED"
        ):
            opportunity = "AVOID"

        else:
            opportunity = "NORMAL"

        rows.append({
            "hour": hour,
            "electricity_price":
                price,
            "solar_power_kw":
                solar,
            "grid_capacity_kw":
                grid,
            "price_status":
                price_status,
            "solar_status":
                solar_status,
            "grid_status":
                grid_status,
            "opportunity":
                opportunity,
        })

    return pd.DataFrame(rows)


# ============================================================
# COMPLETE FORECAST
# ============================================================

def generate_poweros_forecast(
    jobs: pd.DataFrame,
    electricity_prices: list,
    grid_capacity: list,
    solar_power: list,
    horizon_hours: int = 24
) -> dict:
    """
    Generate the complete PowerOS planning forecast.
    """

    power_forecast = forecast_power_demand(
        jobs,
        horizon_hours
    )

    price_forecast = (
        forecast_electricity_prices(
            electricity_prices
        )
    )

    solar_forecast = (
        forecast_solar_generation(
            solar_power
        )
    )

    grid_forecast = (
        forecast_grid_capacity(
            grid_capacity
        )
    )

    opportunities = (
        identify_energy_opportunities(
            electricity_prices,
            solar_power,
            grid_capacity
        )
    )

    return {
        "power_demand_kw":
            power_forecast,

        "electricity":
            price_forecast,

        "solar":
            solar_forecast,

        "grid":
            grid_forecast,

        "opportunities":
            opportunities,
    }


# ============================================================
# FORECAST REPORT
# ============================================================

def print_forecast_report(
    forecast: dict
):
    """
    Display the PowerOS planning forecast.
    """

    electricity = forecast[
        "electricity"
    ]

    solar = forecast[
        "solar"
    ]

    grid = forecast[
        "grid"
    ]

    power = forecast[
        "power_demand_kw"
    ]

    opportunities = forecast[
        "opportunities"
    ]

    print("\n")
    print("=" * 60)
    print(
        "        POWEROS FORECAST ENGINE"
    )
    print("=" * 60)

    print("\nPOWER DEMAND")
    print("-" * 60)

    print(
        f"Forecast peak demand   : "
        f"{max(power):.2f} kW"
    )

    print(
        f"Forecast average demand: "
        f"{sum(power) / len(power):.2f} kW"
        if power
        else
        "Forecast average demand: 0.00 kW"
    )

    print("\nELECTRICITY")
    print("-" * 60)

    print(
        f"Average price          : "
        f"₹{electricity['average_price']:.2f}/kWh"
    )

    print(
        f"Minimum price          : "
        f"₹{electricity['minimum_price']:.2f}/kWh"
    )

    print(
        f"Maximum price          : "
        f"₹{electricity['maximum_price']:.2f}/kWh"
    )

    print(
        f"Cheapest hours         : "
        f"{electricity['cheapest_hours']}"
    )

    print(
        f"Expensive hours        : "
        f"{electricity['expensive_hours']}"
    )

    print("\nSOLAR")
    print("-" * 60)

    print(
        f"Total solar available  : "
        f"{solar['total_solar_kwh']:.2f} kWh"
    )

    print(
        f"Peak solar generation  : "
        f"{solar['peak_solar_kw']:.2f} kW"
    )

    print(
        f"Solar available hours  : "
        f"{len(solar['solar_hours'])}"
    )

    print("\nGRID")
    print("-" * 60)

    print(
        f"Minimum grid capacity  : "
        f"{grid['minimum_capacity_kw']:.2f} kW"
    )

    print(
        f"Maximum grid capacity  : "
        f"{grid['maximum_capacity_kw']:.2f} kW"
    )

    print(
        f"Average grid capacity  : "
        f"{grid['average_capacity_kw']:.2f} kW"
    )

    print(
        f"Constrained hours      : "
        f"{grid['constrained_hours']}"
    )

    print("\nENERGY OPPORTUNITIES")
    print("-" * 60)

    if not opportunities.empty:

        print(
            opportunities[
                [
                    "hour",
                    "electricity_price",
                    "solar_power_kw",
                    "grid_capacity_kw",
                    "opportunity"
                ]
            ].to_string(
                index=False
            )
        )

    else:

        print(
            "No forecast opportunities available."
        )

    print("=" * 60)