"""
ZYVARENTH PowerOS
Customer Configuration Adapter

Converts CustomerConfiguration into the existing
PowerOS DataCenterState model.
"""

from datetime import datetime

from poweros.core.models import (
    GPU,
    Workload,
    PowerState,
    EnergyResource,
    DataCenterState,
)

from poweros.data.customer_config import (
    CustomerConfiguration,
)


def customer_gpu_to_gpu(customer_gpu):
    """Convert CustomerGPU to PowerOS GPU."""

    return GPU(
        gpu_id=customer_gpu.gpu_id,
        utilization_percent=customer_gpu.utilization_percent,
        power_kw=customer_gpu.power_kw,
        temperature_c=customer_gpu.temperature_c,
        memory_utilization_percent=customer_gpu.memory_utilization_percent,
        available=customer_gpu.available,
    )


def customer_workload_to_workload(customer_workload):
    """Convert CustomerWorkload to PowerOS Workload."""

    return Workload(
        workload_id=customer_workload.workload_id,
        gpu_required=customer_workload.gpu_required,
        duration_hours=customer_workload.duration_hours,
        deadline_hour=customer_workload.deadline_hour,
        priority=customer_workload.priority,
    )


def customer_power_to_power_state(customer_power):
    """Convert CustomerPower to PowerState."""

    return PowerState(
        available_power_kw=customer_power.available_power_kw,
        grid_capacity_kw=customer_power.grid_capacity_kw,
        electricity_price_per_kwh=customer_power.electricity_price_per_kwh,
        solar_power_kw=customer_power.solar_power_kw,
        battery_available_kw=customer_power.battery_available_kw,
    )


def customer_resource_to_resource(customer_resource):
    """Convert CustomerEnergyResource to EnergyResource."""

    return EnergyResource(
        name=customer_resource.name,
        available_power_kw=customer_resource.available_power_kw,
        cost_per_kwh=customer_resource.cost_per_kwh,
        renewable=customer_resource.renewable,
    )


def customer_to_poweros_state(customer_config: CustomerConfiguration):
    """
    Convert a complete CustomerConfiguration into
    the standard PowerOS DataCenterState.
    """

    # Validate customer configuration first
    customer_config.validate()

    gpus = [
        customer_gpu_to_gpu(gpu)
        for gpu in customer_config.gpus
    ]

    workloads = [
        customer_workload_to_workload(workload)
        for workload in customer_config.workloads
    ]

    power = customer_power_to_power_state(
        customer_config.power
    )

    energy_resources = [
        customer_resource_to_resource(resource)
        for resource in customer_config.energy_resources
    ]

    return DataCenterState(
        timestamp=datetime.now(),
        gpus=gpus,
        workloads=workloads,
        power=power,
        energy_resources=energy_resources,
        pue=customer_config.pue,
    )


def validate_adapter(customer_config):
    """Validate that customer data converts correctly."""

    state = customer_to_poweros_state(customer_config)

    if len(state.gpus) != len(customer_config.gpus):
        raise ValueError("GPU conversion failed.")

    if len(state.workloads) != len(customer_config.workloads):
        raise ValueError("Workload conversion failed.")

    if state.power.available_power_kw != customer_config.power.available_power_kw:
        raise ValueError("Power conversion failed.")

    if state.pue != customer_config.pue:
        raise ValueError("PUE conversion failed.")

    return state


def print_adapter_summary(state):
    """Print converted PowerOS state."""

    print("=" * 70)
    print("ZYVARENTH POWEROS")
    print("CUSTOMER → POWEROS ADAPTER")
    print("=" * 70)

    print(f"GPUs: {state.total_gpu_count()}")
    print(f"Available GPUs: {state.available_gpu_count()}")
    print(f"Workloads: {len(state.workloads)}")

    print(
        f"Available Power: "
        f"{state.power.available_power_kw:.1f} kW"
    )

    print(
        f"Grid Capacity: "
        f"{state.power.grid_capacity_kw:.1f} kW"
    )

    print(
        f"Electricity Price: "
        f"{state.power.electricity_price_per_kwh:.2f} ₹/kWh"
    )

    print(
        f"Solar: "
        f"{state.power.solar_power_kw:.1f} kW"
    )

    print(
        f"Battery: "
        f"{state.power.battery_available_kw:.1f} kW"
    )

    print(f"PUE: {state.pue}")

    print()
    print("CUSTOMER DATA CONVERTED TO POWEROS STATE")
    print("=" * 70)


def main():
    """Run customer adapter test."""

    from poweros.data.customer_config import create_example_customer

    customer = create_example_customer()

    state = validate_adapter(customer)

    print_adapter_summary(state)


if __name__ == "__main__":
    main()