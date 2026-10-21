from poweros.demo import create_demo_state
from poweros.core.orchestrator import run_poweros


# ============================================================
# METRICS
# ============================================================

def get_peak_power(forecast):
    """
    Safely extract peak forecast power from the forecasting engine.

    Supports the possible key names used by PowerOS V1.
    """

    peak = forecast.get("peak", {})

    if isinstance(peak, dict):

        if "power_kw" in peak:
            return peak["power_kw"]

        if "peak_power_kw" in peak:
            return peak["peak_power_kw"]

        if "forecast_power_kw" in peak:
            return peak["forecast_power_kw"]

        if "power" in peak:
            return peak["power"]

    return 0.0


def get_peak_hour(forecast):
    """
    Safely extract the peak forecast hour.
    """

    peak = forecast.get("peak", {})

    if isinstance(peak, dict):

        if "hour" in peak:
            return peak["hour"]

        if "peak_hour" in peak:
            return peak["peak_hour"]

    return "N/A"


def calculate_metrics(result):

    optimization = result["optimization_summary"]
    forecast = result["forecast"]

    scheduled = optimization.get(
        "scheduled_workloads",
        0
    )

    unscheduled = optimization.get(
        "unscheduled_workloads",
        0
    )

    total = scheduled + unscheduled

    if total > 0:
        success_rate = (
            scheduled / total
        ) * 100

    else:
        success_rate = 0

    peak_power = get_peak_power(
        forecast
    )

    peak_hour = get_peak_hour(
        forecast
    )

    return {
        "scheduled": scheduled,
        "unscheduled": unscheduled,
        "success_rate": success_rate,
        "forecast_peak_power_kw": peak_power,
        "forecast_peak_hour": peak_hour,
    }


# ============================================================
# BENCHMARK CASE
# ============================================================

def run_benchmark_case(name, state):

    result = run_poweros(
        state=state,
        horizon_hours=24,
    )

    metrics = calculate_metrics(
        result
    )

    return {
        "name": name,
        **metrics,
    }


# ============================================================
# SCENARIO 1
# BASELINE
# ============================================================

def create_baseline_case():

    return create_demo_state()


# ============================================================
# SCENARIO 2
# LOW POWER
# ============================================================

def create_low_power_case():

    state = create_demo_state()

    state.power.available_power_kw = 25

    return state


# ============================================================
# SCENARIO 3
# HIGH DEMAND
# ============================================================

def create_high_demand_case():

    state = create_demo_state()

    for workload in state.workloads:

        workload.gpu_required = int(
            workload.gpu_required * 1.5
        )

    return state


# ============================================================
# SCENARIO 4
# TIGHT DEADLINES
# ============================================================

def create_tight_deadline_case():

    state = create_demo_state()

    for workload in state.workloads:

        if workload.priority == "HIGH":

            workload.deadline_hour = 6

        else:

            workload.deadline_hour = 10

    return state


# ============================================================
# SCENARIO 5
# HIGH SOLAR
# ============================================================

def create_high_solar_case():

    state = create_demo_state()

    state.power.solar_power_kw = 40

    return state


# ============================================================
# RUN ALL BENCHMARKS
# ============================================================

def run_all_benchmarks():

    cases = [

        (
            "BASELINE",
            create_baseline_case()
        ),

        (
            "LOW POWER",
            create_low_power_case()
        ),

        (
            "HIGH DEMAND",
            create_high_demand_case()
        ),

        (
            "TIGHT DEADLINES",
            create_tight_deadline_case()
        ),

        (
            "HIGH SOLAR",
            create_high_solar_case()
        ),
    ]

    results = []

    for name, state in cases:

        result = run_benchmark_case(
            name,
            state
        )

        results.append(
            result
        )

    return results


# ============================================================
# BENCHMARK REPORT
# ============================================================

def print_benchmark_report(results):

    print()
    print("=" * 80)

    print(
        "ZYVARENTH POWEROS"
    )

    print(
        "BENCHMARK PERFORMANCE REPORT"
    )

    print("=" * 80)

    print()

    for result in results:

        print("-" * 80)

        print(
            f"SCENARIO: "
            f"{result['name']}"
        )

        print()

        print(
            f"Scheduled workloads: "
            f"{result['scheduled']}"
        )

        print(
            f"Unscheduled workloads: "
            f"{result['unscheduled']}"
        )

        print(
            f"Success rate: "
            f"{result['success_rate']:.1f}%"
        )

        print(
            f"Forecast peak power: "
            f"{result['forecast_peak_power_kw']:.2f} kW"
        )

        print(
            f"Forecast peak hour: "
            f"{result['forecast_peak_hour']}"
        )

    print("-" * 80)

    print()

    print(
        "BENCHMARK COMPLETED"
    )

    print(
        "POWEROS PERFORMANCE VALIDATION COMPLETED"
    )

    print()


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)

    print(
        "ZYVARENTH POWEROS"
    )

    print(
        "STARTING PERFORMANCE BENCHMARK"
    )

    print("=" * 80)

    print()

    results = run_all_benchmarks()

    print_benchmark_report(
        results
    )


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":

    main()