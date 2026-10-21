"""
ZYVARENTH PowerOS
Scenario Simulator

Runs the existing PowerOS simulation engine
under different operating conditions.
"""

import inspect

from poweros.data.fair_baseline import (
    create_realistic_state,
)

from poweros.simulation.simulator import (
    simulate_power_reduction,
    simulate_price_increase,
    simulate_solar_reduction,
    simulate_gpu_demand_increase,
)


def call_scenario_function(
    function,
    state,
    change_value,
):
    """
    Call an existing simulator function without
    assuming the exact parameter name.

    This keeps the scenario API compatible with
    the existing PowerOS simulator.
    """

    signature = inspect.signature(
        function
    )

    parameters = list(
        signature.parameters.values()
    )

    # ---------------------------------------------------------
    # Find parameters other than state
    # ---------------------------------------------------------

    change_parameter = None

    for parameter in parameters:

        name = parameter.name.lower()

        if name in {
            "state",
            "data_center_state",
            "datacenter_state",
        }:

            continue

        if (
            parameter.kind
            in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            )
        ):

            change_parameter = parameter

            break

    # ---------------------------------------------------------
    # Function only needs state
    # ---------------------------------------------------------

    if change_parameter is None:

        return function(
            state
        )

    # ---------------------------------------------------------
    # Decide value based on parameter name
    # ---------------------------------------------------------

    parameter_name = (
        change_parameter.name.lower()
    )

    # Percentage-based parameter
    if (
        "percent" in parameter_name
        or "percentage" in parameter_name
    ):

        value = change_value

    # Multiplier / factor
    elif (
        "factor" in parameter_name
        or "multiplier" in parameter_name
    ):

        value = 1.0 + (
            change_value / 100.0
        )

    # Default
    else:

        value = change_value

    # ---------------------------------------------------------
    # Call using detected parameter name
    # ---------------------------------------------------------

    return function(
        state=state,
        **{
            change_parameter.name: value
        },
    )


def run_scenario(
    scenario_name
):
    """
    Run one PowerOS scenario.
    """

    state = create_realistic_state()

    # ---------------------------------------------------------
    # POWER REDUCTION
    # ---------------------------------------------------------

    if scenario_name == "power_reduction":

        return call_scenario_function(
            simulate_power_reduction,
            state,
            20.0,
        )

    # ---------------------------------------------------------
    # PRICE INCREASE
    # ---------------------------------------------------------

    elif scenario_name == "price_increase":

        return call_scenario_function(
            simulate_price_increase,
            state,
            50.0,
        )

    # ---------------------------------------------------------
    # SOLAR REDUCTION
    # ---------------------------------------------------------

    elif scenario_name == "solar_reduction":

        return call_scenario_function(
            simulate_solar_reduction,
            state,
            50.0,
        )

    # ---------------------------------------------------------
    # GPU DEMAND INCREASE
    # ---------------------------------------------------------

    elif scenario_name == "gpu_demand_increase":

        return call_scenario_function(
            simulate_gpu_demand_increase,
            state,
            30.0,
        )

    # ---------------------------------------------------------
    # UNKNOWN SCENARIO
    # ---------------------------------------------------------

    else:

        return {
            "success": False,
            "error": (
                "Unknown scenario: "
                + scenario_name
            ),
        }


def get_result_value(
    result,
    *keys,
    default=0,
):
    """
    Safely retrieve a result value.
    """

    if not isinstance(
        result,
        dict,
    ):

        return default

    for key in keys:

        if key in result:

            return result[key]

    return default


def print_scenario_result(
    scenario_name,
    result,
):
    """
    Print a clean scenario result.
    """

    print()

    print("=" * 70)

    print(
        "SCENARIO:",
        scenario_name.upper(),
    )

    print("=" * 70)

    if not isinstance(
        result,
        dict,
    ):

        print(result)

        return

    print()

    print(
        "Status:",
        get_result_value(
            result,
            "status",
            default="UNKNOWN",
        ),
    )

    print(
        "Bottleneck:",
        get_result_value(
            result,
            "bottleneck",
            default="NONE",
        ),
    )

    print(
        "Power Pressure:",
        get_result_value(
            result,
            "power_pressure_percent",
            "power_pressure",
            default=0,
        ),
        "%",
    )

    print(
        "Power Headroom:",
        get_result_value(
            result,
            "power_headroom_kw",
            "power_headroom",
            default=0,
        ),
        "kW",
    )

    print(
        "Scheduled Workloads:",
        get_result_value(
            result,
            "scheduled_workloads",
            "scheduled_count",
            default=0,
        ),
    )

    print(
        "Unscheduled Workloads:",
        get_result_value(
            result,
            "unscheduled_workloads",
            "unscheduled_count",
            default=0,
        ),
    )

    print(
        "RUN Decisions:",
        get_result_value(
            result,
            "run_decisions",
            "run",
            default=0,
        ),
    )

    print(
        "SHIFT Decisions:",
        get_result_value(
            result,
            "shift_decisions",
            "shift",
            default=0,
        ),
    )

    print(
        "Deadline Protection:",
        get_result_value(
            result,
            "deadline_protection_decisions",
            "protect_deadline",
            default=0,
        ),
    )


def main():

    print()

    print("=" * 70)

    print(
        "ZYVARENTH POWEROS SCENARIO SIMULATOR"
    )

    print("=" * 70)

    scenarios = [

        "power_reduction",

        "price_increase",

        "solar_reduction",

        "gpu_demand_increase",

    ]

    for scenario in scenarios:

        try:

            result = run_scenario(
                scenario
            )

            print_scenario_result(
                scenario,
                result,
            )

        except Exception as error:

            print()

            print(
                "SCENARIO ERROR:",
                scenario.upper(),
            )

            print(
                type(error).__name__,
                ":",
                error,
            )

            print()

    print()

    print("=" * 70)

    print(
        "SCENARIO SIMULATOR TEST COMPLETED"
    )

    print("=" * 70)


if __name__ == "__main__":

    main()