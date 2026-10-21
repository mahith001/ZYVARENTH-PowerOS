from typing import Dict, List


# ============================================================
# BATTERY
# ============================================================

def calculate_battery_energy_kwh(
    capacity_kwh: float,
    soc_percent: float,
) -> float:

    soc_percent = max(
        0.0,
        min(100.0, soc_percent),
    )

    return (
        capacity_kwh
        * soc_percent
        / 100.0
    )


# ============================================================
# SINGLE-HOUR ENERGY DISPATCH
# ============================================================

def calculate_energy_dispatch(
    required_power_kw: float,
    solar_available_kw: float,
    battery_available_kw: float,
    grid_available_kw: float,
    solar_cost_per_kwh: float = 0.0,
    battery_cost_per_kwh: float = 6.0,
    grid_cost_per_kwh: float = 8.5,
) -> Dict:

    if required_power_kw < 0:
        raise ValueError(
            "required_power_kw cannot be negative"
        )

    # --------------------------------------------------------
    # SOLAR
    # --------------------------------------------------------

    solar_used_kw = min(
        required_power_kw,
        max(0.0, solar_available_kw),
    )

    remaining_power = (
        required_power_kw
        - solar_used_kw
    )

    # --------------------------------------------------------
    # BATTERY
    # --------------------------------------------------------

    battery_used_kw = min(
        remaining_power,
        max(0.0, battery_available_kw),
    )

    remaining_power -= battery_used_kw

    # --------------------------------------------------------
    # GRID
    # --------------------------------------------------------

    grid_used_kw = min(
        remaining_power,
        max(0.0, grid_available_kw),
    )

    remaining_power -= grid_used_kw

    # --------------------------------------------------------
    # UNSERVED POWER
    # --------------------------------------------------------

    unserved_power_kw = max(
        0.0,
        remaining_power,
    )

    # --------------------------------------------------------
    # COST
    # --------------------------------------------------------

    total_cost_per_hour = (
        solar_used_kw
        * solar_cost_per_kwh
        + battery_used_kw
        * battery_cost_per_kwh
        + grid_used_kw
        * grid_cost_per_kwh
    )

    # --------------------------------------------------------
    # RENEWABLE SHARE
    # --------------------------------------------------------

    if required_power_kw > 0:

        renewable_share_percent = (
            solar_used_kw
            / required_power_kw
        ) * 100.0

    else:

        renewable_share_percent = 0.0

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if unserved_power_kw > 0:

        status = "POWER_SHORTAGE"

    elif grid_used_kw > 0:

        status = "GRID_SUPPORTED"

    elif battery_used_kw > 0:

        status = "BATTERY_SUPPORTED"

    elif solar_used_kw > 0:

        status = "SOLAR_SUPPORTED"

    else:

        status = "NO_POWER_REQUIRED"

    return {
        "required_power_kw": required_power_kw,
        "solar_used_kw": solar_used_kw,
        "battery_used_kw": battery_used_kw,
        "grid_used_kw": grid_used_kw,
        "unserved_power_kw": unserved_power_kw,
        "total_cost_per_hour": total_cost_per_hour,
        "renewable_share_percent": renewable_share_percent,
        "status": status,
    }


# ============================================================
# 24-HOUR BATTERY SIMULATION
# ============================================================

def simulate_battery_dispatch(
    power_demand_by_hour: List[float],
    solar_by_hour: List[float],
    electricity_prices: List[float],
    battery_capacity_kwh: float,
    initial_soc_percent: float,
    max_discharge_kw: float,
    grid_capacity_kw: float,
    battery_cost_per_kwh: float = 6.0,
) -> Dict:

    if battery_capacity_kwh <= 0:
        raise ValueError(
            "battery_capacity_kwh must be greater than 0"
        )

    if max_discharge_kw < 0:
        raise ValueError(
            "max_discharge_kw cannot be negative"
        )

    battery_energy_kwh = (
        calculate_battery_energy_kwh(
            battery_capacity_kwh,
            initial_soc_percent,
        )
    )

    hourly_results = []

    total_grid_energy = 0.0
    total_solar_energy = 0.0
    total_battery_energy = 0.0
    total_cost = 0.0

    for hour in range(
        len(power_demand_by_hour)
    ):

        demand = max(
            0.0,
            power_demand_by_hour[hour],
        )

        solar = max(
            0.0,
            solar_by_hour[
                min(
                    hour,
                    len(solar_by_hour) - 1,
                )
            ],
        )

        price = max(
            0.0,
            electricity_prices[
                min(
                    hour,
                    len(electricity_prices) - 1,
                )
            ],
        )

        # ----------------------------------------------------
        # SOLAR FIRST
        # ----------------------------------------------------

        solar_used = min(
            demand,
            solar,
        )

        remaining = (
            demand
            - solar_used
        )

        # ----------------------------------------------------
        # BATTERY SECOND
        # ----------------------------------------------------

        battery_used = min(
            remaining,
            max_discharge_kw,
            battery_energy_kwh,
        )

        battery_energy_kwh -= (
            battery_used
        )

        remaining -= battery_used

        # ----------------------------------------------------
        # GRID THIRD
        # ----------------------------------------------------

        grid_used = min(
            remaining,
            grid_capacity_kw,
        )

        remaining -= grid_used

        unserved = max(
            0.0,
            remaining,
        )

        # ----------------------------------------------------
        # COST
        # ----------------------------------------------------

        hour_cost = (
            grid_used * price
            + battery_used
            * battery_cost_per_kwh
        )

        # ----------------------------------------------------
        # SOC
        # ----------------------------------------------------

        soc_percent = (
            battery_energy_kwh
            / battery_capacity_kwh
        ) * 100.0

        # ----------------------------------------------------
        # TOTALS
        # ----------------------------------------------------

        total_grid_energy += grid_used
        total_solar_energy += solar_used
        total_battery_energy += battery_used
        total_cost += hour_cost

        hourly_results.append(
            {
                "hour": hour,
                "demand_kw": demand,
                "solar_used_kw": solar_used,
                "battery_used_kw": battery_used,
                "grid_used_kw": grid_used,
                "unserved_kw": unserved,
                "battery_remaining_kwh": (
                    battery_energy_kwh
                ),
                "battery_soc_percent": (
                    soc_percent
                ),
                "electricity_price": price,
                "cost": hour_cost,
            }
        )

    return {
        "hourly_results": hourly_results,
        "total_grid_energy_kwh": (
            total_grid_energy
        ),
        "total_solar_energy_kwh": (
            total_solar_energy
        ),
        "total_battery_energy_kwh": (
            total_battery_energy
        ),
        "total_cost": total_cost,
        "final_battery_energy_kwh": (
            battery_energy_kwh
        ),
        "final_battery_soc_percent": (
            (
                battery_energy_kwh
                / battery_capacity_kwh
            ) * 100.0
        ),
    }


# ============================================================
# REPORT
# ============================================================

def print_battery_report(
    result: Dict,
):

    print()
    print("=" * 70)
    print("POWEROS BATTERY DISPATCH REPORT")
    print("=" * 70)

    print()

    print(
        f"Total solar energy: "
        f"{result['total_solar_energy_kwh']:.2f} kWh"
    )

    print(
        f"Total battery energy: "
        f"{result['total_battery_energy_kwh']:.2f} kWh"
    )

    print(
        f"Total grid energy: "
        f"{result['total_grid_energy_kwh']:.2f} kWh"
    )

    print(
        f"Total energy cost: "
        f"₹{result['total_cost']:.2f}"
    )

    print(
        f"Final battery energy: "
        f"{result['final_battery_energy_kwh']:.2f} kWh"
    )

    print(
        f"Final battery SOC: "
        f"{result['final_battery_soc_percent']:.1f}%"
    )

    print()

    print("HOURLY BATTERY STATE")
    print("-" * 70)

    for item in result["hourly_results"]:

        print(
            f"Hour {item['hour']:02d} | "
            f"Demand {item['demand_kw']:.1f} kW | "
            f"Solar {item['solar_used_kw']:.1f} kW | "
            f"Battery {item['battery_used_kw']:.1f} kW | "
            f"Grid {item['grid_used_kw']:.1f} kW | "
            f"SOC {item['battery_soc_percent']:.1f}%"
        )

    print()
    print("=" * 70)