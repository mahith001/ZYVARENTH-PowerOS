from copy import deepcopy
from typing import Dict

from poweros.core.models import DataCenterState

from poweros.intelligence.state_analyzer import (
    analyze_state,
)

from poweros.intelligence.optimizer import (
    optimize_workloads,
    summarize_optimization,
)

from poweros.decisions.decision_engine import (
    create_decisions,
    summarize_decisions,
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_scheduled_count(
    optimization_summary: Dict,
) -> int:
    """
    Get scheduled workload count using the current
    optimizer interface, with backward compatibility.
    """

    return optimization_summary.get(
        "scheduled_count",
        optimization_summary.get(
            "scheduled_workloads",
            0,
        ),
    )


def get_unscheduled_count(
    optimization_summary: Dict,
) -> int:
    """
    Get unscheduled workload count using the current
    optimizer interface, with backward compatibility.
    """

    return optimization_summary.get(
        "unscheduled_count",
        optimization_summary.get(
            "unscheduled_workloads",
            0,
        ),
    )


def get_total_count(
    optimization_summary: Dict,
) -> int:
    """
    Get total workload count using the current
    optimizer interface, with backward compatibility.
    """

    return optimization_summary.get(
        "total_count",
        optimization_summary.get(
            "total_workloads",
            0,
        ),
    )


# =========================================================
# SIMULATION RESULT
# =========================================================

def build_simulation_result(
    scenario_name: str,
    state_analysis: Dict,
    optimization_summary: Dict,
    decision_summary: Dict,
) -> Dict:
    """
    Build a standardized result for one simulation scenario.
    """

    scheduled_workloads = get_scheduled_count(
        optimization_summary
    )

    unscheduled_workloads = get_unscheduled_count(
        optimization_summary
    )

    total_workloads = get_total_count(
        optimization_summary
    )

    return {
        "scenario": scenario_name,

        # -------------------------------------------------
        # STATE
        # -------------------------------------------------

        "status": state_analysis.get(
            "status",
            "UNKNOWN",
        ),

        "bottleneck": state_analysis.get(
            "primary_bottleneck",
            "NONE",
        ),

        "power_pressure_percent": state_analysis.get(
            "power_pressure_percent",
            0.0,
        ),

        "power_headroom_kw": state_analysis.get(
            "power_headroom_kw",
            0.0,
        ),

        # -------------------------------------------------
        # OPTIMIZATION
        # -------------------------------------------------

        "scheduled_workloads": scheduled_workloads,

        "unscheduled_workloads": unscheduled_workloads,

        "total_workloads": total_workloads,

        # -------------------------------------------------
        # DECISIONS
        # -------------------------------------------------

        "run_decisions": decision_summary.get(
            "run",
            decision_summary.get(
                "run_decisions",
                0,
            ),
        ),

        "shift_decisions": decision_summary.get(
            "shift",
            decision_summary.get(
                "shift_decisions",
                0,
            ),
        ),

        "deadline_protection_decisions": decision_summary.get(
            "protect_deadline",
            decision_summary.get(
                "deadline_protection_decisions",
                0,
            ),
        ),
    }


# =========================================================
# RUN ONE SIMULATION
# =========================================================

def simulate_scenario(
    state: DataCenterState,
    scenario_name: str,
) -> Dict:
    """
    Run PowerOS against one simulated scenario.
    """

    # -----------------------------------------------------
    # Create isolated copy
    # -----------------------------------------------------

    state_copy = deepcopy(state)

    # -----------------------------------------------------
    # Analyze simulated state
    # -----------------------------------------------------

    state_analysis = analyze_state(
        state_copy
    )

    # -----------------------------------------------------
    # Optimize workloads
    # -----------------------------------------------------

    schedule = optimize_workloads(
        state=state_copy,
        horizon_hours=24,
    )

    # -----------------------------------------------------
    # Summarize optimization
    # -----------------------------------------------------

    optimization_summary = summarize_optimization(
        schedule
    )

    # -----------------------------------------------------
    # Convert optimization into decisions
    # -----------------------------------------------------

    decisions = create_decisions(
        schedule,
        current_hour=0,
    )

    # -----------------------------------------------------
    # Summarize decisions
    # -----------------------------------------------------

    decision_summary = summarize_decisions(
        decisions
    )

    # -----------------------------------------------------
    # Build result
    # -----------------------------------------------------

    return build_simulation_result(
        scenario_name=scenario_name,
        state_analysis=state_analysis,
        optimization_summary=optimization_summary,
        decision_summary=decision_summary,
    )


# =========================================================
# POWER REDUCTION SCENARIO
# =========================================================

def simulate_power_reduction(
    state: DataCenterState,
    reduction_percent: float = 20.0,
) -> Dict:
    """
    Simulate reduced available power.
    """

    scenario = deepcopy(state)

    if scenario.power:
        scenario.power.available_power_kw *= (
            1 - reduction_percent / 100
        )

    return simulate_scenario(
        scenario,
        f"POWER_REDUCTION_{reduction_percent}%",
    )


# =========================================================
# ELECTRICITY PRICE INCREASE
# =========================================================

def simulate_price_increase(
    state: DataCenterState,
    increase_percent: float = 25.0,
) -> Dict:
    """
    Simulate increased electricity price.
    """

    scenario = deepcopy(state)

    if scenario.power:
        scenario.power.electricity_price_per_kwh *= (
            1 + increase_percent / 100
        )

    return simulate_scenario(
        scenario,
        f"PRICE_INCREASE_{increase_percent}%",
    )


# =========================================================
# SOLAR REDUCTION
# =========================================================

def simulate_solar_reduction(
    state: DataCenterState,
    reduction_percent: float = 50.0,
) -> Dict:
    """
    Simulate reduced solar availability.
    """

    scenario = deepcopy(state)

    if scenario.power:
        scenario.power.solar_power_kw *= (
            1 - reduction_percent / 100
        )

    return simulate_scenario(
        scenario,
        f"SOLAR_REDUCTION_{reduction_percent}%",
    )


# =========================================================
# GPU DEMAND INCREASE
# =========================================================

def simulate_gpu_demand_increase(
    state: DataCenterState,
    additional_gpu_percent: float = 30.0,
) -> Dict:
    """
    Simulate increased GPU demand from workloads.
    """

    scenario = deepcopy(state)

    for workload in scenario.workloads:

        workload.gpu_required = max(
            1,
            int(
                workload.gpu_required
                * (
                    1
                    + additional_gpu_percent
                    / 100
                )
            ),
        )

    return simulate_scenario(
        scenario,
        f"GPU_DEMAND_{additional_gpu_percent}%",
    )


# =========================================================
# RUN STANDARD SCENARIOS
# =========================================================

def run_standard_scenarios(
    state: DataCenterState,
) -> Dict:
    """
    Run the standard PowerOS simulation scenarios.
    """

    results = {}

    # -----------------------------------------------------
    # BASELINE
    # -----------------------------------------------------

    results["BASELINE"] = simulate_scenario(
        state,
        "BASELINE",
    )

    # -----------------------------------------------------
    # POWER REDUCTION
    # -----------------------------------------------------

    results["POWER_REDUCTION_20%"] = (
        simulate_power_reduction(
            state,
            20,
        )
    )

    # -----------------------------------------------------
    # PRICE INCREASE
    # -----------------------------------------------------

    results["PRICE_INCREASE_25%"] = (
        simulate_price_increase(
            state,
            25,
        )
    )

    # -----------------------------------------------------
    # SOLAR REDUCTION
    # -----------------------------------------------------

    results["SOLAR_REDUCTION_50%"] = (
        simulate_solar_reduction(
            state,
            50,
        )
    )

    # -----------------------------------------------------
    # GPU DEMAND INCREASE
    # -----------------------------------------------------

    results["GPU_DEMAND_30%"] = (
        simulate_gpu_demand_increase(
            state,
            30,
        )
    )

    return results


# =========================================================
# COMPARISON TABLE
# =========================================================

def compare_scenarios(
    results: Dict,
):
    """
    Convert simulation results into comparison rows.
    """

    rows = []

    for name, result in results.items():

        rows.append(
            {
                "scenario": name,

                "status": result.get(
                    "status",
                    "UNKNOWN",
                ),

                "bottleneck": result.get(
                    "bottleneck",
                    "NONE",
                ),

                "power_pressure_percent": result.get(
                    "power_pressure_percent",
                    0.0,
                ),

                "power_headroom_kw": result.get(
                    "power_headroom_kw",
                    0.0,
                ),

                "scheduled_workloads": result.get(
                    "scheduled_workloads",
                    0,
                ),

                "unscheduled_workloads": result.get(
                    "unscheduled_workloads",
                    0,
                ),

                "run_decisions": result.get(
                    "run_decisions",
                    0,
                ),

                "shift_decisions": result.get(
                    "shift_decisions",
                    0,
                ),

                "deadline_protection": result.get(
                    "deadline_protection_decisions",
                    0,
                ),
            }
        )

    return rows


# =========================================================
# PRINT SIMULATION REPORT
# =========================================================

def print_simulation_report(
    results: Dict,
):
    """
    Print a readable PowerOS simulation report.
    """

    print()

    print("=" * 70)
    print("POWEROS SIMULATION ENGINE")
    print("=" * 70)

    for name, result in results.items():

        print()

        print(
            f"SCENARIO: {name}"
        )

        print(
            f"Status: "
            f"{result.get('status', 'UNKNOWN')}"
        )

        print(
            f"Bottleneck: "
            f"{result.get('bottleneck', 'NONE')}"
        )

        print(
            f"Power pressure: "
            f"{result.get('power_pressure_percent', 0.0)}%"
        )

        print(
            f"Power headroom: "
            f"{result.get('power_headroom_kw', 0.0)} kW"
        )

        print(
            f"Scheduled workloads: "
            f"{result.get('scheduled_workloads', 0)}"
        )

        print(
            f"Unscheduled workloads: "
            f"{result.get('unscheduled_workloads', 0)}"
        )

        print(
            f"RUN decisions: "
            f"{result.get('run_decisions', 0)}"
        )

        print(
            f"SHIFT decisions: "
            f"{result.get('shift_decisions', 0)}"
        )

        print(
            f"Deadline protection: "
            f"{result.get('deadline_protection_decisions', 0)}"
        )

    print()

    print("=" * 70)