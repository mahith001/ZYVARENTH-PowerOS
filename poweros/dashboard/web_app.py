"""
ZYVARENTH PowerOS
Web Dashboard + Scenario API
"""

from flask import Flask, render_template, jsonify, request

from poweros.data.fair_baseline import (
    create_realistic_state,
    create_realistic_prices,
    create_realistic_solar,
)

from poweros.core.orchestrator import run_poweros

from poweros.dashboard.scenario_api import (
    run_scenario,
    get_result_value,
)
from poweros.dashboard.customer_api import customer_api


app = Flask(__name__)

app.register_blueprint(customer_api)
# ============================================================
# SAFE VALUE HELPERS
# ============================================================

def safe_float(value, default=0.0):

    try:
        return float(value)

    except (TypeError, ValueError):

        return default


def safe_int(value, default=0):

    try:
        return int(value)

    except (TypeError, ValueError):

        return default


def get_value(
    data,
    *keys,
    default=0,
):

    if not isinstance(data, dict):

        return default

    for key in keys:

        if key in data:

            return data[key]

    return default


# ============================================================
# PREPARE DECISIONS
# ============================================================

def prepare_decisions(decisions):

    prepared = []

    if not isinstance(
        decisions,
        list,
    ):

        return prepared

    for item in decisions:

        if not isinstance(
            item,
            dict,
        ):

            continue

        prepared.append(
            {
                "workload_id": item.get(
                    "workload_id",
                    item.get(
                        "id",
                        "UNKNOWN",
                    ),
                ),

                "decision": item.get(
                    "decision",
                    item.get(
                        "action",
                        "WAIT",
                    ),
                ),

                "action": item.get(
                    "action",
                    item.get(
                        "decision",
                        "WAIT",
                    ),
                ),

                "start_hour": item.get(
                    "start_hour",
                    None,
                ),

                "finish_hour": item.get(
                    "finish_hour",
                    None,
                ),

                "deadline_hour": item.get(
                    "deadline_hour",
                    None,
                ),

                "priority": item.get(
                    "priority",
                    "MEDIUM",
                ),

                "reason": item.get(
                    "reason",
                    "PowerOS optimization decision",
                ),
            }
        )

    return prepared


# ============================================================
# MAIN DASHBOARD DATA
# ============================================================

def build_dashboard_data():

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

    state_analysis = result.get(
        "state_analysis",
        {},
    )

    power_summary = result.get(
        "power_summary",
        {},
    )

    decision_summary = result.get(
        "decision_summary",
        {},
    )

    dispatch = result.get(
        "battery_dispatch",
        {},
    )

    schedule = result.get(
        "schedule",
        {},
    )

    optimization = result.get(
        "optimization_summary",
        {},
    )

    decisions = result.get(
        "decisions",
        [],
    )

    scheduled = schedule.get(
        "scheduled",
        [],
    )

    unscheduled = schedule.get(
        "unscheduled",
        [],
    )

    cost = get_value(
        dispatch,
        "total_cost",
        "total_energy_cost",
        "cost",
        default=0.0,
    )

    solar_used = get_value(
        dispatch,
        "solar_energy_used_kwh",
        "solar_used_kwh",
        "solar_used",
        default=0.0,
    )

    battery_used = get_value(
        dispatch,
        "battery_energy_used_kwh",
        "battery_used_kwh",
        "battery_used",
        default=0.0,
    )

    peak_power = get_value(
        power_summary,
        "peak_facility_power_kw",
        "peak_power_kw",
        default=0.0,
    )

    power_headroom = get_value(
        state_analysis,
        "power_headroom_kw",
        default=0.0,
    )

    power_pressure = get_value(
        state_analysis,
        "power_pressure_percent",
        default=0.0,
    )

    return {

        "status": state_analysis.get(
            "status",
            "UNKNOWN",
        ),

        "bottleneck": state_analysis.get(
            "primary_bottleneck",
            "NONE",
        ),

        "power_pressure": safe_float(
            power_pressure
        ),

        "power_headroom": safe_float(
            power_headroom
        ),

        "peak_power": safe_float(
            peak_power
        ),

        "scheduled": len(
            scheduled
        ),

        "unscheduled": len(
            unscheduled
        ),

        "total_workloads": len(
            state.workloads
        ),

        "cost": safe_float(
            cost
        ),

        "solar": safe_float(
            solar_used
        ),

        "battery": safe_float(
            battery_used
        ),

        "run": safe_int(
            get_value(
                decision_summary,
                "run_decisions",
                "run",
                default=0,
            )
        ),

        "wait": safe_int(
            get_value(
                decision_summary,
                "wait_decisions",
                "wait",
                default=0,
            )
        ),

        "shift": safe_int(
            get_value(
                decision_summary,
                "shift_decisions",
                "shift",
                default=0,
            )
        ),

        "protect": safe_int(
            get_value(
                decision_summary,
                "protect_deadline_decisions",
                "protect_deadline",
                default=0,
            )
        ),

        "power_demand": [
            safe_float(value)
            for value in result.get(
                "power_demand_by_hour",
                [],
            )
        ],

        "prices": [
            safe_float(value)
            for value in prices
        ],

        "solar_forecast": [
            safe_float(value)
            for value in solar
        ],

        "scheduled_workloads": [

            {
                "workload_id": item.get(
                    "workload_id",
                    "UNKNOWN",
                ),

                "start_hour": item.get(
                    "start_hour",
                    None,
                ),

                "finish_hour": item.get(
                    "finish_hour",
                    None,
                ),

                "gpu_required": item.get(
                    "gpu_required",
                    0,
                ),

                "power_kw": item.get(
                    "power_kw",
                    0,
                ),

                "deadline_hour": item.get(
                    "deadline_hour",
                    None,
                ),

                "priority": item.get(
                    "priority",
                    "MEDIUM",
                ),
            }

            for item in scheduled
            if isinstance(
                item,
                dict,
            )

        ],

        "decisions": prepare_decisions(
            decisions
        ),

        "optimization": {

            "scheduled_count":
                get_value(
                    optimization,
                    "scheduled_count",
                    default=len(
                        scheduled
                    ),
                ),

            "unscheduled_count":
                get_value(
                    optimization,
                    "unscheduled_count",
                    default=len(
                        unscheduled
                    ),
                ),

            "success_rate_percent":
                get_value(
                    optimization,
                    "success_rate_percent",
                    default=0,
                ),
        },
    }


# ============================================================
# SCENARIO API
# ============================================================

@app.route(
    "/api/scenario",
    methods=["GET"],
)
def scenario_api():

    scenario = request.args.get(
        "scenario",
        "",
    ).strip()

    allowed_scenarios = {

        "power_reduction",

        "price_increase",

        "solar_reduction",

        "gpu_demand_increase",

    }

    if scenario not in allowed_scenarios:

        return jsonify(
            {
                "success": False,

                "error":
                    "Invalid scenario",

                "allowed_scenarios":
                    sorted(
                        allowed_scenarios
                    ),
            }
        ), 400

    try:

        result = run_scenario(
            scenario
        )

        if not isinstance(
            result,
            dict,
        ):

            result = {
                "result": result
            }

        return jsonify(
            {
                "success": True,

                "scenario":
                    scenario,

                "status":
                    get_result_value(
                        result,
                        "status",
                        default="UNKNOWN",
                    ),

                "bottleneck":
                    get_result_value(
                        result,
                        "bottleneck",
                        default="NONE",
                    ),

                "power_pressure":
                    safe_float(
                        get_result_value(
                            result,
                            "power_pressure_percent",
                            "power_pressure",
                            default=0,
                        )
                    ),

                "power_headroom":
                    safe_float(
                        get_result_value(
                            result,
                            "power_headroom_kw",
                            "power_headroom",
                            default=0,
                        )
                    ),

                "scheduled":
                    safe_int(
                        get_result_value(
                            result,
                            "scheduled_workloads",
                            "scheduled_count",
                            default=0,
                        )
                    ),

                "unscheduled":
                    safe_int(
                        get_result_value(
                            result,
                            "unscheduled_workloads",
                            "unscheduled_count",
                            default=0,
                        )
                    ),

                "run":
                    safe_int(
                        get_result_value(
                            result,
                            "run_decisions",
                            "run",
                            default=0,
                        )
                    ),

                "shift":
                    safe_int(
                        get_result_value(
                            result,
                            "shift_decisions",
                            "shift",
                            default=0,
                        )
                    ),

                "protect":
                    safe_int(
                        get_result_value(
                            result,
                            "deadline_protection_decisions",
                            "protect_deadline",
                            default=0,
                        )
                    ),
            }
        )

    except Exception as error:

        return jsonify(
            {
                "success": False,

                "scenario":
                    scenario,

                "error":
                    str(error),
            }
        ), 500


# ============================================================
# DASHBOARD PAGE
# ============================================================

@app.route("/")
def dashboard():

    return render_template(
        "dashboard.html"
    )


# ============================================================
# MAIN DASHBOARD API
# ============================================================

@app.route(
    "/api/dashboard"
)
def dashboard_api():

    return jsonify(
        build_dashboard_data()
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    print()

    print("=" * 70)

    print(
        "ZYVARENTH POWEROS WEB DASHBOARD"
    )

    print("=" * 70)

    print()

    print(
        "Dashboard:"
    )

    print(
        "http://127.0.0.1:5000"
    )

    print()

    print(
        "Dashboard API:"
    )

    print(
        "http://127.0.0.1:5000/api/dashboard"
    )

    print()

    print(
        "Scenario API:"
    )

    print(
        "http://127.0.0.1:5000/api/scenario?scenario=power_reduction"
    )

    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
    )