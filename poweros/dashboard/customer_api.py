
"""
ZYVARENTH PowerOS
Customer API

Accepts customer infrastructure and workload data,
runs the real PowerOS orchestrator, and returns
scheduling results and decisions.
"""

import logging
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum

from flask import Blueprint, jsonify, request

from poweros.data.customer_config import (
    CustomerConfiguration,
    CustomerGPU,
    CustomerWorkload,
    CustomerPower,
    CustomerEnergyResource,
)
from poweros.data.customer_adapter import customer_to_poweros_state
from poweros.core.orchestrator import run_poweros


customer_api = Blueprint("customer_api", __name__)


def make_json_safe(value):
    """Convert Python objects into JSON-compatible values."""

    if is_dataclass(value):
        return make_json_safe(asdict(value))

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [make_json_safe(item) for item in value]

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if hasattr(value, "__dict__"):
        return make_json_safe(vars(value))

    return str(value)


def build_customer_from_json(data):
    """Validate and construct a customer configuration."""

    if not isinstance(data, dict):
        raise ValueError("Request must contain a JSON object.")

    for key in ("customer_name", "gpus", "workloads", "power"):
        if key not in data:
            raise ValueError(f"Missing required field: {key}")

    if not isinstance(data["gpus"], list):
        raise ValueError("'gpus' must be a list.")

    if not isinstance(data["workloads"], list):
        raise ValueError("'workloads' must be a list.")

    if not isinstance(data["power"], dict):
        raise ValueError("'power' must be an object.")

    gpus = [
        CustomerGPU(
            gpu_id=item["gpu_id"],
            power_kw=item.get("power_kw", 0.7),
            utilization_percent=item.get("utilization_percent", 0),
            temperature_c=item.get("temperature_c", 60),
            memory_utilization_percent=item.get(
                "memory_utilization_percent", 0
            ),
            available=item.get("available", True),
        )
        for item in data["gpus"]
    ]

    workloads = [
        CustomerWorkload(
            workload_id=item["workload_id"],
            gpu_required=item["gpu_required"],
            duration_hours=item["duration_hours"],
            deadline_hour=item["deadline_hour"],
            priority=item.get("priority", "MEDIUM"),
        )
        for item in data["workloads"]
    ]

    power_data = data["power"]

    power = CustomerPower(
        available_power_kw=power_data["available_power_kw"],
        grid_capacity_kw=power_data["grid_capacity_kw"],
        electricity_price_per_kwh=power_data[
            "electricity_price_per_kwh"
        ],
        solar_power_kw=power_data.get("solar_power_kw", 0),
        battery_available_kw=power_data.get(
            "battery_available_kw", 0
        ),
    )

    resources = [
        CustomerEnergyResource(
            name=item["name"],
            available_power_kw=item["available_power_kw"],
            cost_per_kwh=item["cost_per_kwh"],
            renewable=item.get("renewable", False),
        )
        for item in data.get("energy_resources", [])
    ]

    customer = CustomerConfiguration(
        customer_name=data["customer_name"],
        gpus=gpus,
        workloads=workloads,
        power=power,
        energy_resources=resources,
        pue=data.get("pue", 1.3),
    )

    customer.validate()

    if not customer.gpus:
        raise ValueError("Add at least one GPU.")

    if not customer.workloads:
        raise ValueError("Add at least one workload.")

    gpu_ids = [gpu.gpu_id for gpu in customer.gpus]
    if len(gpu_ids) != len(set(gpu_ids)):
        raise ValueError("GPU IDs must be unique.")

    workload_ids = [
        workload.workload_id for workload in customer.workloads
    ]
    if len(workload_ids) != len(set(workload_ids)):
        raise ValueError("Workload IDs must be unique.")

    return customer


def create_customer_prices(customer):
    """Create a 24-hour illustrative electricity-price profile."""

    base = customer.power.electricity_price_per_kwh

    multipliers = [
        1.00, 1.00, 1.00, 1.00,
        0.95, 0.90, 0.85, 0.80,
        0.75, 0.72, 0.70, 0.72,
        0.76, 0.82, 0.88, 0.95,
        1.05, 1.15, 1.20, 1.15,
        1.10, 1.08, 1.05, 1.00,
    ]

    return [base * factor for factor in multipliers]


def create_customer_solar(customer):
    """Create a 24-hour illustrative solar profile."""

    solar = customer.power.solar_power_kw

    fractions = [
        0, 0, 0, 0,
        0.10, 0.25, 0.40, 0.60,
        0.80, 0.90, 1.00, 1.00,
        1.00, 0.90, 0.75, 0.55,
        0.35, 0.15, 0.05, 0,
        0, 0, 0, 0,
    ]

    return [solar * fraction for fraction in fractions]


def get_workload_id(item):
    """Extract a workload ID from a result record."""

    if not isinstance(item, dict):
        return None

    return item.get("workload_id", item.get("id"))


def get_status(item):
    """Normalize a workload status."""

    if not isinstance(item, dict):
        return ""

    return str(item.get("status", "")).strip().upper()


def classify_decisions(decisions):
    """
    Use the actual decision records to recover workload outcomes.

    A SHIFT or PROTECT_DEADLINE action can still have a
    SCHEDULED status. Scheduling status and decision action
    represent different things.
    """

    if isinstance(decisions, dict):
        decisions = decisions.get("decisions", [])

    if not isinstance(decisions, list):
        return [], []

    scheduled = []
    unscheduled = []

    for item in decisions:
        if not isinstance(item, dict):
            continue

        status = get_status(item)

        if status == "SCHEDULED":
            scheduled.append(item)
        elif status in {
            "UNSCHEDULED",
            "FAILED",
            "REJECTED",
            "NOT_SCHEDULED",
        }:
            unscheduled.append(item)

    return scheduled, unscheduled


def extract_workload_outcomes(optimization, decisions):
    """
    Extract actual scheduled and unscheduled workload records.

    Prefer the optimizer's populated lists. If those lists are
    empty or missing, recover outcomes from decision records.
    """

    if not isinstance(optimization, dict):
        optimization = {}

    scheduled = optimization.get("scheduled", [])
    unscheduled = optimization.get("unscheduled", [])

    # Support alternate key names from different result formats.
    if not scheduled:
        scheduled = optimization.get("scheduled_workloads", [])

    if not unscheduled:
        unscheduled = optimization.get("unscheduled_workloads", [])

    if not isinstance(scheduled, list):
        scheduled = []

    if not isinstance(unscheduled, list):
        unscheduled = []

    decision_scheduled, decision_unscheduled = classify_decisions(
        decisions
    )

    if not scheduled:
        scheduled = decision_scheduled

    if not unscheduled:
        unscheduled = decision_unscheduled

    # Remove duplicate records by workload ID.
    def unique_records(records):
        output = []
        seen = set()

        for record in records:
            workload_id = get_workload_id(record)

            if workload_id is None:
                output.append(record)
                continue

            if workload_id not in seen:
                output.append(record)
                seen.add(workload_id)

        return output

    scheduled = unique_records(scheduled)
    unscheduled = unique_records(unscheduled)

    # Never report the same workload in both groups.
    scheduled_ids = {
        get_workload_id(item)
        for item in scheduled
        if get_workload_id(item) is not None
    }

    unscheduled = [
        item for item in unscheduled
        if get_workload_id(item) not in scheduled_ids
    ]

    return (
        make_json_safe(scheduled),
        make_json_safe(unscheduled),
    )


def summarize_decisions(decisions):
    """Summarize decision actions without counting scheduling status."""

    if isinstance(decisions, dict):
        decisions = decisions.get("decisions", [])

    counts = {
        "run": 0,
        "shift": 0,
        "wait": 0,
        "protect_deadline": 0,
    }

    if not isinstance(decisions, list):
        return counts

    for item in decisions:
        if not isinstance(item, dict):
            continue

        action = str(item.get("action", "")).strip().upper()

        if action == "RUN":
            counts["run"] += 1
        elif action == "SHIFT":
            counts["shift"] += 1
        elif action == "WAIT":
            counts["wait"] += 1
        elif action in {
            "PROTECT_DEADLINE",
            "PROTECT DEADLINE",
        }:
            counts["protect_deadline"] += 1

    return counts


@customer_api.route("/api/customer/validate", methods=["POST"])
def validate_customer_api():
    """Validate submitted customer data."""

    try:
        customer = build_customer_from_json(request.get_json())

        return jsonify({
            "status": "VALID",
            "customer_name": customer.customer_name,
            "gpu_count": len(customer.gpus),
            "workload_count": len(customer.workloads),
            "message": "Customer configuration validated.",
        })

    except (ValueError, TypeError, KeyError) as exc:
        return jsonify({
            "status": "INVALID",
            "error": str(exc),
        }), 400


@customer_api.route("/api/customer/run", methods=["POST"])
def run_customer_api():
    """Run customer workloads through the real PowerOS orchestrator."""

    try:
        customer = build_customer_from_json(request.get_json())

        state = customer_to_poweros_state(customer)
        prices = create_customer_prices(customer)
        solar = create_customer_solar(customer)

        result = run_poweros(
            state=state,
            electricity_prices=prices,
            solar_power_by_hour=solar,
        )

        if not isinstance(result, dict):
            raise TypeError(
                "PowerOS returned an unexpected result format."
            )

        optimization = result.get("optimization", {})
        decisions = make_json_safe(result.get("decisions", []))

        scheduled, unscheduled = extract_workload_outcomes(
            optimization,
            decisions,
        )

        # Only count workload IDs that belong to this request.
        submitted_ids = {
            workload.workload_id
            for workload in customer.workloads
        }

        scheduled_ids = {
            get_workload_id(item)
            for item in scheduled
            if get_workload_id(item) is not None
        }

        unscheduled_ids = {
            get_workload_id(item)
            for item in unscheduled
            if get_workload_id(item) is not None
        }

        # If the optimizer did not return an outcome for a submitted
        # workload, do not silently label it as scheduled.
        known_ids = scheduled_ids | unscheduled_ids
        missing_ids = submitted_ids - known_ids

        if missing_ids:
            logging.warning(
                "PowerOS returned no scheduling outcome for workloads: %s",
                sorted(missing_ids),
            )

        power_summary = make_json_safe(
            result.get("power_summary", {})
        )

        if not isinstance(power_summary, dict):
            power_summary = {}

        return jsonify({
            "status": "SUCCESS",
            "customer_name": customer.customer_name,

            "infrastructure": {
                "gpus": len(customer.gpus),
                "workloads": len(customer.workloads),
                "available_power_kw":
                    customer.power.available_power_kw,
                "grid_capacity_kw":
                    customer.power.grid_capacity_kw,
                "electricity_price_per_kwh":
                    customer.power.electricity_price_per_kwh,
                "solar_power_kw":
                    customer.power.solar_power_kw,
                "battery_available_kw":
                    customer.power.battery_available_kw,
                "pue": customer.pue,
            },

            "optimization": {
                "scheduled": len(scheduled),
                "unscheduled": len(unscheduled),
                "scheduled_workloads": scheduled,
                "unscheduled_workloads": unscheduled,
                "hourly_gpu_usage": make_json_safe(
                    optimization.get("hourly_gpu_usage", [])
                ),
                "hourly_power_usage": make_json_safe(
                    optimization.get("hourly_power_usage", [])
                ),
            },

            "decisions": decisions,
            "decision_summary": summarize_decisions(decisions),
            "power_summary": power_summary,

            "message": (
                "PowerOS processed the customer request. "
                f"{len(scheduled)} scheduled, "
                f"{len(unscheduled)} unscheduled."
            ),
        })

    except (ValueError, TypeError, KeyError) as exc:
        return jsonify({
            "status": "ERROR",
            "error": str(exc),
        }), 400

    except Exception:
        logging.exception("Customer PowerOS run failed")

        return jsonify({
            "status": "ERROR",
            "error": (
                "PowerOS could not process this configuration. "
                "Check the VS Code terminal for the detailed error."
            ),
        }), 500
