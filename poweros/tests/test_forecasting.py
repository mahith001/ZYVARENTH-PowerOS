from poweros.core.models import (
    GPU,
    Workload,
    PowerState,
    DataCenterState,
)

from poweros.intelligence.forecasting import (
    generate_forecast,
)


def create_test_state():

    gpus = [
        GPU(
            gpu_id="GPU-001",
            utilization_percent=50,
            power_kw=0.4,
            temperature_c=60,
            memory_utilization_percent=50,
        ),
        GPU(
            gpu_id="GPU-002",
            utilization_percent=50,
            power_kw=0.4,
            temperature_c=60,
            memory_utilization_percent=50,
        ),
        GPU(
            gpu_id="GPU-003",
            utilization_percent=50,
            power_kw=0.4,
            temperature_c=60,
            memory_utilization_percent=50,
        ),
        GPU(
            gpu_id="GPU-004",
            utilization_percent=50,
            power_kw=0.4,
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
            duration_hours=3,
            deadline_hour=12,
            priority="MEDIUM",
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


def test_forecasting():

    state = create_test_state()

    forecast = generate_forecast(
        state,
        horizon_hours=24,
    )

    assert forecast[
        "horizon_hours"
    ] == 24

    assert len(
        forecast["hourly_forecast"]
    ) == 24

    assert "peak" in forecast

    assert (
        "critical_hours"
        in forecast
    )

    assert (
        "warning_hours"
        in forecast
    )


if __name__ == "__main__":

    test_forecasting()

    print()
    print(
        "POWEROS FORECASTING ENGINE TEST PASSED"
    )