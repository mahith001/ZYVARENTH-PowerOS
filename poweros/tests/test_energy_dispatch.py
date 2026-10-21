from poweros.intelligence.energy_dispatch import (
    calculate_battery_energy_kwh,
    simulate_battery_dispatch,
)


def main():

    # --------------------------------------------------------
    # INITIAL BATTERY
    # --------------------------------------------------------

    energy = calculate_battery_energy_kwh(
        capacity_kwh=100,
        soc_percent=80,
    )

    assert energy == 80

    # --------------------------------------------------------
    # 4-HOUR SIMULATION
    # --------------------------------------------------------

    result = simulate_battery_dispatch(

        power_demand_by_hour=[
            30,
            30,
            30,
            30,
        ],

        solar_by_hour=[
            20,
            10,
            0,
            0,
        ],

        electricity_prices=[
            5,
            6,
            10,
            12,
        ],

        battery_capacity_kwh=100,

        initial_soc_percent=80,

        max_discharge_kw=10,

        grid_capacity_kw=50,
    )

    # Hour 0:
    # 30 demand
    # 20 solar
    # 10 battery

    assert (
        result["hourly_results"][0][
            "battery_used_kw"
        ]
        == 10
    )

    # Battery started with 80 kWh.
    # Four hours can use at most 10 kWh/hour.
    assert (
        result["final_battery_energy_kwh"]
        == 40
    )

    assert (
        result["final_battery_soc_percent"]
        == 40
    )

    assert (
        result["total_battery_energy_kwh"]
        == 40
    )

    print(
        "POWEROS BATTERY SOC TEST PASSED"
    )


if __name__ == "__main__":

    main()