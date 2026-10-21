from poweros.data.fair_baseline import (
    create_realistic_state,
    create_realistic_prices,
    create_realistic_solar,
    schedule_earliest_start,
    calculate_baseline_metrics,
)

from poweros.core.orchestrator import run_poweros


# ============================================================
# POWEROS METRICS
# ============================================================

def calculate_poweros_metrics(result):
    """Extract comparable metrics from PowerOS."""

    demand = result.get(
        "power_demand_by_hour",
        [],
    )

    demand = [
        float(value)
        for value in demand
    ]

    total_energy_kwh = sum(demand)

    peak_power_kw = max(
        demand,
        default=0.0,
    )

    optimization = result.get(
        "optimization_summary",
        {},
    )

    decision_summary = result.get(
        "decision_summary",
        {},
    )

    battery = result.get(
        "battery_dispatch",
        {},
    )

    scheduled_count = optimization.get(
        "scheduled_count",
        0,
    )

    total_count = optimization.get(
        "total_count",
        len(result.get("schedule", {}).get("scheduled", [])),
    )

    if total_count == 0:
        total_count = scheduled_count

    deadline_success = (
        scheduled_count
        / total_count
        * 100
        if total_count > 0
        else 0.0
    )

    solar_used = battery.get(
        "total_solar_energy_kwh",
        0.0,
    )

    battery_used = battery.get(
        "total_battery_energy_kwh",
        0.0,
    )

    energy_cost = battery.get(
        "total_cost",
        0.0,
    )

    return {
        "total_workloads": total_count,
        "scheduled_count": scheduled_count,
        "unscheduled_count": (
            total_count - scheduled_count
        ),
        "total_energy_kwh": total_energy_kwh,
        "peak_power_kw": peak_power_kw,
        "deadline_success_percent": deadline_success,
        "estimated_cost": energy_cost,
        "solar_used_kwh": solar_used,
        "battery_used_kwh": battery_used,
        "shift_decisions": decision_summary.get(
            "shift_decisions",
            decision_summary.get("shift", 0),
        ),
        "deadline_protection_decisions":
            decision_summary.get(
                "protect_deadline_decisions",
                decision_summary.get(
                    "protect_deadline",
                    0,
                ),
            ),
    }


# ============================================================
# BASELINE 1
# ============================================================

def calculate_baseline_1(
    state,
    electricity_prices,
):
    """
    Baseline 1:
    All workloads are assumed to run immediately.

    This is intentionally simple and is used only
    as a reference point.
    """

    total_it_energy = 0.0

    total_power_now = 0.0

    for workload in state.workloads:

        gpu_power = (
            workload.gpu_required
            * 0.70
        )

        total_it_energy += (
            gpu_power
            * workload.duration_hours
        )

        total_power_now += gpu_power

    facility_energy = (
        total_it_energy
        * state.pue
    )

    peak_power = (
        total_power_now
        * state.pue
    )

    # Baseline 1 uses hour-0 electricity price.
    price = (
        electricity_prices[0]
        if electricity_prices
        else 0.0
    )

    estimated_cost = (
        facility_energy
        * price
    )

    deadline_met = 0

    for workload in state.workloads:

        if (
            workload.duration_hours
            <= workload.deadline_hour
        ):
            deadline_met += 1

    total_workloads = len(
        state.workloads
    )

    deadline_success = (
        deadline_met
        / total_workloads
        * 100
        if total_workloads > 0
        else 0.0
    )

    return {
        "total_workloads":
            total_workloads,

        "scheduled_count":
            total_workloads,

        "unscheduled_count":
            0,

        "total_energy_kwh":
            facility_energy,

        "peak_power_kw":
            peak_power,

        "deadline_success_percent":
            deadline_success,

        "estimated_cost":
            estimated_cost,

        "solar_used_kwh":
            0.0,

        "battery_used_kwh":
            0.0,

        "shift_decisions":
            0,

        "deadline_protection_decisions":
            0,
    }


# ============================================================
# RUN POWEROS
# ============================================================

def run_poweros_benchmark(
    state,
    prices,
    solar,
):

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


# ============================================================
# THREE-WAY COMPARISON
# ============================================================

def calculate_comparison(
    baseline_1,
    baseline_2,
    poweros,
):

    return {
        "baseline_1": baseline_1,
        "baseline_2": baseline_2,
        "poweros": poweros,
    }


# ============================================================
# REPORT
# ============================================================

def print_three_way_report(
    comparison,
):

    baseline_1 = comparison[
        "baseline_1"
    ]

    baseline_2 = comparison[
        "baseline_2"
    ]

    poweros = comparison[
        "poweros"
    ]

    print()

    print("=" * 90)
    print("ZYVARENTH POWEROS")
    print("THREE-WAY REALISTIC BENCHMARK")
    print("=" * 90)

    print()

    print(
        "                    "
        "BASELINE 1    "
        "BASELINE 2    "
        "POWEROS"
    )

    print("-" * 90)

    print(
        f"{'Workloads':22}"
        f"{baseline_1['total_workloads']:>13}"
        f"{baseline_2['total_workloads']:>13}"
        f"{poweros['total_workloads']:>13}"
    )

    print(
        f"{'Scheduled':22}"
        f"{baseline_1['scheduled_count']:>13}"
        f"{baseline_2['scheduled_count']:>13}"
        f"{poweros['scheduled_count']:>13}"
    )

    print(
        f"{'Unscheduled':22}"
        f"{baseline_1['unscheduled_count']:>13}"
        f"{baseline_2['unscheduled_count']:>13}"
        f"{poweros['unscheduled_count']:>13}"
    )

    print()

    print(
        f"{'Peak power (kW)':22}"
        f"{baseline_1['peak_power_kw']:>13.2f}"
        f"{baseline_2['peak_power_kw']:>13.2f}"
        f"{poweros['peak_power_kw']:>13.2f}"
    )

    print(
        f"{'Energy (kWh)':22}"
        f"{baseline_1['total_energy_kwh']:>13.2f}"
        f"{baseline_2['total_energy_kwh']:>13.2f}"
        f"{poweros['total_energy_kwh']:>13.2f}"
    )

    print(
        f"{'Cost (₹)':22}"
        f"{baseline_1['estimated_cost']:>13.2f}"
        f"{baseline_2['estimated_cost']:>13.2f}"
        f"{poweros['estimated_cost']:>13.2f}"
    )

    print(
        f"{'Deadline success (%)':22}"
        f"{baseline_1['deadline_success_percent']:>13.2f}"
        f"{baseline_2['deadline_success_percent']:>13.2f}"
        f"{poweros['deadline_success_percent']:>13.2f}"
    )

    print()

    print(
        f"{'Solar used (kWh)':22}"
        f"{baseline_1['solar_used_kwh']:>13.2f}"
        f"{baseline_2['solar_used_kwh']:>13.2f}"
        f"{poweros['solar_used_kwh']:>13.2f}"
    )

    print(
        f"{'Battery used (kWh)':22}"
        f"{baseline_1['battery_used_kwh']:>13.2f}"
        f"{baseline_2['battery_used_kwh']:>13.2f}"
        f"{poweros['battery_used_kwh']:>13.2f}"
    )

    print()

    print(
        f"{'SHIFT decisions':22}"
        f"{baseline_1['shift_decisions']:>13}"
        f"{baseline_2['shift_decisions']:>13}"
        f"{poweros['shift_decisions']:>13}"
    )

    print(
        f"{'Deadline protection':22}"
        f"{baseline_1['deadline_protection_decisions']:>13}"
        f"{baseline_2['deadline_protection_decisions']:>13}"
        f"{poweros['deadline_protection_decisions']:>13}"
    )

    print()

    print("=" * 90)

    print(
        "THREE-WAY BENCHMARK COMPLETED"
    )

    print("=" * 90)


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # SAME DATA FOR ALL THREE SYSTEMS
    # --------------------------------------------------------

    state = create_realistic_state()

    prices = create_realistic_prices()

    solar = create_realistic_solar()

    # --------------------------------------------------------
    # BASELINE 1
    # --------------------------------------------------------

    baseline_1 = calculate_baseline_1(
        state=state,
        electricity_prices=prices,
    )

    # --------------------------------------------------------
    # BASELINE 2
    # --------------------------------------------------------

    baseline_2_schedule = (
        schedule_earliest_start(
            state=state,
            horizon_hours=24,
        )
    )

    baseline_2 = (
        calculate_baseline_metrics(
            state=state,
            schedule=baseline_2_schedule,
            electricity_prices=prices,
        )
    )

    # Add common fields
    baseline_2[
        "shift_decisions"
    ] = 0

    baseline_2[
        "deadline_protection_decisions"
    ] = 0

    # --------------------------------------------------------
    # POWEROS
    # --------------------------------------------------------

    poweros_result = (
        run_poweros_benchmark(
            state=state,
            prices=prices,
            solar=solar,
        )
    )

    poweros = (
        calculate_poweros_metrics(
            poweros_result
        )
    )

    # --------------------------------------------------------
    # COMPARISON
    # --------------------------------------------------------

    comparison = (
        calculate_comparison(
            baseline_1=baseline_1,
            baseline_2=baseline_2,
            poweros=poweros,
        )
    )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    print_three_way_report(
        comparison
    )

    return comparison


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()