from poweros.core.models import (
    GPU,
    Workload,
    PowerState,
    DataCenterState,
)

from poweros.simulation.simulator import (
    simulate_scenario,
    simulate_power_reduction,
    run_standard_scenarios,
)


def create_test_state():

    gpus = [
        GPU(
            gpu_id="GPU-001",
            utilization_percent=50,
            power_kw=0.40,
            temperature_c=60,
            memory_utilization_percent=50,
        ),
        GPU(
            gpu_id="GPU-002",
            utilization_percent=50,
            power_kw=0.40,
            temperature_c=60,
            memory_utilization_percent=50,
        ),
        GPU(
            gpu_id="GPU-003",
            utilization_percent=50,
            power_kw=0.40,
            temperature_c=60,
            memory_utilization_percent=50,
        ),
        GPU(
            gpu_id="GPU-004",
            utilization_percent=50,
            power_kw=0.40,
            temperature_c=60,
            memory_utilization_percent=50,
        ),
    ]

    workloads = [
        Workload(
            workload_id="JOB-001",
            gpu_required=2,
            duration_hours=2,
            deadline_hour=8,
            priority="HIGH",
        ),
        Workload(
            workload_id="JOB-002",
            gpu_required=1,
            duration_hours=2,
            deadline_hour=12,
            priority="LOW",
        ),
    ]

    power = PowerState(
        available_power_kw=10,
        grid_capacity_kw=10,
        electricity_price_per_kwh=8,
        solar_power_kw=2,
        battery_available_kw=1,
    )

    return DataCenterState(
        timestamp="2026-09-20T13:00:00",
        gpus=gpus,
        workloads=workloads,
        power=power,
    )


def test_simulation():

    state = create_test_state()

    result = simulate_scenario(
        state,
        "TEST_SCENARIO",
    )

    assert result["scenario"] == "TEST_SCENARIO"

    assert "status" in result

    assert "bottleneck" in result

    assert "scheduled_workloads" in result


def test_power_reduction():

    state = create_test_state()

    result = simulate_power_reduction(
        state,
        20,
    )

    assert (
        result["scenario"]
        == "POWER_REDUCTION_20%"
    )


def test_standard_scenarios():

    state = create_test_state()

    results = run_standard_scenarios(
        state
    )

    assert "BASELINE" in results

    assert (
        "POWER_REDUCTION_20%"
        in results
    )

    assert (
        "PRICE_INCREASE_25%"
        in results
    )

    assert (
        "SOLAR_REDUCTION_50%"
        in results
    )

    assert (
        "GPU_DEMAND_30%"
        in results
    )


if __name__ == "__main__":

    test_simulation()

    test_power_reduction()

    test_standard_scenarios()

    print()
    print("POWEROS SIMULATION ENGINE TEST PASSED")