from poweros.core.models import (
    GPU,
    Workload,
    PowerState,
    DataCenterState,
)

from poweros.intelligence.state_analyzer import (
    analyze_state,
)


def test_state_intelligence():

    gpus = [
        GPU(
            gpu_id="GPU-001",
            utilization_percent=80,
            power_kw=0.60,
            temperature_c=65,
            memory_utilization_percent=70,
        ),

        GPU(
            gpu_id="GPU-002",
            utilization_percent=10,
            power_kw=0.10,
            temperature_c=50,
            memory_utilization_percent=20,
        ),
    ]

    workloads = [
        Workload(
            workload_id="JOB-001",
            gpu_required=1,
            duration_hours=2,
            deadline_hour=4,
            priority="HIGH",
        )
    ]

    power = PowerState(
        available_power_kw=500,
        grid_capacity_kw=600,
        electricity_price_per_kwh=8.5,
        solar_power_kw=100,
        battery_available_kw=50,
    )

    state = DataCenterState(
        timestamp="2026-09-14T20:00:00",
        gpus=gpus,
        workloads=workloads,
        power=power,
    )

    analysis = analyze_state(state)

    assert analysis["status"] == "WARNING"

    assert (
        analysis["primary_bottleneck"]
        == "GPU_UTILIZATION"
    )

    assert (
        analysis["gpu_analysis"]["idle_gpu_count"]
        == 1
    )

    assert (
        analysis["workload_analysis"]
        ["urgent_workloads"]
        == 1
    )


if __name__ == "__main__":

    test_state_intelligence()

    print()
    print("POWEROS STATE INTELLIGENCE TEST PASSED")