from poweros.core.models import (
    DataCenterState,
    GPU,
    Workload,
    PowerState,
    EnergyResource,
)


def telemetry_to_data_center_state(snapshot, pue=1.3):
    gpus = []

    for telemetry in snapshot.gpus:
        gpus.append(
            GPU(
                gpu_id=telemetry.gpu_id,
                utilization_percent=telemetry.utilization_percent,
                power_kw=telemetry.power_kw,
                temperature_c=telemetry.temperature_c,
                memory_utilization_percent=(
                    telemetry.memory_utilization_percent
                ),
                available=True,
            )
        )

    workloads = []

    for telemetry in snapshot.workloads:
        workloads.append(
            Workload(
                workload_id=telemetry.workload_id,
                gpu_required=telemetry.gpu_required,
                duration_hours=telemetry.duration_hours,
                deadline_hour=telemetry.deadline_hour,
                priority=telemetry.priority,
            )
        )

    power = PowerState(
        available_power_kw=snapshot.power.available_power_kw,
        grid_capacity_kw=snapshot.power.grid_capacity_kw,
        electricity_price_per_kwh=(
            snapshot.power.electricity_price_per_kwh
        ),
        solar_power_kw=snapshot.power.solar_power_kw,
        battery_available_kw=snapshot.power.battery_available_kw,
    )

    resources = [
        EnergyResource(
            name="GRID",
            available_power_kw=snapshot.power.grid_capacity_kw,
            cost_per_kwh=snapshot.power.electricity_price_per_kwh,
            renewable=False,
        ),
        EnergyResource(
            name="SOLAR",
            available_power_kw=snapshot.power.solar_power_kw,
            cost_per_kwh=0.0,
            renewable=True,
        ),
        EnergyResource(
            name="BATTERY",
            available_power_kw=snapshot.power.battery_available_kw,
            cost_per_kwh=6.0,
            renewable=False,
        ),
    ]

    return DataCenterState(
        timestamp=snapshot.timestamp,
        gpus=gpus,
        workloads=workloads,
        power=power,
        energy_resources=resources,
        pue=pue,
    )