from typing import Dict, List

from poweros.core.models import (
    GPU,
    Workload,
    PowerState,
    EnergyResource,
    DataCenterState,
)


# =========================================================
# GPU DATA
# =========================================================

def load_gpus(gpu_data: List[Dict]) -> List[GPU]:
    """
    Convert raw GPU telemetry into PowerOS GPU objects.
    """

    gpus = []

    for item in gpu_data:

        gpu = GPU(
            gpu_id=str(item["gpu_id"]),
            utilization_percent=float(
                item.get("utilization_percent", 0)
            ),
            power_kw=float(
                item.get("power_kw", 0)
            ),
            temperature_c=float(
                item.get("temperature_c", 0)
            ),
            memory_utilization_percent=float(
                item.get(
                    "memory_utilization_percent",
                    0
                )
            ),
            available=bool(
                item.get("available", True)
            ),
        )

        gpus.append(gpu)

    return gpus


# =========================================================
# WORKLOAD DATA
# =========================================================

def load_workloads(
    workload_data: List[Dict],
) -> List[Workload]:
    """
    Convert raw workload information into
    PowerOS workload objects.
    """

    workloads = []

    for item in workload_data:

        workload = Workload(
            workload_id=str(item["workload_id"]),
            gpu_required=int(
                item["gpu_required"]
            ),
            duration_hours=float(
                item["duration_hours"]
            ),
            deadline_hour=int(
                item["deadline_hour"]
            ),
            priority=item.get(
                "priority",
                "MEDIUM"
            ),
        )

        workloads.append(workload)

    return workloads


# =========================================================
# POWER DATA
# =========================================================

def load_power_state(
    power_data: Dict,
) -> PowerState:
    """
    Convert raw power information into
    a PowerOS PowerState.
    """

    return PowerState(
        available_power_kw=float(
            power_data["available_power_kw"]
        ),
        grid_capacity_kw=float(
            power_data["grid_capacity_kw"]
        ),
        electricity_price_per_kwh=float(
            power_data[
                "electricity_price_per_kwh"
            ]
        ),
        solar_power_kw=float(
            power_data.get(
                "solar_power_kw",
                0
            )
        ),
        battery_available_kw=float(
            power_data.get(
                "battery_available_kw",
                0
            )
        ),
    )


# =========================================================
# ENERGY RESOURCES
# =========================================================

def load_energy_resources(
    resource_data: List[Dict],
) -> List[EnergyResource]:
    """
    Convert raw energy-resource information
    into PowerOS energy resources.
    """

    resources = []

    for item in resource_data:

        resource = EnergyResource(
            name=str(item["name"]),
            available_power_kw=float(
                item["available_power_kw"]
            ),
            cost_per_kwh=float(
                item["cost_per_kwh"]
            ),
            renewable=bool(
                item.get("renewable", False)
            ),
        )

        resources.append(resource)

    return resources


# =========================================================
# COMPLETE DATA CENTER STATE
# =========================================================

def build_data_center_state(
    timestamp: str,
    gpu_data: List[Dict],
    workload_data: List[Dict],
    power_data: Dict,
    resource_data: List[Dict],
) -> DataCenterState:
    """
    Build the complete state of the data center
    from raw infrastructure data.
    """

    gpus = load_gpus(gpu_data)

    workloads = load_workloads(
        workload_data
    )

    power = load_power_state(
        power_data
    )

    resources = load_energy_resources(
        resource_data
    )

    return DataCenterState(
        timestamp=timestamp,
        gpus=gpus,
        workloads=workloads,
        power=power,
        energy_resources=resources,
    )


# =========================================================
# STATE SUMMARY
# =========================================================

def summarize_state(
    state: DataCenterState,
) -> Dict:
    """
    Create a compact summary of the current
    data-center state.
    """

    return {
        "timestamp": state.timestamp,

        "total_gpus":
            state.total_gpu_count(),

        "available_gpus":
            state.available_gpu_count(),

        "average_gpu_utilization_percent":
            round(
                state.average_gpu_utilization(),
                2,
            ),

        "total_gpu_power_kw":
            round(
                state.total_gpu_power_kw(),
                3,
            ),

        "workloads":
            len(state.workloads),

        "available_power_kw":
            round(
                state.power.available_power_kw,
                2,
            )
            if state.power
            else 0,

        "grid_capacity_kw":
            round(
                state.power.grid_capacity_kw,
                2,
            )
            if state.power
            else 0,

        "electricity_price_per_kwh":
            round(
                state.power.electricity_price_per_kwh,
                2,
            )
            if state.power
            else 0,

        "solar_power_kw":
            round(
                state.power.solar_power_kw,
                2,
            )
            if state.power
            else 0,

        "battery_available_kw":
            round(
                state.power.battery_available_kw,
                2,
            )
            if state.power
            else 0,
    }


def print_state_summary(
    summary: Dict,
):
    """
    Print a clean PowerOS state summary.
    """

    print()
    print("=" * 60)
    print("POWEROS DATA CENTER STATE")
    print("=" * 60)

    for key, value in summary.items():

        label = key.replace(
            "_",
            " "
        ).title()

        print(
            f"{label}: {value}"
        )

    print("=" * 60)