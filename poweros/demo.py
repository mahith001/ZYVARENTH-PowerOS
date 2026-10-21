from poweros.core.models import (
    GPU,
    Workload,
    PowerState,
    EnergyResource,
    DataCenterState,
)

from poweros.core.orchestrator import (
    run_poweros,
    print_poweros_report,
)


def create_demo_state():

    # ========================================================
    # GPU FLEET
    # ========================================================

    gpus = []

    for i in range(20):

        gpus.append(
            GPU(
                gpu_id=f"GPU-{i + 1:03d}",
                utilization_percent=65,
                power_kw=0.55,
                temperature_c=65,
                memory_utilization_percent=60,
                available=True,
            )
        )

    # ========================================================
    # AI WORKLOADS
    # ========================================================

    workloads = [

        Workload(
            workload_id="LLM-TRAIN-001",
            gpu_required=8,
            duration_hours=4,
            deadline_hour=12,
            priority="HIGH",
        ),

        Workload(
            workload_id="LLM-TRAIN-002",
            gpu_required=6,
            duration_hours=3,
            deadline_hour=16,
            priority="HIGH",
        ),

        Workload(
            workload_id="INFERENCE-001",
            gpu_required=2,
            duration_hours=2,
            deadline_hour=18,
            priority="MEDIUM",
        ),

        Workload(
            workload_id="BATCH-001",
            gpu_required=4,
            duration_hours=3,
            deadline_hour=22,
            priority="LOW",
        ),
    ]

    # ========================================================
    # CURRENT POWER
    # ========================================================

    power = PowerState(
        available_power_kw=50,
        grid_capacity_kw=60,
        electricity_price_per_kwh=8.5,
        solar_power_kw=15,
        battery_available_kw=10,
    )

    # ========================================================
    # ENERGY RESOURCES
    # ========================================================

    resources = [

        EnergyResource(
            name="Grid",
            available_power_kw=60,
            cost_per_kwh=8.5,
            renewable=False,
        ),

        EnergyResource(
            name="Solar",
            available_power_kw=15,
            cost_per_kwh=0,
            renewable=True,
        ),

        EnergyResource(
            name="Battery",
            available_power_kw=10,
            cost_per_kwh=6.0,
            renewable=False,
        ),
    ]

    # ========================================================
    # DATA CENTER STATE
    # ========================================================

    return DataCenterState(
        timestamp="2026-09-20T15:00:00",
        gpus=gpus,
        workloads=workloads,
        power=power,
        energy_resources=resources,
        pue=1.3,
    )


def create_hourly_prices():

    return [
        9.0,   # 00
        8.8,   # 01
        8.5,   # 02
        8.0,   # 03
        7.0,   # 04
        6.5,   # 05
        6.0,   # 06
        5.5,   # 07
        5.0,   # 08
        5.5,   # 09
        6.0,   # 10
        7.0,   # 11
        8.0,   # 12
        9.0,   # 13
        10.0,  # 14
        11.0,  # 15
        12.0,  # 16
        13.0,  # 17
        12.0,  # 18
        11.0,  # 19
        10.0,  # 20
        9.5,   # 21
        9.0,   # 22
        8.5,   # 23
    ]


def create_hourly_solar():

    return [
        0,   # 00
        0,   # 01
        0,   # 02
        0,   # 03
        1,   # 04
        3,   # 05
        6,   # 06
        10,  # 07
        15,  # 08
        20,  # 09
        25,  # 10
        30,  # 11
        35,  # 12
        32,  # 13
        28,  # 14
        22,  # 15
        16,  # 16
        10,  # 17
        5,   # 18
        2,   # 19
        0,   # 20
        0,   # 21
        0,   # 22
        0,   # 23
    ]


def main():

    print()
    print("=" * 70)
    print("ZYVARENTH POWEROS")
    print("DYNAMIC POWER-AWARE DEMONSTRATION")
    print("=" * 70)

    state = create_demo_state()

    hourly_prices = create_hourly_prices()

    hourly_solar = create_hourly_solar()

    result = run_poweros(
    state=state,
    horizon_hours=24,
    electricity_prices=hourly_prices,
    solar_power_by_hour=hourly_solar,
    battery_capacity_kwh=100,
    initial_battery_soc_percent=80,
    battery_max_discharge_kw=10,
)

    print_poweros_report(
        result
    )

    print()
    print("HOURLY ENERGY CONDITIONS")
    print("-" * 70)

    for hour in range(24):

        print(
            f"Hour {hour:02d} | "
            f"Price: ₹{hourly_prices[hour]:.2f}/kWh | "
            f"Solar: {hourly_solar[hour]:.1f} kW"
        )

    print()
    print("=" * 70)
    print("FINAL STATUS:")
    print("POWEROS DYNAMIC OPTIMIZATION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()