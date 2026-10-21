from poweros.core.models import (
    GPU,
    Workload,
    PowerState,
    EnergyResource,
    DataCenterState,
)


def test_poweros_core():

    gpu = GPU(
        gpu_id="GPU-001",
        utilization_percent=75,
        power_kw=0.55,
        temperature_c=65,
        memory_utilization_percent=70,
    )

    workload = Workload(
        workload_id="JOB-001",
        gpu_required=2,
        duration_hours=4,
        deadline_hour=12,
        priority="HIGH",
    )

    power = PowerState(
        available_power_kw=500,
        grid_capacity_kw=600,
        electricity_price_per_kwh=8.5,
        solar_power_kw=100,
        battery_available_kw=50,
    )

    solar = EnergyResource(
        name="Solar",
        available_power_kw=100,
        cost_per_kwh=0,
        renewable=True,
    )

    state = DataCenterState(
        timestamp="2026-09-14T18:00:00",
        gpus=[gpu],
        workloads=[workload],
        power=power,
        energy_resources=[solar],
    )

    assert state.total_gpu_count() == 1
    assert state.available_gpu_count() == 1
    assert state.total_gpu_power_kw() == 0.55
    assert state.average_gpu_utilization() == 75


if __name__ == "__main__":
    test_poweros_core()
    print("POWEROS CORE TEST PASSED")