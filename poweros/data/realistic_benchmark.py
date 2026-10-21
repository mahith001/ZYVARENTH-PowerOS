from typing import Dict, List

from poweros.data.realistic_validation import (
    build_realistic_state,
    create_realistic_prices,
    create_realistic_solar,
)

from poweros.core.orchestrator import (
    run_poweros,
)


# =========================================================
# BASELINE CALCULATION
# =========================================================

def calculate_baseline(
    state,
    electricity_prices: List[float],
) -> Dict:
    """
    Calculate a simple baseline where every workload
    starts immediately at hour 0.

    This represents a non-power-aware scheduling strategy.
    """

    gpu_power_kw = 0.70

    pue = state.pue

    total_gpu_hours = 0.0

    total_it_energy_kwh = 0.0

    total_workloads = len(
        state.workloads
    )

    completed_workloads = 0

    deadline_missed = 0

    # -----------------------------------------------------
    # Calculate workload energy
    # -----------------------------------------------------

    for workload in state.workloads:

        gpu_hours = (
            workload.gpu_required
            * workload.duration_hours
        )

        total_gpu_hours += gpu_hours

        it_energy = (
            gpu_hours
            * gpu_power_kw
        )

        total_it_energy_kwh += (
            it_energy
        )

        # Baseline starts at hour 0.
        completion_hour = (
            workload.duration_hours
        )

        if (
            completion_hour
            <= workload.deadline_hour
        ):
            completed_workloads += 1
        else:
            deadline_missed += 1

    # -----------------------------------------------------
    # Facility energy
    # -----------------------------------------------------

    total_facility_energy_kwh = (
        total_it_energy_kwh
        * pue
    )

    # -----------------------------------------------------
    # Baseline peak
    #
    # All workloads start together.
    # -----------------------------------------------------

    total_gpu_demand = sum(
        workload.gpu_required
        for workload in state.workloads
    )

    baseline_it_peak_kw = (
        total_gpu_demand
        * gpu_power_kw
    )

    baseline_facility_peak_kw = (
        baseline_it_peak_kw
        * pue
    )

    # -----------------------------------------------------
    # Baseline electricity cost
    #
    # All workloads begin at hour 0.
    # -----------------------------------------------------

    starting_price = (
        electricity_prices[0]
        if electricity_prices
        else 0.0
    )

    baseline_cost = (
        total_facility_energy_kwh
        * starting_price
    )

    deadline_success_rate = (
        completed_workloads
        / total_workloads
        * 100
        if total_workloads > 0
        else 0.0
    )

    return {
        "total_workloads": total_workloads,

        "completed_workloads": (
            completed_workloads
        ),

        "deadline_missed": (
            deadline_missed
        ),

        "deadline_success_rate_percent": (
            deadline_success_rate
        ),

        "total_gpu_hours": (
            total_gpu_hours
        ),

        "total_it_energy_kwh": (
            total_it_energy_kwh
        ),

        "total_facility_energy_kwh": (
            total_facility_energy_kwh
        ),

        "peak_facility_power_kw": (
            baseline_facility_peak_kw
        ),

        "estimated_electricity_cost": (
            baseline_cost
        ),

        "starting_electricity_price": (
            starting_price
        ),
    }


# =========================================================
# POWEROS METRICS
# =========================================================

def calculate_poweros_metrics(
    result: Dict,
) -> Dict:
    """
    Extract measurable metrics from PowerOS.
    """

    optimization = result.get(
        "optimization_summary",
        {},
    )

    decisions = result.get(
        "decision_summary",
        {},
    )

    power_demand = result.get(
        "power_demand_by_hour",
        [],
    )

    # -----------------------------------------------------
    # Normalize power demand
    # -----------------------------------------------------

    power_demand = [
        float(value)
        for value in power_demand
    ]

    total_facility_energy_kwh = sum(
        power_demand
    )

    peak_facility_power_kw = max(
        power_demand,
        default=0.0,
    )

    total_workloads = optimization.get(
        "total_count",
        optimization.get(
            "total_workloads",
            0,
        ),
    )

    scheduled_workloads = optimization.get(
        "scheduled_count",
        optimization.get(
            "scheduled_workloads",
            0,
        ),
    )

    unscheduled_workloads = optimization.get(
        "unscheduled_count",
        optimization.get(
            "unscheduled_workloads",
            0,
        ),
    )

    success_rate = optimization.get(
        "success_rate_percent",
        0.0,
    )

    run_decisions = decisions.get(
        "run",
        0,
    )

    shift_decisions = decisions.get(
        "shift",
        0,
    )

    deadline_protection = decisions.get(
        "protect_deadline",
        0,
    )

    # -----------------------------------------------------
    # Peak reduction cannot be calculated until
    # baseline is supplied.
    # -----------------------------------------------------

    return {
        "total_workloads": (
            total_workloads
        ),

        "scheduled_workloads": (
            scheduled_workloads
        ),

        "unscheduled_workloads": (
            unscheduled_workloads
        ),

        "success_rate_percent": (
            success_rate
        ),

        "total_facility_energy_kwh": (
            total_facility_energy_kwh
        ),

        "peak_facility_power_kw": (
            peak_facility_power_kw
        ),

        "run_decisions": (
            run_decisions
        ),

        "shift_decisions": (
            shift_decisions
        ),

        "deadline_protection_decisions": (
            deadline_protection
        ),
    }


# =========================================================
# COMPARE
# =========================================================

def compare_results(
    baseline: Dict,
    poweros: Dict,
) -> Dict:
    """
    Compare baseline and PowerOS.
    """

    baseline_peak = (
        baseline[
            "peak_facility_power_kw"
        ]
    )

    poweros_peak = (
        poweros[
            "peak_facility_power_kw"
        ]
    )

    if baseline_peak > 0:

        peak_reduction_percent = (
            (
                baseline_peak
                - poweros_peak
            )
            / baseline_peak
            * 100
        )

    else:

        peak_reduction_percent = 0.0

    baseline_energy = (
        baseline[
            "total_facility_energy_kwh"
        ]
    )

    poweros_energy = (
        poweros[
            "total_facility_energy_kwh"
        ]
    )

    if baseline_energy > 0:

        energy_difference_percent = (
            (
                baseline_energy
                - poweros_energy
            )
            / baseline_energy
            * 100
        )

    else:

        energy_difference_percent = 0.0

    return {
        "baseline_peak_kw": (
            baseline_peak
        ),

        "poweros_peak_kw": (
            poweros_peak
        ),

        "peak_reduction_percent": (
            peak_reduction_percent
        ),

        "baseline_energy_kwh": (
            baseline_energy
        ),

        "poweros_energy_kwh": (
            poweros_energy
        ),

        "energy_difference_percent": (
            energy_difference_percent
        ),

        "baseline_deadline_success": (
            baseline[
                "deadline_success_rate_percent"
            ]
        ),

        "poweros_success_rate": (
            poweros[
                "success_rate_percent"
            ]
        ),

        "shift_decisions": (
            poweros[
                "shift_decisions"
            ]
        ),

        "deadline_protection": (
            poweros[
                "deadline_protection_decisions"
            ]
        ),
    }


# =========================================================
# PRINT REPORT
# =========================================================

def print_benchmark_report(
    baseline: Dict,
    poweros: Dict,
    comparison: Dict,
) -> None:

    print()

    print("=" * 80)
    print("ZYVARENTH POWEROS")
    print("REALISTIC BASELINE VS POWEROS BENCHMARK")
    print("=" * 80)

    # -----------------------------------------------------
    # WORKLOADS
    # -----------------------------------------------------

    print()

    print("WORKLOADS")
    print("-" * 80)

    print(
        f"Total workloads: "
        f"{baseline['total_workloads']}"
    )

    print(
        f"PowerOS scheduled: "
        f"{poweros['scheduled_workloads']}"
    )

    print(
        f"PowerOS unscheduled: "
        f"{poweros['unscheduled_workloads']}"
    )

    # -----------------------------------------------------
    # POWER
    # -----------------------------------------------------

    print()

    print("POWER")
    print("-" * 80)

    print(
        f"Baseline peak: "
        f"{comparison['baseline_peak_kw']:.2f} kW"
    )

    print(
        f"PowerOS peak: "
        f"{comparison['poweros_peak_kw']:.2f} kW"
    )

    print(
        f"Peak reduction: "
        f"{comparison['peak_reduction_percent']:.2f}%"
    )

    # -----------------------------------------------------
    # ENERGY
    # -----------------------------------------------------

    print()

    print("ENERGY")
    print("-" * 80)

    print(
        f"Baseline energy: "
        f"{comparison['baseline_energy_kwh']:.2f} kWh"
    )

    print(
        f"PowerOS energy: "
        f"{comparison['poweros_energy_kwh']:.2f} kWh"
    )

    print(
        f"Energy difference: "
        f"{comparison['energy_difference_percent']:.2f}%"
    )

    # -----------------------------------------------------
    # DEADLINES
    # -----------------------------------------------------

    print()

    print("DEADLINES")
    print("-" * 80)

    print(
        f"Baseline deadline success: "
        f"{comparison['baseline_deadline_success']:.2f}%"
    )

    print(
        f"PowerOS optimization success: "
        f"{comparison['poweros_success_rate']:.2f}%"
    )

    # -----------------------------------------------------
    # DECISIONS
    # -----------------------------------------------------

    print()

    print("POWEROS DECISIONS")
    print("-" * 80)

    print(
        f"SHIFT decisions: "
        f"{comparison['shift_decisions']}"
    )

    print(
        f"Deadline protection: "
        f"{comparison['deadline_protection']}"
    )

    # -----------------------------------------------------
    # COST
    # -----------------------------------------------------

    print()

    print("BASELINE COST")
    print("-" * 80)

    print(
        f"Baseline estimated electricity cost: "
        f"₹{baseline['estimated_electricity_cost']:.2f}"
    )

    # -----------------------------------------------------
    # FINAL
    # -----------------------------------------------------

    print()

    print("=" * 80)
    print("POWEROS REALISTIC BENCHMARK COMPLETED")
    print("=" * 80)


# =========================================================
# MAIN
# =========================================================

def main():

    # -----------------------------------------------------
    # BUILD STATE
    # -----------------------------------------------------

    state = build_realistic_state()

    prices = create_realistic_prices()

    solar = create_realistic_solar()

    # -----------------------------------------------------
    # BASELINE
    # -----------------------------------------------------

    baseline = calculate_baseline(
        state=state,
        electricity_prices=prices,
    )

    # -----------------------------------------------------
    # POWEROS
    # -----------------------------------------------------

    result = run_poweros(
        state=state,
        horizon_hours=24,
        electricity_prices=prices,
        solar_power_by_hour=solar,
        battery_capacity_kwh=100,
        initial_battery_soc_percent=80,
        battery_max_discharge_kw=10,
    )

    poweros = calculate_poweros_metrics(
        result
    )

    # -----------------------------------------------------
    # COMPARISON
    # -----------------------------------------------------

    comparison = compare_results(
        baseline=baseline,
        poweros=poweros,
    )

    # -----------------------------------------------------
    # REPORT
    # -----------------------------------------------------

    print_benchmark_report(
        baseline=baseline,
        poweros=poweros,
        comparison=comparison,
    )


if __name__ == "__main__":
    main()