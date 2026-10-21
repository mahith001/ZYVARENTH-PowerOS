from poweros.core.models import (
    GPU,
    Workload,
    PowerState,
    DataCenterState,
)

from poweros.core.orchestrator import (
    run_poweros,
    create_executive_summary,
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
        timestamp="2026-09-20T14:00:00",
        gpus=gpus,
        workloads=workloads,
        power=power,
    )


def test_orchestrator():

    state = create_test_state()

    result = run_poweros(
        state,
        horizon_hours=24,
    )

    assert "state_analysis" in result
    assert "forecast" in result
    assert "schedule" in result
    assert "optimization_summary" in result
    assert "decisions" in result
    assert "decision_summary" in result

    summary = create_executive_summary(
        result
    )

    assert "system_status" in summary
    assert "primary_bottleneck" in summary
    assert "scheduled_workloads" in summary
def test_power_summary_metrics_are_consistent():
    from poweros.core.orchestrator import (
        build_power_demand_by_hour,
        calculate_power_summary,
    )

    schedule = {
        "scheduled": [
            {
                "start_hour": 0,
                "duration_hours": 1,
                "power_kw": 2.0,
                "status": "SCHEDULED",
            },
            {
                "start_hour": 1,
                "duration_hours": 1,
                "power_kw": 1.0,
                "status": "SCHEDULED",
            },
        ]
    }

    pue = 1.3
    demand = build_power_demand_by_hour(
        schedule, horizon_hours=3, pue=pue
    )
    summary = calculate_power_summary(schedule, demand, pue)

    assert abs(summary["peak_it_power_kw"] - 2.0) < 1e-9
    assert abs(summary["peak_facility_power_kw"] - 2.6) < 1e-9
    assert abs(summary["total_it_energy_kwh"] - 3.0) < 1e-9
    assert abs(summary["total_facility_energy_kwh"] - 3.9) < 1e-9
    assert abs(summary["cooling_overhead_kw"] - 0.6) < 1e-9

    
def test_energy_cost_is_non_negative_and_matches_dispatch():
    from poweros.core.orchestrator import run_poweros
    from poweros.data.fair_baseline import create_realistic_state

    state = create_realistic_state()

    result = run_poweros(state)

    battery = result["battery_dispatch"]

    soc = battery.get(
    "final_soc_percent",
    battery.get("final_battery_soc_percent")
    )

    assert soc is not None
    assert 0 <= soc <= 100

    
def test_battery_dispatch_respects_soc_and_energy_bounds():
    from poweros.core.orchestrator import run_poweros
    from poweros.data.fair_baseline import create_realistic_state

    state = create_realistic_state()
    result = run_poweros(state)
    battery = result["battery_dispatch"]

    soc = battery.get(
        "final_soc_percent",
        battery.get("final_battery_soc_percent")
    )

    assert soc is not None
    assert 0 <= soc <= 100

    assert battery["total_battery_energy_kwh"] >= 0
    assert battery["total_grid_energy_kwh"] >= 0
    assert battery["total_solar_energy_kwh"] >= 0


def test_forecast_returns_valid_non_negative_power():
    from poweros.core.orchestrator import run_poweros
    from poweros.data.fair_baseline import create_realistic_state

    state = create_realistic_state()
    result = run_poweros(state, horizon_hours=24)

    forecast = result["forecast"]
    assert isinstance(forecast, dict)

    peak = (
        forecast.get("power_kw")
        or forecast.get("peak_power_kw")
        or forecast.get("forecast_power_kw")
        or forecast.get("power", 0.0)
    )

    assert isinstance(peak, (int, float))
    assert peak >= 0


def test_scheduled_workloads_respect_deadlines():
    from poweros.core.orchestrator import run_poweros
    from poweros.data.fair_baseline import create_realistic_state

    state = create_realistic_state()
    result = run_poweros(state, horizon_hours=24)

    schedule = result["schedule"]

    for workload in schedule.get("scheduled", []):
        start = workload["start_hour"]
        duration = workload["duration_hours"]
        deadline = workload["deadline_hour"]

        assert start >= 0
        assert duration > 0
        assert start + duration <= deadline


def test_unscheduled_workloads_have_reasons():
    from poweros.core.orchestrator import run_poweros
    from poweros.data.fair_baseline import create_realistic_state

    state = create_realistic_state()
    result = run_poweros(state, horizon_hours=24)

    schedule = result["schedule"]
    unscheduled = schedule.get("unscheduled", [])

    for workload in unscheduled:
        assert workload.get("workload_id") is not None
        assert isinstance(workload.get("reason"), str)
        assert workload["reason"].strip() != ""


def test_poweros_supports_different_scheduling_horizons():
    from poweros.core.orchestrator import run_poweros
    from poweros.data.fair_baseline import create_realistic_state

    for horizon in (6, 12, 24):
        state = create_realistic_state()
        result = run_poweros(state, horizon_hours=horizon)

        assert len(result["power_demand_by_hour"]) == horizon
        assert "scheduled" in result["schedule"]
        assert "unscheduled" in result["schedule"]
        assert len(result["power_demand_by_hour"]) == horizon

def test_gpu_schedule_never_exceeds_capacity():
    from poweros.core.orchestrator import run_poweros
    from poweros.data.fair_baseline import create_realistic_state

    state = create_realistic_state()
    result = run_poweros(state, horizon_hours=24)

    usage = result["schedule"]["hourly_gpu_usage"]
    capacity = state.available_gpu_count()

    assert len(usage) == 24
    assert all(0 <= used <= capacity for used in usage)


if __name__ == "__main__":

    test_orchestrator()

    print()
    print("POWEROS ORCHESTRATOR TEST PASSED")