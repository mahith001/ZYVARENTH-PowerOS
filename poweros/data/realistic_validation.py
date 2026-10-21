from typing import List, Dict

from poweros.core.models import (
    GPU,
    Workload,
    PowerState,
    EnergyResource,
    DataCenterState,
)

from poweros.data.realistic_workloads import (
    get_realistic_workloads,
)

from poweros.core.orchestrator import (
    run_poweros,
)


# =========================================================
# BUILD REALISTIC DATA CENTER
# =========================================================

def build_realistic_state():
    """
    Build a realistic AI data-center state
    from the PowerOS workload dataset.
    """

    # -----------------------------------------------------
    # GPU CLUSTER
    # -----------------------------------------------------

    gpus = []

    for i in range(1, 33):

        gpus.append(
            GPU(
                gpu_id=f"GPU-{i:03d}",
                utilization_percent=55.0,
                power_kw=0.70,
                temperature_c=65.0,
                memory_utilization_percent=60.0,
                available=True,
            )
        )

    # -----------------------------------------------------
    # WORKLOADS
    # -----------------------------------------------------

    workload_data = get_realistic_workloads()

    workloads = []

    for item in workload_data:

        workloads.append(
            Workload(
                workload_id=item["workload_id"],
                gpu_required=item["gpu_required"],
                duration_hours=item["duration_hours"],
                deadline_hour=item["deadline_hour"],
                priority=item["priority"],
            )
        )

    # -----------------------------------------------------
    # POWER
    # -----------------------------------------------------

    power = PowerState(
        available_power_kw=40.0,
        grid_capacity_kw=50.0,
        electricity_price_per_kwh=8.50,
        solar_power_kw=10.0,
        battery_available_kw=10.0,
    )

    # -----------------------------------------------------
    # ENERGY RESOURCES
    # -----------------------------------------------------

    resources = [
        EnergyResource(
            name="GRID",
            available_power_kw=50.0,
            cost_per_kwh=8.50,
            renewable=False,
        ),
        EnergyResource(
            name="SOLAR",
            available_power_kw=10.0,
            cost_per_kwh=0.0,
            renewable=True,
        ),
        EnergyResource(
            name="BATTERY",
            available_power_kw=10.0,
            cost_per_kwh=6.0,
            renewable=False,
        ),
    ]

    # -----------------------------------------------------
    # DATA CENTER STATE
    # -----------------------------------------------------

    return DataCenterState(
        timestamp="2026-10-02T10:00:00",
        gpus=gpus,
        workloads=workloads,
        power=power,
        energy_resources=resources,
        pue=1.30,
    )


# =========================================================
# REALISTIC ELECTRICITY PRICES
# =========================================================

def create_realistic_prices():

    return [
        9.5,
        9.2,
        9.0,
        8.8,
        8.0,
        7.5,
        7.0,
        6.5,
        6.0,
        5.8,
        5.5,
        5.8,
        6.2,
        6.8,
        7.5,
        8.5,
        9.5,
        10.5,
        11.0,
        10.5,
        10.0,
        9.8,
        9.6,
        9.5,
    ]


# =========================================================
# REALISTIC SOLAR PROFILE
# =========================================================

def create_realistic_solar():

    return [
        0,
        0,
        0,
        0,
        1,
        3,
        5,
        8,
        12,
        16,
        20,
        24,
        27,
        25,
        22,
        18,
        13,
        8,
        4,
        1,
        0,
        0,
        0,
        0,
    ]


# =========================================================
# RUN REALISTIC VALIDATION
# =========================================================

def run_realistic_validation():

    state = build_realistic_state()

    prices = create_realistic_prices()

    solar = create_realistic_solar()

    result = run_poweros(
        state=state,
        horizon_hours=24,
        electricity_prices=prices,
        solar_power_by_hour=solar,
        battery_capacity_kwh=100,
        initial_battery_soc_percent=80,
        battery_max_discharge_kw=10,
    )

    return result


# =========================================================
# PRINT VALIDATION RESULT
# =========================================================

def print_validation_result(
    result: Dict,
):
    """
    Print realistic PowerOS validation results.
    """

    # -----------------------------------------------------
    # GET RESULT SECTIONS
    # -----------------------------------------------------

    optimization = result.get(
        "optimization_summary",
        {},
    )

    decisions = result.get(
        "decision_summary",
        {},
    )

    state_analysis = result.get(
        "state_analysis",
        {},
    )

    power_summary = result.get(
        "power_summary",
        {},
    )

    # -----------------------------------------------------
    # GET HOURLY POWER DEMAND
    # -----------------------------------------------------

    power_demand = result.get(
        "power_demand_by_hour",
        [],
    )

    # Make sure we have numeric values.
    power_demand = [
        float(value)
        for value in power_demand
    ]

    # -----------------------------------------------------
    # CALCULATE ENERGY
    # -----------------------------------------------------

    total_facility_energy_kwh = sum(
        power_demand
    )

    # -----------------------------------------------------
    # CALCULATE PEAK POWER
    # -----------------------------------------------------

    peak_facility_power_kw = max(
        power_demand,
        default=0.0,
    )

    # -----------------------------------------------------
    # PRINT REPORT
    # -----------------------------------------------------

    print()

    print("=" * 80)
    print("POWEROS REALISTIC VALIDATION")
    print("=" * 80)

    # -----------------------------------------------------
    # SYSTEM
    # -----------------------------------------------------

    print()

    print("SYSTEM")
    print("-" * 40)

    print(
        f"Status: "
        f"{state_analysis.get('status', 'UNKNOWN')}"
    )

    print(
        f"Bottleneck: "
        f"{state_analysis.get('primary_bottleneck', 'NONE')}"
    )

    print(
        f"Power pressure: "
        f"{state_analysis.get('power_pressure_percent', 0.0)}%"
    )

    print(
        f"Power headroom: "
        f"{state_analysis.get('power_headroom_kw', 0.0)} kW"
    )

    # -----------------------------------------------------
    # OPTIMIZATION
    # -----------------------------------------------------

    print()

    print("OPTIMIZATION")
    print("-" * 40)

    print(
        f"Total workloads: "
        f"{optimization.get('total_count', 0)}"
    )

    print(
        f"Scheduled: "
        f"{optimization.get('scheduled_count', 0)}"
    )

    print(
        f"Unscheduled: "
        f"{optimization.get('unscheduled_count', 0)}"
    )

    print(
        f"Success rate: "
        f"{optimization.get('success_rate_percent', 0.0)}%"
    )

    # -----------------------------------------------------
    # DECISIONS
    # -----------------------------------------------------

    print()

    print("DECISIONS")
    print("-" * 40)

    print(
        f"RUN: "
        f"{decisions.get('run', 0)}"
    )

    print(
        f"SHIFT: "
        f"{decisions.get('shift', 0)}"
    )

    print(
        f"Deadline protection: "
        f"{decisions.get('protect_deadline', 0)}"
    )

    # -----------------------------------------------------
    # POWER
    # -----------------------------------------------------

    print()

    print("POWER")
    print("-" * 40)

    print(
        f"Peak facility power: "
        f"{peak_facility_power_kw:.2f} kW"
    )

    print(
        f"Total facility energy: "
        f"{total_facility_energy_kwh:.2f} kWh"
    )

    # -----------------------------------------------------
    # RAW POWER SUMMARY
    # -----------------------------------------------------

    print()

    print("POWER SUMMARY")
    print("-" * 40)

    print(
        f"Total IT power: "
        f"{power_summary.get('total_it_power_kw', 0.0)} kW"
    )

    print(
        f"Cooling overhead: "
        f"{power_summary.get('cooling_overhead_kw', 0.0)} kW"
    )

    # -----------------------------------------------------
    # FINAL STATUS
    # -----------------------------------------------------

    print()

    print("=" * 80)
    print("POWEROS REALISTIC VALIDATION COMPLETED")
    print("=" * 80)


# =========================================================
# MAIN
# =========================================================

def main():

    result = run_realistic_validation()

    print_validation_result(
        result
    )


# =========================================================
# DIRECT EXECUTION
# =========================================================

if __name__ == "__main__":
    main()