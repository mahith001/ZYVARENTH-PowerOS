# ============================================================
# ZYVARENTH POWEROS
# WHAT-IF SIMULATION ENGINE
# ============================================================

import pandas as pd

from engine.power_model import calculate_job_power

from engine.optimizer import (
    optimize_schedule,
    calculate_schedule_metrics,
    calculate_optimized_energy_cost,
    get_energy_resources,
    get_electricity_prices,
    get_grid_capacity,
)


# ============================================================
# DATA CENTER DEFAULTS
# ============================================================

DEFAULT_NUM_GPUS = 100

DEFAULT_POWER_LIMIT_KW = 70.0

DEFAULT_PUE = 1.3


# ============================================================
# LOAD AND PREPARE WORKLOADS
# ============================================================

def prepare_jobs(
    jobs: pd.DataFrame,
    pue: float = DEFAULT_PUE,
) -> pd.DataFrame:

    prepared = jobs.copy()

    prepared["gpu_power_kw"] = (
        prepared["gpu_required"].apply(
            calculate_job_power
        )
    )

    prepared["power_kw"] = (
        prepared["gpu_power_kw"] * pue
    )

    return prepared


# ============================================================
# CONVENTIONAL BASELINE
# ============================================================

def create_baseline_schedule(
    jobs: pd.DataFrame,
    power_limit_kw: float,
    num_gpus: int,
    grid_capacity: list,
) -> pd.DataFrame:

    jobs = jobs.sort_values(
        by=["deadline", "job_id"]
    ).reset_index(drop=True)

    power_usage = [
        0.0
        for _ in range(24)
    ]

    gpu_usage = [
        0
        for _ in range(24)
    ]

    scheduled = []

    for _, job in jobs.iterrows():

        duration = int(
            job["duration_hours"]
        )

        gpu_required = int(
            job["gpu_required"]
        )

        power_kw = float(
            job["power_kw"]
        )

        deadline = int(
            job["deadline"]
        )

        priority = str(
            job["priority"]
        )

        latest_start = min(
            deadline - duration,
            24 - duration,
        )

        best_start = None

        for start in range(
            max(0, latest_start + 1)
        ):

            feasible = True

            for hour in range(
                start,
                start + duration
            ):

                available_power = min(
                    power_limit_kw,
                    float(grid_capacity[hour])
                )

                if (
                    power_usage[hour]
                    + power_kw
                    > available_power
                ):

                    feasible = False

                    break

                if (
                    gpu_usage[hour]
                    + gpu_required
                    > num_gpus
                ):

                    feasible = False

                    break

            if feasible:

                best_start = start

                break

        if best_start is not None:

            for hour in range(
                best_start,
                best_start + duration
            ):

                power_usage[hour] += (
                    power_kw
                )

                gpu_usage[hour] += (
                    gpu_required
                )

        scheduled.append({

            "job_id":
                int(job["job_id"]),

            "start_hour":
                (
                    best_start
                    if best_start is not None
                    else -1
                ),

            "duration_hours":
                duration,

            "gpu_required":
                gpu_required,

            "power_kw":
                power_kw,

            "deadline":
                deadline,

            "priority":
                priority,

            "cost":
                None,
        })

    return pd.DataFrame(
        scheduled
    )


# ============================================================
# APPLY SCENARIO TO WORKLOADS
# ============================================================

def apply_gpu_demand_change(
    jobs: pd.DataFrame,
    percentage: float,
) -> pd.DataFrame:

    changed = jobs.copy()

    multiplier = (
        1.0
        + percentage / 100.0
    )

    changed["gpu_required"] = (
        changed["gpu_required"]
        * multiplier
    ).round().astype(int)

    changed["gpu_required"] = (
        changed["gpu_required"]
        .clip(lower=1)
    )

    changed["gpu_power_kw"] = (
        changed["gpu_required"].apply(
            calculate_job_power
        )
    )

    # Preserve PUE from the existing power
    # relationship.

    original_gpu_power = (
        jobs["gpu_power_kw"]
        .replace(0, 1)
    )

    pue = (
        jobs["power_kw"]
        / original_gpu_power
    ).mean()

    changed["power_kw"] = (
        changed["gpu_power_kw"]
        * pue
    )

    return changed


# ============================================================
# APPLY PRICE CHANGE
# ============================================================

def apply_price_change(
    prices: list,
    percentage: float,
) -> list:

    multiplier = (
        1.0
        + percentage / 100.0
    )

    return [
        max(
            0.0,
            float(price) * multiplier
        )
        for price in prices
    ]


# ============================================================
# APPLY SOLAR CHANGE
# ============================================================

def apply_solar_change(
    solar_power: list,
    percentage: float,
) -> list:

    multiplier = (
        1.0
        + percentage / 100.0
    )

    return [
        max(
            0.0,
            float(power) * multiplier
        )
        for power in solar_power
    ]


# ============================================================
# APPLY GRID CAPACITY CHANGE
# ============================================================

def apply_grid_capacity_change(
    grid_capacity: list,
    percentage: float,
) -> list:

    multiplier = (
        1.0
        + percentage / 100.0
    )

    return [
        max(
            0.0,
            float(capacity) * multiplier
        )
        for capacity in grid_capacity
    ]


# ============================================================
# CALCULATE SCENARIO
# ============================================================

def simulate_scenario(
    jobs: pd.DataFrame,
    prices: list,
    solar_power: list,
    grid_capacity: list,
    battery_power: list,
    num_gpus: int = DEFAULT_NUM_GPUS,
    power_limit_kw: float = DEFAULT_POWER_LIMIT_KW,
) -> dict:

    # --------------------------------------------------------
    # BASELINE
    # --------------------------------------------------------

    baseline_schedule = (
        create_baseline_schedule(
            jobs,
            power_limit_kw,
            num_gpus,
            grid_capacity,
        )
    )

    baseline_metrics = (
        calculate_schedule_metrics(
            baseline_schedule,
            prices,
            num_gpus,
            power_limit_kw,
        )
    )

    baseline_energy = (
        calculate_optimized_energy_cost(
            baseline_schedule,
            prices,
            grid_capacity,
            solar_power,
            battery_power,
        )
    )


    # --------------------------------------------------------
    # POWEROS
    # --------------------------------------------------------

    optimized_schedule = optimize_schedule(
        jobs,
        prices,
        power_limit_kw,
        num_gpus=num_gpus,
        grid_capacity=grid_capacity,
    )

    optimized_metrics = (
        calculate_schedule_metrics(
            optimized_schedule,
            prices,
            num_gpus,
            power_limit_kw,
        )
    )

    optimized_energy = (
        calculate_optimized_energy_cost(
            optimized_schedule,
            prices,
            grid_capacity,
            solar_power,
            battery_power,
        )
    )


    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    baseline_cost = float(
        baseline_energy.get(
            "total_cost",
            0.0,
        )
    )

    optimized_cost = float(
        optimized_energy.get(
            "total_cost",
            0.0,
        )
    )

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

    baseline_gpu = float(
        baseline_metrics.get(
            "gpu_utilization_percent",
            0.0,
        )
    )

    optimized_gpu = float(
        optimized_metrics.get(
            "gpu_utilization_percent",
            0.0,
        )
    )

    baseline_missed = int(
        baseline_metrics.get(
            "missed_deadlines",
            0,
        )
    )

    optimized_missed = int(
        optimized_metrics.get(
            "missed_deadlines",
            0,
        )
    )

    baseline_violations = int(
        baseline_metrics.get(
            "power_limit_violations",
            0,
        )
    )

    optimized_violations = int(
        optimized_metrics.get(
            "power_limit_violations",
            0,
        )
    )


    # --------------------------------------------------------
    # POWEROS BENEFIT
    # --------------------------------------------------------

    savings = (
        baseline_cost
        - optimized_cost
    )

    peak_reduction = (
        baseline_peak
        - optimized_peak
    )

    if baseline_cost > 0:

        savings_percentage = (
            savings
            / baseline_cost
            * 100.0
        )

    else:

        savings_percentage = 0.0


    if baseline_peak > 0:

        peak_reduction_percentage = (
            peak_reduction
            / baseline_peak
            * 100.0
        )

    else:

        peak_reduction_percentage = 0.0


    return {

        "baseline_cost":
            baseline_cost,

        "poweros_cost":
            optimized_cost,

        "cost_savings":
            savings,

        "cost_savings_percentage":
            savings_percentage,

        "baseline_peak_kw":
            baseline_peak,

        "poweros_peak_kw":
            optimized_peak,

        "peak_reduction_kw":
            peak_reduction,

        "peak_reduction_percentage":
            peak_reduction_percentage,

        "baseline_gpu_utilization":
            baseline_gpu,

        "poweros_gpu_utilization":
            optimized_gpu,

        "baseline_missed_deadlines":
            baseline_missed,

        "poweros_missed_deadlines":
            optimized_missed,

        "baseline_power_violations":
            baseline_violations,

        "poweros_power_violations":
            optimized_violations,

        "optimized_schedule":
            optimized_schedule,

        "baseline_schedule":
            baseline_schedule,

        "energy_result":
            optimized_energy,
    }


# ============================================================
# RUN COMPLETE WHAT-IF ANALYSIS
# ============================================================

def run_what_if_analysis(
    jobs: pd.DataFrame,
    gpu_change: float = 0.0,
    price_change: float = 0.0,
    solar_change: float = 0.0,
    grid_change: float = 0.0,
    power_limit_change: float = 0.0,
    num_gpus: int = DEFAULT_NUM_GPUS,
    power_limit_kw: float = DEFAULT_POWER_LIMIT_KW,
) -> dict:

    # --------------------------------------------------------
    # Prepare jobs
    # --------------------------------------------------------

    jobs = prepare_jobs(
        jobs
    )


    # --------------------------------------------------------
    # Get current energy environment
    # --------------------------------------------------------

    prices = get_electricity_prices()

    grid_capacity = get_grid_capacity()

    energy_resources = (
        get_energy_resources()
    )

    solar_power = (
        energy_resources[
            "solar_power_kw"
        ]
    )

    battery_power = (
        energy_resources[
            "battery_power_kw"
        ]
    )


    # --------------------------------------------------------
    # Apply changes
    # --------------------------------------------------------

    scenario_jobs = (
        apply_gpu_demand_change(
            jobs,
            gpu_change,
        )
    )

    scenario_prices = (
        apply_price_change(
            prices,
            price_change,
        )
    )

    scenario_solar = (
        apply_solar_change(
            solar_power,
            solar_change,
        )
    )

    scenario_grid = (
        apply_grid_capacity_change(
            grid_capacity,
            grid_change,
        )
    )

    scenario_power_limit = (
        power_limit_kw
        * (
            1.0
            + power_limit_change / 100.0
        )
    )

    scenario_power_limit = max(
        1.0,
        scenario_power_limit,
    )


    # --------------------------------------------------------
    # Run simulation
    # --------------------------------------------------------

    result = simulate_scenario(
        scenario_jobs,
        scenario_prices,
        scenario_solar,
        scenario_grid,
        battery_power,
        num_gpus,
        scenario_power_limit,
    )


    # --------------------------------------------------------
    # Scenario information
    # --------------------------------------------------------

    result["scenario"] = {

        "gpu_change_percent":
            gpu_change,

        "price_change_percent":
            price_change,

        "solar_change_percent":
            solar_change,

        "grid_change_percent":
            grid_change,

        "power_limit_change_percent":
            power_limit_change,

        "effective_power_limit_kw":
            scenario_power_limit,
    }


    return result


# ============================================================
# PRINT WHAT-IF REPORT
# ============================================================

def print_what_if_report(
    result: dict,
) -> None:

    scenario = result[
        "scenario"
    ]


    print()
    print("=" * 70)
    print("ZYVARENTH POWEROS — WHAT-IF SIMULATOR")
    print("=" * 70)


    # --------------------------------------------------------
    # Scenario
    # --------------------------------------------------------

    print()
    print("SCENARIO")
    print("-" * 70)

    print(
        f"GPU demand change       : "
        f"{scenario['gpu_change_percent']:+.1f}%"
    )

    print(
        f"Electricity price      : "
        f"{scenario['price_change_percent']:+.1f}%"
    )

    print(
        f"Solar generation       : "
        f"{scenario['solar_change_percent']:+.1f}%"
    )

    print(
        f"Grid capacity          : "
        f"{scenario['grid_change_percent']:+.1f}%"
    )

    print(
        f"Power limit            : "
        f"{scenario['effective_power_limit_kw']:.2f} kW"
    )


    # --------------------------------------------------------
    # Cost
    # --------------------------------------------------------

    print()
    print("COST IMPACT")
    print("-" * 70)

    print(
        f"Baseline cost          : "
        f"₹{result['baseline_cost']:.2f}"
    )

    print(
        f"PowerOS cost           : "
        f"₹{result['poweros_cost']:.2f}"
    )

    print(
        f"PowerOS savings        : "
        f"₹{result['cost_savings']:.2f}"
    )

    print(
        f"Savings percentage     : "
        f"{result['cost_savings_percentage']:.2f}%"
    )


    # --------------------------------------------------------
    # Power
    # --------------------------------------------------------

    print()
    print("POWER IMPACT")
    print("-" * 70)

    print(
        f"Baseline peak          : "
        f"{result['baseline_peak_kw']:.2f} kW"
    )

    print(
        f"PowerOS peak           : "
        f"{result['poweros_peak_kw']:.2f} kW"
    )

    print(
        f"Peak reduction         : "
        f"{result['peak_reduction_kw']:.2f} kW"
    )

    print(
        f"Peak reduction         : "
        f"{result['peak_reduction_percentage']:.2f}%"
    )


    # --------------------------------------------------------
    # GPU
    # --------------------------------------------------------

    print()
    print("GPU UTILIZATION")
    print("-" * 70)

    print(
        f"Baseline utilization   : "
        f"{result['baseline_gpu_utilization']:.2f}%"
    )

    print(
        f"PowerOS utilization    : "
        f"{result['poweros_gpu_utilization']:.2f}%"
    )


    # --------------------------------------------------------
    # Reliability
    # --------------------------------------------------------

    print()
    print("RELIABILITY")
    print("-" * 70)

    print(
        f"Baseline missed jobs   : "
        f"{result['baseline_missed_deadlines']}"
    )

    print(
        f"PowerOS missed jobs    : "
        f"{result['poweros_missed_deadlines']}"
    )

    print(
        f"Baseline violations    : "
        f"{result['baseline_power_violations']}"
    )

    print(
        f"PowerOS violations     : "
        f"{result['poweros_power_violations']}"
    )


    # --------------------------------------------------------
    # Decision
    # --------------------------------------------------------

    print()
    print("POWEROS DECISION")
    print("-" * 70)

    if (
        result["poweros_missed_deadlines"] == 0
        and result["poweros_power_violations"] == 0
    ):

        print(
            "PowerOS can handle this scenario "
            "within the modeled constraints."
        )

    else:

        print(
            "PowerOS detected capacity or scheduling "
            "pressure under this scenario."
        )


    print()
    print("=" * 70)
    print()


# ============================================================
# QUICK PREDEFINED SCENARIOS
# ============================================================

def run_standard_scenarios(
    jobs: pd.DataFrame,
) -> dict:

    scenarios = {

        "GPU_DEMAND_PLUS_30": {
            "gpu_change": 30.0,
        },

        "ELECTRICITY_PLUS_20": {
            "price_change": 20.0,
        },

        "SOLAR_MINUS_40": {
            "solar_change": -40.0,
        },

        "GRID_MINUS_20": {
            "grid_change": -20.0,
        },

        "GPU_PLUS_30_PRICE_PLUS_20": {
            "gpu_change": 30.0,
            "price_change": 20.0,
        },

    }


    results = {}


    for name, settings in scenarios.items():

        result = run_what_if_analysis(
            jobs,
            **settings,
        )

        results[name] = result


    return results


# ============================================================
# COMPARISON TABLE
# ============================================================

def create_scenario_comparison(
    results: dict,
) -> pd.DataFrame:

    rows = []


    for name, result in results.items():

        rows.append({

            "scenario":
                name,

            "cost_savings_percent":
                result[
                    "cost_savings_percentage"
                ],

            "peak_reduction_percent":
                result[
                    "peak_reduction_percentage"
                ],

            "poweros_peak_kw":
                result[
                    "poweros_peak_kw"
                ],

            "poweros_gpu_utilization":
                result[
                    "poweros_gpu_utilization"
                ],

            "missed_deadlines":
                result[
                    "poweros_missed_deadlines"
                ],

            "power_violations":
                result[
                    "poweros_power_violations"
                ],
        })


    return pd.DataFrame(rows)


# ============================================================
# END
# ============================================================