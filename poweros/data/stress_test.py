"""
ZYVARENTH PowerOS
Stress Test Suite

Tests PowerOS under difficult operating conditions:

1. 20% power reduction
2. 50% electricity price increase
3. 50% solar reduction
4. 30% GPU demand increase
5. Tight workload deadlines
"""

from copy import deepcopy

from poweros.data.fair_baseline import (
    create_realistic_state,
    create_realistic_prices,
    create_realistic_solar,
    schedule_earliest_start,
    calculate_baseline_metrics,
)

from poweros.core.orchestrator import run_poweros


GPU_POWER_KW = 0.7
PUE = 1.30


# ============================================================
# HELPERS
# ============================================================

def get_value(data, *keys, default=0):
    """Safely retrieve the first available key."""
    if not isinstance(data, dict):
        return default

    for key in keys:
        if key in data:
            return data[key]

    return default


def calculate_schedule_deadline_success(schedule, workloads):
    """
    Calculate true deadline success using actual finish times.
    """
    workload_map = {
        workload.workload_id: workload
        for workload in workloads
    }

    if not workloads:
        return 100.0

    successful = 0

    for item in schedule:
        workload_id = item.get("workload_id")

        if workload_id not in workload_map:
            continue

        workload = workload_map[workload_id]

        finish_hour = item.get("finish_hour")

        if finish_hour is not None and finish_hour <= workload.deadline_hour:
            successful += 1

    return (successful / len(workloads)) * 100.0


def calculate_poweros_metrics(result, state):
    """
    Convert PowerOS output into benchmark metrics.
    """

    schedule = result.get("schedule", {})
    scheduled = schedule.get("scheduled", [])
    unscheduled = schedule.get("unscheduled", [])

    total_workloads = len(state.workloads)

    # --------------------------------------------------------
    # TRUE DEADLINE SUCCESS
    # --------------------------------------------------------

    deadline_success = calculate_schedule_deadline_success(
        scheduled,
        state.workloads,
    )

    # --------------------------------------------------------
    # POWER
    # --------------------------------------------------------

    power_summary = result.get("power_summary", {})

    peak_power = get_value(
        power_summary,
        "peak_facility_power_kw",
        "peak_power_kw",
        default=0.0,
    )

    total_energy = sum(
        result.get("power_demand_by_hour", [])
    )

    # --------------------------------------------------------
    # COST
    # --------------------------------------------------------

    battery_dispatch = result.get("battery_dispatch", {})

    total_cost = get_value(
        battery_dispatch,
        "total_cost",
        "total_energy_cost",
        "cost",
        default=0.0,
    )

    # --------------------------------------------------------
    # ENERGY RESOURCES
    # --------------------------------------------------------

    solar_used = get_value(
        battery_dispatch,
        "solar_energy_used_kwh",
        "solar_used_kwh",
        "solar_used",
        default=0.0,
    )

    battery_used = get_value(
        battery_dispatch,
        "battery_energy_used_kwh",
        "battery_used_kwh",
        "battery_used",
        default=0.0,
    )

    # --------------------------------------------------------
    # DECISIONS
    # --------------------------------------------------------

    decision_summary = result.get("decision_summary", {})

    shift_decisions = get_value(
        decision_summary,
        "shift_decisions",
        "shift",
        default=0,
    )

    deadline_protection = get_value(
        decision_summary,
        "protect_deadline_decisions",
        "protect_deadline",
        default=0,
    )

    return {
        "total": total_workloads,
        "scheduled": len(scheduled),
        "unscheduled": len(unscheduled),
        "peak_power": peak_power,
        "energy": total_energy,
        "cost": total_cost,
        "deadline_success": deadline_success,
        "solar_used": solar_used,
        "battery_used": battery_used,
        "shift_decisions": shift_decisions,
        "deadline_protection": deadline_protection,
    }


def calculate_baseline_metrics_safe(
    state,
    prices,
    baseline_schedule,
):
    """
    Safely calculate Baseline 2 metrics.
    """

    metrics = calculate_baseline_metrics(
        state,
        baseline_schedule,
        prices,
    )

    return {
        "total": len(state.workloads),
        "scheduled": len(baseline_schedule),
        "unscheduled": max(
            0,
            len(state.workloads) - len(baseline_schedule),
        ),
        "peak_power": get_value(
            metrics,
            "peak_facility_power_kw",
            "peak_power_kw",
            default=0.0,
        ),
        "energy": get_value(
            metrics,
            "total_facility_energy_kwh",
            "energy_kwh",
            "total_energy_kwh",
            default=0.0,
        ),
        "cost": get_value(
            metrics,
            "estimated_cost",
            "cost",
            "electricity_cost",
            default=0.0,
        ),
        "deadline_success": get_value(
            metrics,
            "deadline_success_percent",
            "deadline_success",
            default=0.0,
        ),
        "solar_used": 0.0,
        "battery_used": 0.0,
        "shift_decisions": 0,
        "deadline_protection": 0,
    }


# ============================================================
# SCENARIO MODIFIERS
# ============================================================

def scenario_power_reduction(state):
    """
    Reduce available power by 20%.
    """

    modified = deepcopy(state)

    modified.power.available_power_kw *= 0.80

    return modified


def scenario_price_spike(prices):
    """
    Increase electricity prices by 50%.
    """

    return [
        price * 1.50
        for price in prices
    ]


def scenario_solar_reduction(solar):
    """
    Reduce solar generation by 50%.
    """

    return [
        value * 0.50
        for value in solar
    ]


def scenario_gpu_demand_increase(state):
    """
    Increase every workload GPU requirement by 30%.
    """

    modified = deepcopy(state)

    for workload in modified.workloads:
        workload.gpu_required = max(
            1,
            int(round(workload.gpu_required * 1.30)),
        )

    return modified


def scenario_tight_deadlines(state):
    """
    Tighten workload deadlines.

    Deadlines are reduced while ensuring they remain
    non-negative.
    """

    modified = deepcopy(state)

    for workload in modified.workloads:

        # Move deadlines closer by 3 hours.
        workload.deadline_hour = max(
            1,
            workload.deadline_hour - 3,
        )

    return modified


# ============================================================
# RUN ONE SCENARIO
# ============================================================

def run_scenario(
    name,
    state,
    prices,
    solar,
):
    """
    Run Baseline 2 and PowerOS on the same scenario.
    """

    print()
    print("=" * 90)
    print(f"SCENARIO: {name}")
    print("=" * 90)

    # --------------------------------------------------------
    # BASELINE 2
    # --------------------------------------------------------

    baseline_schedule = schedule_earliest_start(
        state
    )

    baseline = calculate_baseline_metrics_safe(
        state,
        prices,
        baseline_schedule,
    )

    # --------------------------------------------------------
    # POWEROS
    # --------------------------------------------------------

    poweros_result = run_poweros(
        state=state,
        electricity_prices=prices,
        solar_power_by_hour=solar,
        battery_capacity_kwh=100.0,
        initial_battery_soc_percent=80.0,
        battery_max_discharge_kw=10.0,
        reserve_percent=15.0,
    )

    poweros = calculate_poweros_metrics(
        poweros_result,
        state,
    )

    # --------------------------------------------------------
    # PRINT RESULT
    # --------------------------------------------------------

    print()
    print(
        f"{'METRIC':<30}"
        f"{'BASELINE 2':>20}"
        f"{'POWEROS':>20}"
    )

    print("-" * 70)

    print(
        f"{'Scheduled':<30}"
        f"{baseline['scheduled']:>20}"
        f"{poweros['scheduled']:>20}"
    )

    print(
        f"{'Unscheduled':<30}"
        f"{baseline['unscheduled']:>20}"
        f"{poweros['unscheduled']:>20}"
    )

    print(
        f"{'Peak power (kW)':<30}"
        f"{baseline['peak_power']:>20.2f}"
        f"{poweros['peak_power']:>20.2f}"
    )

    print(
        f"{'Energy (kWh)':<30}"
        f"{baseline['energy']:>20.2f}"
        f"{poweros['energy']:>20.2f}"
    )

    print(
        f"{'Cost (₹)':<30}"
        f"{baseline['cost']:>20.2f}"
        f"{poweros['cost']:>20.2f}"
    )

    print(
        f"{'Deadline success (%)':<30}"
        f"{baseline['deadline_success']:>20.2f}"
        f"{poweros['deadline_success']:>20.2f}"
    )

    print(
        f"{'Solar used (kWh)':<30}"
        f"{baseline['solar_used']:>20.2f}"
        f"{poweros['solar_used']:>20.2f}"
    )

    print(
        f"{'Battery used (kWh)':<30}"
        f"{baseline['battery_used']:>20.2f}"
        f"{poweros['battery_used']:>20.2f}"
    )

    print(
        f"{'SHIFT decisions':<30}"
        f"{baseline['shift_decisions']:>20}"
        f"{poweros['shift_decisions']:>20}"
    )

    print(
        f"{'Deadline protection':<30}"
        f"{baseline['deadline_protection']:>20}"
        f"{poweros['deadline_protection']:>20}"
    )

    return {
        "scenario": name,
        "baseline": baseline,
        "poweros": poweros,
    }


# ============================================================
# MAIN STRESS TEST
# ============================================================

def main():

    print()
    print("=" * 90)
    print("ZYVARENTH POWEROS")
    print("STRESS TEST SUITE")
    print("=" * 90)

    base_state = create_realistic_state()
    base_prices = create_realistic_prices()
    base_solar = create_realistic_solar()

    results = []

    # ========================================================
    # TEST 1 — POWER REDUCTION
    # ========================================================

    state = scenario_power_reduction(
        base_state
    )

    results.append(
        run_scenario(
            "20% POWER REDUCTION",
            state,
            base_prices,
            base_solar,
        )
    )

    # ========================================================
    # TEST 2 — PRICE SPIKE
    # ========================================================

    prices = scenario_price_spike(
        base_prices
    )

    results.append(
        run_scenario(
            "50% ELECTRICITY PRICE SPIKE",
            deepcopy(base_state),
            prices,
            base_solar,
        )
    )

    # ========================================================
    # TEST 3 — SOLAR REDUCTION
    # ========================================================

    solar = scenario_solar_reduction(
        base_solar
    )

    results.append(
        run_scenario(
            "50% SOLAR REDUCTION",
            deepcopy(base_state),
            base_prices,
            solar,
        )
    )

    # ========================================================
    # TEST 4 — GPU DEMAND INCREASE
    # ========================================================

    state = scenario_gpu_demand_increase(
        base_state
    )

    results.append(
        run_scenario(
            "30% GPU DEMAND INCREASE",
            state,
            base_prices,
            base_solar,
        )
    )

    # ========================================================
    # TEST 5 — TIGHT DEADLINES
    # ========================================================

    state = scenario_tight_deadlines(
        base_state
    )

    results.append(
        run_scenario(
            "TIGHT DEADLINES",
            state,
            base_prices,
            base_solar,
        )
    )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()
    print("=" * 90)
    print("STRESS TEST SUMMARY")
    print("=" * 90)

    print()

    print(
        f"{'SCENARIO':<32}"
        f"{'BASELINE COST':>18}"
        f"{'POWEROS COST':>18}"
    )

    print("-" * 70)

    for result in results:

        name = result["scenario"]

        baseline_cost = result["baseline"]["cost"]
        poweros_cost = result["poweros"]["cost"]

        print(
            f"{name:<32}"
            f"₹{baseline_cost:>16.2f}"
            f"₹{poweros_cost:>16.2f}"
        )

    print()
    print("=" * 90)
    print("POWEROS STRESS TEST COMPLETED")
    print("=" * 90)
    print()


if __name__ == "__main__":
    main()