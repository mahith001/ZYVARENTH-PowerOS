"""
ZYVARENTH PowerOS
Customer PowerOS Runner

Runs the complete PowerOS intelligence and optimization pipeline
using customer-provided infrastructure data.
"""

from poweros.data.customer_config import create_example_customer
from poweros.data.customer_adapter import customer_to_poweros_state
from poweros.core.orchestrator import (
    run_poweros,
    create_default_prices,
    create_default_solar,
)


def create_customer_prices(customer):
    """
    Create a 24-hour electricity-price profile.

    The customer's current electricity price is used as
    the base price.
    """

    base_price = customer.power.electricity_price_per_kwh

    return [
        base_price,
        base_price,
        base_price,
        base_price,
        base_price * 0.95,
        base_price * 0.90,
        base_price * 0.85,
        base_price * 0.80,
        base_price * 0.75,
        base_price * 0.72,
        base_price * 0.70,
        base_price * 0.72,
        base_price * 0.76,
        base_price * 0.82,
        base_price * 0.88,
        base_price * 0.95,
        base_price * 1.05,
        base_price * 1.15,
        base_price * 1.20,
        base_price * 1.15,
        base_price * 1.10,
        base_price * 1.08,
        base_price * 1.05,
        base_price,
    ]


def create_customer_solar(customer):
    """
    Create a 24-hour solar forecast using the customer's
    available solar capacity.
    """

    solar = customer.power.solar_power_kw

    return [
        0.0,
        0.0,
        0.0,
        0.0,
        solar * 0.10,
        solar * 0.25,
        solar * 0.40,
        solar * 0.60,
        solar * 0.80,
        solar * 0.90,
        solar,
        solar,
        solar,
        solar * 0.90,
        solar * 0.75,
        solar * 0.55,
        solar * 0.35,
        solar * 0.15,
        solar * 0.05,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    ]


def run_customer_poweros(customer):
    """
    Run PowerOS using customer infrastructure.
    """

    state = customer_to_poweros_state(customer)

    prices = create_customer_prices(customer)

    solar = create_customer_solar(customer)

    result = run_poweros(
        state=state,
        electricity_prices=prices,
        solar_power_by_hour=solar,
    )

    return result


def print_customer_result(customer, result):
    """Print the customer PowerOS result."""

    print()
    print("=" * 70)
    print("ZYVARENTH POWEROS")
    print("CUSTOMER POWER OPTIMIZATION RESULT")
    print("=" * 70)

    print(f"Customer: {customer.customer_name}")

    print()

    print("INFRASTRUCTURE")
    print("-" * 70)
    print(f"GPUs: {len(customer.gpus)}")
    print(f"Workloads: {len(customer.workloads)}")
    print(f"Power Available: {customer.power.available_power_kw:.1f} kW")
    print(f"Grid Capacity: {customer.power.grid_capacity_kw:.1f} kW")
    print(f"Solar Capacity: {customer.power.solar_power_kw:.1f} kW")
    print(f"Battery Capacity: {customer.power.battery_available_kw:.1f} kW")

    print()

    print("POWEROS RESULT")
    print("-" * 70)

    optimization = result.get("optimization", {})

    scheduled = optimization.get("scheduled", [])
    unscheduled = optimization.get("unscheduled", [])

    print(f"Scheduled Workloads: {len(scheduled)}")
    print(f"Unscheduled Workloads: {len(unscheduled)}")

    if "power_summary" in result:
        summary = result["power_summary"]

        print(
            f"Peak Facility Power: "
            f"{summary.get('peak_facility_power_kw', 0.0):.2f} kW"
        )

        print(
            f"Total Facility Energy: "
            f"{summary.get('total_facility_energy_kwh', 0.0):.2f} kWh"
        )

    decisions = result.get("decisions", [])

    if isinstance(decisions, dict):
        decision_summary = decisions.get("summary", decisions)

        print()
        print("DECISIONS")
        print("-" * 70)

        print(
            f"RUN: "
            f"{decision_summary.get('run_decisions', 0)}"
        )

        print(
            f"WAIT: "
            f"{decision_summary.get('wait_decisions', 0)}"
        )

        print(
            f"SHIFT: "
            f"{decision_summary.get('shift_decisions', 0)}"
        )

        print(
            f"PROTECT DEADLINE: "
            f"{decision_summary.get('protect_deadline_decisions', 0)}"
        )

    print()
    print("=" * 70)
    print("CUSTOMER POWEROS RUN COMPLETED")
    print("=" * 70)


def main():

    customer = create_example_customer()

    result = run_customer_poweros(customer)

    print_customer_result(customer, result)


if __name__ == "__main__":
    main()