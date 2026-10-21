# ============================================================
# ZYVARENTH POWEROS
# CAPACITY PLANNING ENGINE
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
# DEFAULT DATA CENTER SETTINGS
# ============================================================

DEFAULT_NUM_GPUS = 100

DEFAULT_POWER_LIMIT_KW = 70.0

DEFAULT_PUE = 1.3


# ============================================================
# PREPARE WORKLOADS
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
# RUN POWEROS FOR A GIVEN GPU CAPACITY
# ============================================================

def evaluate_gpu_capacity(
    jobs: pd.DataFrame,
    num_gpus: int,
    power_limit_kw: float,
    prices: list,
    grid_capacity: list,
    solar_power: list,
    battery_power: list,
) -> dict:

    # --------------------------------------------------------
    # Run optimizer
    # --------------------------------------------------------

    optimized_schedule = optimize_schedule(
        jobs,
        prices,
        power_limit_kw,
        num_gpus=num_gpus,
        grid_capacity=grid_capacity,
    )


    # --------------------------------------------------------
    # Calculate performance
    # --------------------------------------------------------

    metrics = calculate_schedule_metrics(
        optimized_schedule,
        prices,
        num_gpus,
        power_limit_kw,
    )


    # --------------------------------------------------------
    # Calculate energy economics
    # --------------------------------------------------------

    energy_result = (
        calculate_optimized_energy_cost(
            optimized_schedule,
            prices,
            grid_capacity,
            solar_power,
            battery_power,
        )
    )


    # --------------------------------------------------------
    # Extract values
    # --------------------------------------------------------

    peak_power = float(
        metrics.get(
            "peak_power_kw",
            0.0,
        )
    )

    gpu_utilization = float(
        metrics.get(
            "gpu_utilization_percent",
            0.0,
        )
    )

    missed_deadlines = int(
        metrics.get(
            "missed_deadlines",
            0,
        )
    )

    power_violations = int(
        metrics.get(
            "power_limit_violations",
            0,
        )
    )

    total_cost = float(
        energy_result.get(
            "total_cost",
            0.0,
        )
    )

    unserved_energy = float(
        energy_result.get(
            "unserved_energy_kwh",
            0.0,
        )
    )


    # --------------------------------------------------------
    # Determine feasibility
    # --------------------------------------------------------

    feasible = (
        missed_deadlines == 0
        and power_violations == 0
        and unserved_energy <= 0.001
    )


    return {

        "num_gpus":
            num_gpus,

        "peak_power_kw":
            peak_power,

        "power_headroom_kw":
            max(
                0.0,
                power_limit_kw
                - peak_power,
            ),

        "gpu_utilization_percent":
            gpu_utilization,

        "missed_deadlines":
            missed_deadlines,

        "power_violations":
            power_violations,

        "unserved_energy_kwh":
            unserved_energy,

        "total_cost":
            total_cost,

        "feasible":
            feasible,

        "schedule":
            optimized_schedule,
    }


# ============================================================
# FIND MAXIMUM SAFE GPU CAPACITY
# ============================================================

def find_max_safe_gpu_capacity(
    jobs: pd.DataFrame,
    current_gpus: int,
    power_limit_kw: float,
    prices: list,
    grid_capacity: list,
    solar_power: list,
    battery_power: list,
    max_additional_gpus: int = 1000,
) -> dict:

    # --------------------------------------------------------
    # Test progressively larger GPU capacities
    # --------------------------------------------------------

    results = []

    maximum_test_gpus = (
        current_gpus
        + max_additional_gpus
    )


    last_feasible = None

    first_infeasible = None


    for gpu_capacity in range(
        current_gpus,
        maximum_test_gpus + 1,
    ):

        result = evaluate_gpu_capacity(
            jobs,
            gpu_capacity,
            power_limit_kw,
            prices,
            grid_capacity,
            solar_power,
            battery_power,
        )

        results.append({

            "gpu_capacity":
                gpu_capacity,

            "peak_power_kw":
                result[
                    "peak_power_kw"
                ],

            "power_headroom_kw":
                result[
                    "power_headroom_kw"
                ],

            "gpu_utilization_percent":
                result[
                    "gpu_utilization_percent"
                ],

            "missed_deadlines":
                result[
                    "missed_deadlines"
                ],

            "power_violations":
                result[
                    "power_violations"
                ],

            "unserved_energy_kwh":
                result[
                    "unserved_energy_kwh"
                ],

            "total_cost":
                result[
                    "total_cost"
                ],

            "feasible":
                result[
                    "feasible"
                ],
        })


        if result["feasible"]:

            last_feasible = result

        else:

            first_infeasible = result

            break


    # --------------------------------------------------------
    # Determine capacity
    # --------------------------------------------------------

    if last_feasible is None:

        maximum_safe_gpus = 0

        additional_safe_gpus = (
            -current_gpus
        )

    else:

        maximum_safe_gpus = (
            last_feasible[
                "num_gpus"
            ]
        )

        additional_safe_gpus = (
            maximum_safe_gpus
            - current_gpus
        )


    # --------------------------------------------------------
    # Determine limiting factor
    # --------------------------------------------------------

    limiting_factor = (
        determine_limiting_factor(
            last_feasible,
            first_infeasible,
            power_limit_kw,
        )
    )


    return {

        "current_gpus":
            current_gpus,

        "maximum_safe_gpus":
            maximum_safe_gpus,

        "additional_safe_gpus":
            max(
                0,
                additional_safe_gpus,
            ),

        "limiting_factor":
            limiting_factor,

        "last_feasible":
            last_feasible,

        "first_infeasible":
            first_infeasible,

        "results":
            pd.DataFrame(results),
    }


# ============================================================
# DETERMINE LIMITING FACTOR
# ============================================================

def determine_limiting_factor(
    last_feasible: dict,
    first_infeasible: dict,
    power_limit_kw: float,
) -> str:

    if first_infeasible is None:

        return (
            "No modeled capacity limit "
            "reached within the test range."
        )


    if (
        first_infeasible[
            "power_violations"
        ] > 0
    ):

        return (
            "Power capacity"
        )


    if (
        first_infeasible[
            "missed_deadlines"
        ] > 0
    ):

        return (
            "Workload deadline capacity"
        )


    if (
        first_infeasible[
            "unserved_energy_kwh"
        ] > 0.001
    ):

        return (
            "Energy supply capacity"
        )


    if (
        first_infeasible[
            "peak_power_kw"
        ] > power_limit_kw
    ):

        return (
            "Data-center power limit"
        )


    return (
        "Scheduling capacity"
    )


# ============================================================
# CAPACITY EXPANSION SCENARIO
# ============================================================

def simulate_gpu_expansion(
    jobs: pd.DataFrame,
    additional_gpus: int,
    current_gpus: int = DEFAULT_NUM_GPUS,
    power_limit_kw: float = DEFAULT_POWER_LIMIT_KW,
) -> dict:

    # --------------------------------------------------------
    # Prepare workloads
    # --------------------------------------------------------

    jobs = prepare_jobs(
        jobs
    )


    # --------------------------------------------------------
    # Energy environment
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
    # New GPU capacity
    # --------------------------------------------------------

    new_gpu_capacity = (
        current_gpus
        + additional_gpus
    )


    # --------------------------------------------------------
    # Evaluate
    # --------------------------------------------------------

    result = evaluate_gpu_capacity(
        jobs,
        new_gpu_capacity,
        power_limit_kw,
        prices,
        grid_capacity,
        solar_power,
        battery_power,
    )


    result["current_gpus"] = (
        current_gpus
    )

    result["additional_gpus"] = (
        additional_gpus
    )

    result["new_gpu_capacity"] = (
        new_gpu_capacity
    )


    return result


# ============================================================
# PRINT CAPACITY REPORT
# ============================================================

def print_capacity_report(
    result: dict,
) -> None:

    print()
    print("=" * 70)
    print(
        "ZYVARENTH POWEROS — CAPACITY PLANNING"
    )
    print("=" * 70)


    # --------------------------------------------------------
    # Current capacity
    # --------------------------------------------------------

    print()
    print("CURRENT CAPACITY")
    print("-" * 70)

    print(
        f"Current GPUs           : "
        f"{result['current_gpus']}"
    )

    print(
        f"Maximum safe GPUs      : "
        f"{result['maximum_safe_gpus']}"
    )

    print(
        f"Additional safe GPUs   : "
        f"{result['additional_safe_gpus']}"
    )

    print(
        f"Limiting factor        : "
        f"{result['limiting_factor']}"
    )


    # --------------------------------------------------------
    # Last feasible point
    # --------------------------------------------------------

    if result["last_feasible"]:

        safe = result[
            "last_feasible"
        ]

        print()
        print("LAST SAFE CAPACITY")
        print("-" * 70)

        print(
            f"GPU capacity           : "
            f"{safe['num_gpus']}"
        )

        print(
            f"Peak power             : "
            f"{safe['peak_power_kw']:.2f} kW"
        )

        print(
            f"Power headroom         : "
            f"{safe['power_headroom_kw']:.2f} kW"
        )

        print(
            f"GPU utilization        : "
            f"{safe['gpu_utilization_percent']:.2f}%"
        )

        print(
            f"Missed deadlines       : "
            f"{safe['missed_deadlines']}"
        )

        print(
            f"Power violations       : "
            f"{safe['power_violations']}"
        )

        print(
            f"Unserved energy        : "
            f"{safe['unserved_energy_kwh']:.2f} kWh"
        )

        print(
            f"Estimated energy cost  : "
            f"₹{safe['total_cost']:.2f}"
        )


    # --------------------------------------------------------
    # First unsafe point
    # --------------------------------------------------------

    if result["first_infeasible"]:

        unsafe = result[
            "first_infeasible"
        ]

        print()
        print("FIRST UNSAFE CAPACITY")
        print("-" * 70)

        print(
            f"GPU capacity           : "
            f"{unsafe['num_gpus']}"
        )

        print(
            f"Peak power             : "
            f"{unsafe['peak_power_kw']:.2f} kW"
        )

        print(
            f"Missed deadlines       : "
            f"{unsafe['missed_deadlines']}"
        )

        print(
            f"Power violations       : "
            f"{unsafe['power_violations']}"
        )

        print(
            f"Unserved energy        : "
            f"{unsafe['unserved_energy_kwh']:.2f} kWh"
        )


    # --------------------------------------------------------
    # Decision
    # --------------------------------------------------------

    print()
    print("POWEROS CAPACITY DECISION")
    print("-" * 70)

    if result[
        "additional_safe_gpus"
    ] > 0:

        print(
            f"The modeled facility can support "
            f"approximately "
            f"{result['additional_safe_gpus']} "
            f"additional GPUs under the current "
            f"workload and energy assumptions."
        )

    else:

        print(
            "No additional GPU capacity is "
            "currently supported under the "
            "modeled constraints."
        )


    print()
    print("=" * 70)
    print()


# ============================================================
# STANDARD CAPACITY SCENARIOS
# ============================================================

def run_capacity_scenarios(
    jobs: pd.DataFrame,
    current_gpus: int = DEFAULT_NUM_GPUS,
    power_limit_kw: float = DEFAULT_POWER_LIMIT_KW,
) -> pd.DataFrame:

    expansion_levels = [
        0,
        10,
        25,
        50,
        100,
        200,
    ]


    rows = []


    for additional_gpus in (
        expansion_levels
    ):

        result = simulate_gpu_expansion(
            jobs,
            additional_gpus,
            current_gpus,
            power_limit_kw,
        )


        rows.append({

            "additional_gpus":
                additional_gpus,

            "total_gpu_capacity":
                result[
                    "new_gpu_capacity"
                ],

            "peak_power_kw":
                result[
                    "peak_power_kw"
                ],

            "gpu_utilization_percent":
                result[
                    "gpu_utilization_percent"
                ],

            "total_cost":
                result[
                    "total_cost"
                ],

            "missed_deadlines":
                result[
                    "missed_deadlines"
                ],

            "power_violations":
                result[
                    "power_violations"
                ],

            "unserved_energy_kwh":
                result[
                    "unserved_energy_kwh"
                ],

            "feasible":
                result[
                    "feasible"
                ],
        })


    return pd.DataFrame(
        rows
    )


# ============================================================
# END OF CAPACITY PLANNING ENGINE
# ============================================================