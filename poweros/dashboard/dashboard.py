"""
ZYVARENTH PowerOS
Operator Dashboard

Runs the PowerOS engine and presents the result
in a clean operator-facing terminal dashboard.
"""

from poweros.data.fair_baseline import (
    create_realistic_state,
    create_realistic_prices,
    create_realistic_solar,
)

from poweros.core.orchestrator import run_poweros


# ============================================================
# DISPLAY HELPERS
# ============================================================

def line(char="=", width=90):
    print(char * width)


def get_value(data, *keys, default=0):
    if not isinstance(data, dict):
        return default

    for key in keys:
        if key in data:
            return data[key]

    return default


def print_header():
    print()
    line()
    print("ZYVARENTH POWEROS")
    print("AI POWER ORCHESTRATION PLATFORM")
    line()


# ============================================================
# POWER STATUS
# ============================================================

def print_power_status(result):

    state = result.get(
        "state_analysis",
        {},
    )

    power_summary = result.get(
        "power_summary",
        {},
    )

    status = state.get(
        "status",
        "UNKNOWN",
    )

    bottleneck = state.get(
        "primary_bottleneck",
        "NONE",
    )

    pressure = get_value(
        state,
        "power_pressure_percent",
        default=0.0,
    )

    headroom = get_value(
        state,
        "power_headroom_kw",
        default=0.0,
    )

    peak_power = get_value(
        power_summary,
        "peak_facility_power_kw",
        "peak_power_kw",
        default=0.0,
    )

    print()
    line("-")
    print("POWER STATUS")
    line("-")

    print(f"System status:        {status}")
    print(f"Primary bottleneck:   {bottleneck}")
    print(f"Power pressure:       {pressure:.2f}%")
    print(f"Power headroom:       {headroom:.2f} kW")
    print(f"Peak facility power:  {peak_power:.2f} kW")


# ============================================================
# GPU STATUS
# ============================================================

def print_gpu_status(result):

    state = result.get(
        "state_analysis",
        {},
    )

    gpu = state.get(
        "gpu_analysis",
        {},
    )

    print()
    line("-")
    print("GPU STATUS")
    line("-")

    print(
        f"Average utilization:  "
        f"{get_value(gpu, 'average_utilization_percent', 'average_utilization', default=0):.2f}%"
    )

    print(
        f"Idle GPUs:            "
        f"{get_value(gpu, 'idle_gpus', default=0)}"
    )

    print(
        f"High-utilization GPUs:"
        f" {get_value(gpu, 'high_utilization_gpus', default=0)}"
    )


# ============================================================
# WORKLOAD STATUS
# ============================================================

def print_workload_status(result):

    schedule = result.get(
        "schedule",
        {},
    )

    scheduled = schedule.get(
        "scheduled",
        []
    )

    unscheduled = schedule.get(
        "unscheduled",
        []
    )

    optimization = result.get(
        "optimization_summary",
        {}
    )

    print()
    line("-")
    print("WORKLOAD STATUS")
    line("-")

    print(
        f"Total workloads:      "
        f"{get_value(optimization, 'total_count', default=0)}"
    )

    print(
        f"Scheduled:            "
        f"{len(scheduled)}"
    )

    print(
        f"Unscheduled:          "
        f"{len(unscheduled)}"
    )

    print()

    if scheduled:

        print("CURRENT SCHEDULE")

        for item in scheduled:

            workload_id = item.get(
                "workload_id",
                "UNKNOWN",
            )

            start = item.get(
                "start_hour",
                "?",
            )

            finish = item.get(
                "finish_hour",
                "?",
            )

            gpu = item.get(
                "gpu_required",
                "?",
            )

            print(
                f"  {workload_id:<20}"
                f" START={start:<3}"
                f" FINISH={finish:<3}"
                f" GPU={gpu}"
            )


# ============================================================
# DECISIONS
# ============================================================

def print_decisions(result):

    summary = result.get(
        "decision_summary",
        {},
    )

    decisions = result.get(
        "decisions",
        [],
    )

    print()
    line("-")
    print("POWEROS DECISIONS")
    line("-")

    print(
        f"RUN:                  "
        f"{get_value(summary, 'run_decisions', 'run', default=0)}"
    )

    print(
        f"WAIT:                 "
        f"{get_value(summary, 'wait_decisions', 'wait', default=0)}"
    )

    print(
        f"SHIFT:                "
        f"{get_value(summary, 'shift_decisions', 'shift', default=0)}"
    )

    print(
        f"PROTECT DEADLINE:     "
        f"{get_value(summary, 'protect_deadline_decisions', default=0)}"
    )

    print()

    for decision in decisions:

        workload_id = decision.get(
            "workload_id",
            "UNKNOWN",
        )

        action = decision.get(
            "action",
            "UNKNOWN",
        )

        reason = decision.get(
            "reason",
            "",
        )

        print(
            f"  {workload_id:<20}"
            f" {action:<20}"
            f" {reason}"
        )


# ============================================================
# ENERGY
# ============================================================

def print_energy_status(result):

    dispatch = result.get(
        "battery_dispatch",
        {},
    )

    solar = get_value(
        dispatch,
        "solar_energy_used_kwh",
        "solar_used_kwh",
        "solar_used",
        default=0.0,
    )

    battery = get_value(
        dispatch,
        "battery_energy_used_kwh",
        "battery_used_kwh",
        "battery_used",
        default=0.0,
    )

    cost = get_value(
        dispatch,
        "total_cost",
        "total_energy_cost",
        "cost",
        default=0.0,
    )

    print()
    line("-")
    print("ENERGY RESOURCES")
    line("-")

    print(
        f"Solar used:           "
        f"{solar:.2f} kWh"
    )

    print(
        f"Battery used:         "
        f"{battery:.2f} kWh"
    )

    print(
        f"Estimated energy cost:"
        f" ₹{cost:.2f}"
    )


# ============================================================
# FORECAST
# ============================================================

def print_forecast(result):

    forecast = result.get(
        "forecast",
        {}
    )

    print()
    line("-")
    print("24-HOUR POWER FORECAST")
    line("-")

    if isinstance(forecast, dict):

        peak = get_value(
            forecast,
            "peak_power_kw",
            "forecast_peak_power_kw",
            default=0.0,
        )

        peak_hour = get_value(
            forecast,
            "peak_hour",
            "forecast_peak_hour",
            default="N/A",
        )

        print(
            f"Forecast peak:       "
            f"{peak:.2f} kW"
        )

        print(
            f"Peak hour:            "
            f"{peak_hour}"
        )


# ============================================================
# EXECUTIVE SUMMARY
# ============================================================

def print_executive_summary(result):

    print()
    line("-")
    print("EXECUTIVE SUMMARY")
    line("-")

    summary = result.get(
        "executive_summary",
        {}
    )

    if isinstance(summary, dict):

        for key, value in summary.items():

            label = key.replace(
                "_",
                " "
            ).title()

            print(
                f"{label:<28}: {value}"
            )

    else:

        print(
            "PowerOS completed the optimization cycle."
        )


# ============================================================
# MAIN DASHBOARD
# ============================================================

def run_dashboard():

    state = create_realistic_state()

    prices = create_realistic_prices()

    solar = create_realistic_solar()

    result = run_poweros(
        state=state,
        electricity_prices=prices,
        solar_power_by_hour=solar,
        battery_capacity_kwh=100.0,
        initial_battery_soc_percent=80.0,
        battery_max_discharge_kw=10.0,
        reserve_percent=15.0,
    )

    print_header()

    print_power_status(result)

    print_gpu_status(result)

    print_workload_status(result)

    print_forecast(result)

    print_energy_status(result)

    print_decisions(result)

    print_executive_summary(result)

    print()
    line()
    print("POWEROS OPERATOR DASHBOARD COMPLETED")
    line()
    print()


def main():

    run_dashboard()


if __name__ == "__main__":
    main()