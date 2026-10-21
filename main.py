import pandas as pd

from engine.power_model import (
    calculate_job_power,
)

from engine.optimizer import (
    optimize_schedule,
    calculate_schedule_metrics,
    calculate_optimized_energy_cost,
    get_energy_resources,
)

from engine.battery import (
    dispatch_battery,
)

from engine.explainability import (
    explain_schedule,
    summarize_explanations,
    print_explainability_report,
)

from engine.forecasting import (
    generate_poweros_forecast,
    print_forecast_report,
)
from engine.what_if import (
    run_standard_scenarios,
    create_scenario_comparison,
    print_what_if_report,
)
from engine.capacity_planning import (
    find_max_safe_gpu_capacity,
    print_capacity_report,
    run_capacity_scenarios,
)
from engine.telemetry import (
    generate_gpu_telemetry,
    calculate_telemetry_summary,
    print_telemetry_report,
)
from engine.telemetry_optimizer import (
    calculate_gpu_efficiency,
    create_telemetry_insights,
    print_telemetry_insights,
)

# ============================================================
# ZYVARENTH POWEROS
# AI COMPUTE-POWER OPTIMIZATION PLATFORM
# ============================================================

print()
print("=" * 70)
print("ZYVARENTH POWEROS")
print("AI COMPUTE-POWER OPTIMIZATION PLATFORM")
print("=" * 70)
print()


# ============================================================
# DATA CENTER CONFIGURATION
# ============================================================

NUM_GPUS = 100

POWER_LIMIT_KW = 70.0

PUE = 1.3


# ============================================================
# LOAD WORKLOAD DATA
# ============================================================

print("Loading AI workloads...")

jobs = pd.read_csv(
    "data/workloads.csv"
)

print(
    f"Loaded {len(jobs)} AI workloads."
)


# ============================================================
# CALCULATE WORKLOAD POWER
# ============================================================

jobs["gpu_power_kw"] = (
    jobs["gpu_required"].apply(
        calculate_job_power
    )
)

jobs["power_kw"] = (
    jobs["gpu_power_kw"] * PUE
)


# ============================================================
# ENERGY ENVIRONMENT
# ============================================================

electricity_prices = [
    5.0, 5.0, 5.0, 5.0,
    5.5, 6.0, 7.0, 8.0,
    9.0, 10.0, 11.0, 12.0,
    12.0, 11.5, 11.0, 10.5,
    10.0, 9.0, 8.0, 7.0,
    6.0, 5.5, 5.0, 5.0
]


solar_power = [
    0.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 5.0, 10.0,
    20.0, 30.0, 40.0, 50.0,
    55.0, 50.0, 45.0, 35.0,
    25.0, 15.0, 5.0, 0.0,
    0.0, 0.0, 0.0, 0.0
]


grid_capacity = [
    70.0, 70.0, 70.0, 70.0,
    70.0, 70.0, 70.0, 65.0,
    65.0, 60.0, 60.0, 55.0,
    55.0, 55.0, 60.0, 60.0,
    65.0, 65.0, 70.0, 70.0,
    70.0, 70.0, 70.0, 70.0
]


# ============================================================
# GET BATTERY / ENERGY RESOURCE MODEL
# ============================================================

energy_resources = get_energy_resources()

battery_power = energy_resources[
    "battery_power_kw"
]


# ============================================================
# VALIDATE 24-HOUR DATA
# ============================================================

if len(electricity_prices) != 24:
    raise ValueError(
        "electricity_prices must contain 24 hourly values."
    )

if len(solar_power) != 24:
    raise ValueError(
        "solar_power must contain 24 hourly values."
    )

if len(grid_capacity) != 24:
    raise ValueError(
        "grid_capacity must contain 24 hourly values."
    )

if len(battery_power) != 24:
    raise ValueError(
        "battery_power must contain 24 hourly values."
    )


# ============================================================
# CONVENTIONAL BASELINE SCHEDULER
# ============================================================

def create_conventional_schedule(
    jobs: pd.DataFrame,
    power_limit_kw: float,
) -> pd.DataFrame:

    schedule = jobs.copy()

    power_usage = [
        0.0
        for _ in range(24)
    ]

    gpu_usage = [
        0
        for _ in range(24)
    ]

    start_hours = []

    for _, job in schedule.iterrows():

        duration = int(
            job["duration_hours"]
        )

        power_kw = float(
            job["power_kw"]
        )

        gpu_required = int(
            job["gpu_required"]
        )

        deadline = int(
            job["deadline"]
        )

        placed = False

        latest_start = min(
            deadline - duration,
            24 - duration,
        )

        if latest_start < 0:

            start_hours.append(0)

            continue


        # ----------------------------------------------------
        # Conventional scheduler:
        # choose the earliest feasible time.
        # ----------------------------------------------------

        for start in range(
            0,
            latest_start + 1
        ):

            valid = True

            for hour in range(
                start,
                start + duration
            ):

                if (
                    power_usage[hour]
                    + power_kw
                    > power_limit_kw
                ):

                    valid = False

                    break

                if (
                    gpu_usage[hour]
                    + gpu_required
                    > NUM_GPUS
                ):

                    valid = False

                    break


            if valid:

                start_hours.append(
                    start
                )

                for hour in range(
                    start,
                    start + duration
                ):

                    power_usage[hour] += (
                        power_kw
                    )

                    gpu_usage[hour] += (
                        gpu_required
                    )

                placed = True

                break


        if not placed:

            start_hours.append(0)


    schedule["start_hour"] = (
        start_hours
    )

    schedule["finish_hour"] = (
        schedule["start_hour"]
        + schedule["duration_hours"]
    )

    return schedule


# ============================================================
# CREATE CONVENTIONAL BASELINE
# ============================================================

print()
print("Creating conventional baseline schedule...")

baseline_schedule = (
    create_conventional_schedule(
        jobs,
        POWER_LIMIT_KW,
    )
)


# ============================================================
# FORECASTING ENGINE
# ============================================================

print()
print("Running PowerOS Forecasting Engine...")
print()

forecast = generate_poweros_forecast(
    jobs,
    electricity_prices,
    solar_power,
    grid_capacity,
    24,
)

print_forecast_report(
    forecast
)


# ============================================================
# POWEROS OPTIMIZATION ENGINE
# ============================================================

print()
print("=" * 70)
print("RUNNING POWEROS OPTIMIZATION ENGINE")
print("=" * 70)
print()

optimized_schedule = optimize_schedule(
    jobs=jobs,
    electricity_prices=electricity_prices,
    power_limit_kw=POWER_LIMIT_KW,
    num_gpus=NUM_GPUS,
    grid_capacity=grid_capacity,
)


# ============================================================
# SCHEDULE METRICS
# ============================================================

print()
print("Calculating baseline performance...")

baseline_metrics = (
    calculate_schedule_metrics(
        baseline_schedule,
        electricity_prices,
        NUM_GPUS,
        POWER_LIMIT_KW,
    )
)


print(
    "Calculating PowerOS performance..."
)

optimized_metrics = (
    calculate_schedule_metrics(
        optimized_schedule,
        electricity_prices,
        NUM_GPUS,
        POWER_LIMIT_KW,
    )
)


# ============================================================
# ENERGY COST — BASELINE
# ============================================================

baseline_energy_result = (
    calculate_optimized_energy_cost(
        baseline_schedule,
        electricity_prices,
        grid_capacity,
        solar_power,
        battery_power,
    )
)


# ============================================================
# ENERGY COST — POWEROS
# ============================================================

optimized_energy_result = (
    calculate_optimized_energy_cost(
        optimized_schedule,
        electricity_prices,
        grid_capacity,
        solar_power,
        battery_power,
    )
)


# ============================================================
# EXTRACT COSTS
# ============================================================

baseline_cost = float(
    baseline_energy_result.get(
        "total_cost",
        0.0,
    )
)

optimized_cost = float(
    optimized_energy_result.get(
        "total_cost",
        0.0,
    )
)


cost_savings = (
    baseline_cost
    - optimized_cost
)


if baseline_cost > 0:

    savings_percentage = (
        cost_savings
        / baseline_cost
        * 100
    )

else:

    savings_percentage = 0.0


# ============================================================
# PEAK POWER
# ============================================================

baseline_peak = float(
    baseline_metrics.get(
        "peak_power_kw",
        0.0,
    )
)

optimized_peak = float(
    optimized_metrics.get(
        "peak_power_kw",
        0.0,
    )
)


peak_reduction = (
    baseline_peak
    - optimized_peak
)


if baseline_peak > 0:

    peak_reduction_percentage = (
        peak_reduction
        / baseline_peak
        * 100
    )

else:

    peak_reduction_percentage = 0.0


# ============================================================
# GPU UTILIZATION
# ============================================================

baseline_gpu_utilization = float(
    baseline_metrics.get(
        "gpu_utilization_percent",
        0.0,
    )
)

optimized_gpu_utilization = float(
    optimized_metrics.get(
        "gpu_utilization_percent",
        0.0,
    )
)


# ============================================================
# DEADLINES
# ============================================================

baseline_missed_deadlines = int(
    baseline_metrics.get(
        "missed_deadlines",
        0,
    )
)

optimized_missed_deadlines = int(
    optimized_metrics.get(
        "missed_deadlines",
        0,
    )
)


# ============================================================
# POWER VIOLATIONS
# ============================================================

baseline_power_violations = int(
    baseline_metrics.get(
        "power_limit_violations",
        0,
    )
)

optimized_power_violations = int(
    optimized_metrics.get(
        "power_limit_violations",
        0,
    )
)


# ============================================================
# BATTERY DISPATCH
# ============================================================

print()
print("Running PowerOS Battery Dispatch...")

dispatch_result = dispatch_battery(
    optimized_schedule,
    electricity_prices,
    solar_power,
)


# ============================================================
# ENERGY MIX
# ============================================================

solar_used = float(
    optimized_energy_result.get(
        "solar_energy_kwh",
        0.0,
    )
)

grid_used = float(
    optimized_energy_result.get(
        "grid_energy_kwh",
        0.0,
    )
)

battery_used = float(
    optimized_energy_result.get(
        "battery_energy_kwh",
        0.0,
    )
)

battery_charged = float(
    optimized_energy_result.get(
        "battery_charged_kwh",
        0.0,
    )
)

unserved_energy = float(
    optimized_energy_result.get(
        "unserved_energy_kwh",
        0.0,
    )
)

final_battery_soc = float(
    optimized_energy_result.get(
        "final_battery_soc_percent",
        0.0,
    )
)


# ============================================================
# EXPLAINABILITY ENGINE
# ============================================================

print()
print("Running PowerOS Explainability Engine...")
print()

explanations = explain_schedule(
    optimized_schedule,
    electricity_prices,
    grid_capacity,
    solar_power,
    POWER_LIMIT_KW,
)


explanation_summary = (
    summarize_explanations(
        explanations
    )
)


print_explainability_report(
    explanations,
    explanation_summary,
)


# ============================================================
# FINAL PERFORMANCE REPORT
# ============================================================

print()
print()
print("=" * 70)
print("ZYVARENTH POWEROS — PERFORMANCE REPORT")
print("=" * 70)


# ============================================================
# WORKLOADS
# ============================================================

print()
print("WORKLOADS")
print("-" * 70)

print(
    f"Total workloads        : "
    f"{len(jobs)}"
)

print(
    f"Total GPUs requested   : "
    f"{jobs['gpu_required'].sum()}"
)

print(
    f"Data center GPUs       : "
    f"{NUM_GPUS}"
)


# ============================================================
# POWER PERFORMANCE
# ============================================================

print()
print("POWER PERFORMANCE")
print("-" * 70)

print(
    f"Power limit            : "
    f"{POWER_LIMIT_KW:.2f} kW"
)

print(
    f"Baseline peak power    : "
    f"{baseline_peak:.2f} kW"
)

print(
    f"ZYVARENTH peak power   : "
    f"{optimized_peak:.2f} kW"
)

print(
    f"Peak power reduction   : "
    f"{peak_reduction:.2f} kW"
)

print(
    f"Peak reduction         : "
    f"{peak_reduction_percentage:.2f}%"
)


# ============================================================
# GPU UTILIZATION
# ============================================================

print()
print("GPU UTILIZATION")
print("-" * 70)

print(
    f"Baseline utilization   : "
    f"{baseline_gpu_utilization:.2f}%"
)

print(
    f"PowerOS utilization    : "
    f"{optimized_gpu_utilization:.2f}%"
)


# ============================================================
# ENERGY COST
# ============================================================

print()
print("ENERGY COST")
print("-" * 70)

print(
    f"Baseline cost          : "
    f"₹{baseline_cost:.2f}"
)

print(
    f"ZYVARENTH cost         : "
    f"₹{optimized_cost:.2f}"
)

print(
    f"Cost savings           : "
    f"₹{cost_savings:.2f}"
)

print(
    f"Savings percentage     : "
    f"{savings_percentage:.2f}%"
)


# ============================================================
# ENERGY MIX
# ============================================================

print()
print("ENERGY MIX")
print("-" * 70)

print(
    f"Solar energy used      : "
    f"{solar_used:.2f} kWh"
)

print(
    f"Grid energy used       : "
    f"{grid_used:.2f} kWh"
)

print(
    f"Battery energy used    : "
    f"{battery_used:.2f} kWh"
)

print(
    f"Battery charged        : "
    f"{battery_charged:.2f} kWh"
)

print(
    f"Final battery SOC      : "
    f"{final_battery_soc:.2f}%"
)

print(
    f"Unserved energy        : "
    f"{unserved_energy:.2f} kWh"
)


# ============================================================
# RELIABILITY
# ============================================================

print()
print("RELIABILITY")
print("-" * 70)

print(
    f"Baseline missed jobs   : "
    f"{baseline_missed_deadlines}"
)

print(
    f"PowerOS missed jobs    : "
    f"{optimized_missed_deadlines}"
)

print(
    f"Baseline violations    : "
    f"{baseline_power_violations}"
)

print(
    f"PowerOS violations     : "
    f"{optimized_power_violations}"
)


# ============================================================
# BUSINESS VALUE
# ============================================================

print()
print("BUSINESS VALUE")
print("-" * 70)

print(
    f"Jobs shifted           : "
    f"{explanation_summary.get('shifted_jobs', 0)}"
)

print(
    f"Solar-optimized jobs   : "
    f"{explanation_summary.get('solar_optimized_jobs', 0)}"
)

print(
    f"Low-price jobs         : "
    f"{explanation_summary.get('low_price_jobs', 0)}"
)


# ============================================================
# OPTIMIZED SCHEDULE
# ============================================================

print()
print("OPTIMIZED SCHEDULE — FIRST 20 JOBS")
print("-" * 70)

display_columns = [
    "job_id",
    "gpu_required",
    "duration_hours",
    "deadline",
    "priority",
    "start_hour",
    "finish_hour",
    "power_kw",
]


available_columns = [
    column
    for column in display_columns
    if column in optimized_schedule.columns
]


print(
    optimized_schedule[
        available_columns
    ].head(20).to_string(
        index=False
    )
)
# ---------------------------------------------------------
# GPU TELEMETRY
# ---------------------------------------------------------

gpu_telemetry = generate_gpu_telemetry(
    num_gpus=NUM_GPUS,
    hours=24,
)

telemetry_summary = calculate_telemetry_summary(
    gpu_telemetry
)

print_telemetry_report(
    gpu_telemetry,
    telemetry_summary,
)

gpu_telemetry.to_csv(
    "results/gpu_telemetry.csv",
    index=False,
)
# ============================================================
# FINAL STATUS
# ============================================================

# ============================================================
# WHAT-IF SIMULATION ENGINE
# ============================================================

print()
print("=" * 70)
print("RUNNING WHAT-IF SIMULATION ENGINE")
print("=" * 70)
print()

what_if_results = run_standard_scenarios(
    jobs
)


# ============================================================
# PRINT INDIVIDUAL SCENARIO REPORTS
# ============================================================

for scenario_name, scenario_result in (
    what_if_results.items()
):

    print()
    print(
        f"SCENARIO: {scenario_name}"
    )

    print_what_if_report(
        scenario_result
    )


# ============================================================
# SCENARIO COMPARISON
# ============================================================

scenario_comparison = (
    create_scenario_comparison(
        what_if_results
    )
)


print()
print("=" * 70)
print("WHAT-IF SCENARIO COMPARISON")
print("=" * 70)
print()

print(
    scenario_comparison.to_string(
        index=False
    )
)


# ============================================================
# SAVE SCENARIO RESULTS
# ============================================================

scenario_comparison.to_csv(
    "results/what_if_scenarios.csv",
    index=False
)


print()
print(
    "What-if scenario results saved to "
    "results/what_if_scenarios.csv"
)



# ============================================================
# CAPACITY PLANNING ENGINE
# ============================================================

print()
print("=" * 70)
print("RUNNING CAPACITY PLANNING ENGINE")
print("=" * 70)
print()

capacity_result = find_max_safe_gpu_capacity(
    jobs=jobs,
    current_gpus=NUM_GPUS,
    power_limit_kw=POWER_LIMIT_KW,
    prices=electricity_prices,
    grid_capacity=grid_capacity,
    solar_power=solar_power,
    battery_power=battery_power,
    max_additional_gpus=500,
)

print_capacity_report(
    capacity_result
)

# ---------------------------------------------------------
# GPU TELEMETRY
# ---------------------------------------------------------

gpu_telemetry = generate_gpu_telemetry(
    num_gpus=NUM_GPUS,
    hours=24,
)

telemetry_summary = calculate_telemetry_summary(
    gpu_telemetry
)

print_telemetry_report(
    gpu_telemetry,
    telemetry_summary,
)

gpu_telemetry.to_csv(
    "results/gpu_telemetry.csv",
    index=False,
)

# ---------------------------------------------------------
# TELEMETRY OPTIMIZATION INSIGHTS
# ---------------------------------------------------------

telemetry_efficiency = calculate_gpu_efficiency(
    gpu_telemetry
)

telemetry_insights = create_telemetry_insights(
    gpu_telemetry
)

print_telemetry_insights(
    telemetry_insights
)

telemetry_efficiency.to_csv(
    "results/telemetry_efficiency.csv",
    index=False,
)

# ============================================================
# GPU EXPANSION SCENARIOS
# ============================================================

capacity_scenarios = run_capacity_scenarios(
    jobs=jobs,
    current_gpus=NUM_GPUS,
    power_limit_kw=POWER_LIMIT_KW,
)

print()
print("=" * 70)
print("GPU EXPANSION SCENARIOS")
print("=" * 70)
print()

print(
    capacity_scenarios.to_string(
        index=False
    )
)


# ============================================================
# SAVE CAPACITY RESULTS
# ============================================================

capacity_scenarios.to_csv(
    "results/capacity_scenarios.csv",
    index=False,
)

print()
print(
    "Capacity planning results saved to "
    "results/capacity_scenarios.csv"
)