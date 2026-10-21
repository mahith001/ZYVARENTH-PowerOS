from poweros.demo import (
    create_demo_state,
    create_hourly_prices,
    create_hourly_solar,
)

from poweros.core.orchestrator import (
    run_poweros,
)


# ============================================================
# BASELINE
# ============================================================

def calculate_baseline(
    state,
    hourly_prices,
):
    """
    Calculate a simple baseline where all workloads
    are considered to run as soon as possible.

    This is intentionally simple for V1 benchmarking.
    """

    total_it_energy_kwh = 0.0

    for workload in state.workloads:

        gpu_power = (
            workload.gpu_required
            * 0.7
        )

        total_it_energy_kwh += (
            gpu_power
            * workload.duration_hours
        )

    total_facility_energy_kwh = (
        total_it_energy_kwh
        * state.pue
    )

    average_price = (
        sum(hourly_prices)
        / len(hourly_prices)
    )

    baseline_cost = (
        total_facility_energy_kwh
        * average_price
    )

    return {
        "it_energy_kwh": total_it_energy_kwh,
        "facility_energy_kwh": (
            total_facility_energy_kwh
        ),
        "estimated_cost": baseline_cost,
    }


# ============================================================
# POWEROS METRICS
# ============================================================

def calculate_poweros_metrics(
    result,
):
    battery = result[
        "battery_dispatch"
    ]

    optimization = result[
        "optimization_summary"
    ]

    demand = result[
        "power_demand_by_hour"
    ]

    total_facility_energy = sum(
        demand
    )

    peak_power = max(
        demand,
        default=0.0,
    )

    # PowerOS already provides the hourly facility demand.
    # Do not depend on a legacy "power_summary['it_power_kw']" key.
    # The current orchestrator does not require that legacy field.

    # Current PowerOS optimizer summary uses:
    # scheduled_count and total_count.
    # Keep a small compatibility fallback for older summaries.
    scheduled = optimization.get(
        "scheduled_count",
        optimization.get("scheduled_workloads", 0),
    )

    total = optimization.get(
        "total_count",
        optimization.get("total_workloads", 0),
    )

    completion_rate = (
        scheduled / total * 100
        if total > 0
        else 0
    )

    return {
        "facility_energy_kwh": (
            total_facility_energy
        ),

        "peak_power_kw": (
            peak_power
        ),

        "grid_energy_kwh": (
            battery[
                "total_grid_energy_kwh"
            ]
        ),

        "solar_energy_kwh": (
            battery[
                "total_solar_energy_kwh"
            ]
        ),

        "battery_energy_kwh": (
            battery[
                "total_battery_energy_kwh"
            ]
        ),

        "energy_cost": (
            battery[
                "total_cost"
            ]
        ),

        "final_battery_soc": (
            battery[
                "final_battery_soc_percent"
            ]
        ),

        "completion_rate": (
            completion_rate
        ),

    }


# ============================================================
# IMPROVEMENT CALCULATION
# ============================================================

def calculate_improvement(
    baseline,
    poweros,
):
    baseline_energy = (
        baseline[
            "facility_energy_kwh"
        ]
    )

    poweros_energy = (
        poweros[
            "facility_energy_kwh"
        ]
    )

    baseline_cost = (
        baseline[
            "estimated_cost"
        ]
    )

    poweros_cost = (
        poweros[
            "energy_cost"
        ]
    )

    energy_reduction = 0.0

    if baseline_energy > 0:

        energy_reduction = (
            (
                baseline_energy
                - poweros_energy
            )
            / baseline_energy
        ) * 100

    cost_reduction = 0.0

    if baseline_cost > 0:

        cost_reduction = (
            (
                baseline_cost
                - poweros_cost
            )
            / baseline_cost
        ) * 100

    return {
        "energy_reduction_percent": (
            energy_reduction
        ),

        "cost_reduction_percent": (
            cost_reduction
        ),
    }


# ============================================================
# SCENARIO
# ============================================================

def run_scenario(
    name,
    state,
    hourly_prices,
    hourly_solar,
):

    result = run_poweros(

        state=state,

        horizon_hours=24,

        electricity_prices=(
            hourly_prices
        ),

        solar_power_by_hour=(
            hourly_solar
        ),

        battery_capacity_kwh=100,

        initial_battery_soc_percent=80,

        battery_max_discharge_kw=10,
    )

    baseline = calculate_baseline(
        state,
        hourly_prices,
    )

    poweros = calculate_poweros_metrics(
        result
    )

    improvement = calculate_improvement(
        baseline,
        poweros,
    )

    return {
        "name": name,
        "baseline": baseline,
        "poweros": poweros,
        "improvement": improvement,
    }


# ============================================================
# CREATE SCENARIOS
# ============================================================

def create_scenarios():

    prices = create_hourly_prices()

    solar = create_hourly_solar()

    # --------------------------------------------------------
    # BASELINE
    # --------------------------------------------------------

    normal = create_demo_state()

    # --------------------------------------------------------
    # LOW POWER
    # --------------------------------------------------------

    low_power = create_demo_state()

    low_power.power.available_power_kw = 25

    # --------------------------------------------------------
    # HIGH DEMAND
    # --------------------------------------------------------

    high_demand = create_demo_state()

    for workload in high_demand.workloads:

        workload.gpu_required = int(
            workload.gpu_required * 1.5
        )

    # --------------------------------------------------------
    # HIGH SOLAR
    # --------------------------------------------------------

    high_solar = create_demo_state()

    high_solar.power.solar_power_kw = 40

    solar_high = [
        value * 1.5
        for value in solar
    ]

    # --------------------------------------------------------
    # TIGHT DEADLINES
    # --------------------------------------------------------

    tight_deadlines = create_demo_state()

    for workload in (
        tight_deadlines.workloads
    ):

        if workload.priority == "HIGH":

            workload.deadline_hour = 6

        else:

            workload.deadline_hour = 10

    return [
        (
            "NORMAL",
            normal,
            prices,
            solar,
        ),

        (
            "LOW POWER",
            low_power,
            prices,
            solar,
        ),

        (
            "HIGH DEMAND",
            high_demand,
            prices,
            solar,
        ),

        (
            "HIGH SOLAR",
            high_solar,
            prices,
            solar_high,
        ),

        (
            "TIGHT DEADLINES",
            tight_deadlines,
            prices,
            solar,
        ),
    ]


# ============================================================
# RUN ALL
# ============================================================

def run_benchmark():

    scenarios = create_scenarios()

    results = []

    for (
        name,
        state,
        prices,
        solar,
    ) in scenarios:

        result = run_scenario(
            name,
            state,
            prices,
            solar,
        )

        results.append(
            result
        )

    return results


# ============================================================
# REPORT
# ============================================================

def print_report(
    results,
):

    print()
    print("=" * 80)
    print("ZYVARENTH POWEROS")
    print("BENCHMARK V2")
    print("=" * 80)

    for result in results:

        baseline = result[
            "baseline"
        ]

        poweros = result[
            "poweros"
        ]

        improvement = result[
            "improvement"
        ]

        print()
        print("-" * 80)

        print(
            f"SCENARIO: "
            f"{result['name']}"
        )

        print()

        print(
            "BASELINE"
        )

        print(
            f"Facility energy: "
            f"{baseline['facility_energy_kwh']:.2f} kWh"
        )

        print(
            f"Estimated cost: "
            f"₹{baseline['estimated_cost']:.2f}"
        )

        print()

        print(
            "POWEROS"
        )

        print(
            f"Facility energy: "
            f"{poweros['facility_energy_kwh']:.2f} kWh"
        )

        print(
            f"Peak power: "
            f"{poweros['peak_power_kw']:.2f} kW"
        )

        print(
            f"Grid energy: "
            f"{poweros['grid_energy_kwh']:.2f} kWh"
        )

        print(
            f"Solar energy: "
            f"{poweros['solar_energy_kwh']:.2f} kWh"
        )

        print(
            f"Battery energy: "
            f"{poweros['battery_energy_kwh']:.2f} kWh"
        )

        print(
            f"Energy cost: "
            f"₹{poweros['energy_cost']:.2f}"
        )

        print(
            f"Final battery SOC: "
            f"{poweros['final_battery_soc']:.1f}%"
        )

        print(
            f"Workload completion: "
            f"{poweros['completion_rate']:.1f}%"
        )

        print()

        print(
            "IMPACT"
        )

        print(
            f"Energy reduction: "
            f"{improvement['energy_reduction_percent']:.1f}%"
        )

        print(
            f"Cost reduction: "
            f"{improvement['cost_reduction_percent']:.1f}%"
        )

    print()
    print("=" * 80)

    print(
        "POWEROS BENCHMARK V2 COMPLETED"
    )

    print("=" * 80)
    print()


# ============================================================
# MAIN
# ============================================================

def main():

    results = run_benchmark()

    print_report(
        results
    )


if __name__ == "__main__":

    main()