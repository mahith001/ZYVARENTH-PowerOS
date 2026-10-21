from poweros.core.models import (
    GPU,
    Workload,
    PowerState,
    DataCenterState,
)

from poweros.intelligence.optimizer import (
    optimize_workloads,
    summarize_optimization,
)


# =============================================================
# BASIC OPTIMIZER TEST
# =============================================================

def test_optimizer():

    gpus = [
        GPU(
            gpu_id="GPU-001",
            utilization_percent=20,
            power_kw=0.2,
            temperature_c=50,
            memory_utilization_percent=20,
        ),

        GPU(
            gpu_id="GPU-002",
            utilization_percent=20,
            power_kw=0.2,
            temperature_c=50,
            memory_utilization_percent=20,
        ),

        GPU(
            gpu_id="GPU-003",
            utilization_percent=20,
            power_kw=0.2,
            temperature_c=50,
            memory_utilization_percent=20,
        ),

        GPU(
            gpu_id="GPU-004",
            utilization_percent=20,
            power_kw=0.2,
            temperature_c=50,
            memory_utilization_percent=20,
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
        electricity_price_per_kwh=8.0,
        solar_power_kw=2,
        battery_available_kw=0,
    )

    state = DataCenterState(
        timestamp="2026-09-16T20:00:00",
        gpus=gpus,
        workloads=workloads,
        power=power,
        pue=1.3,
    )

    prices = [
        10,
        10,
        10,
        10,
        5,
        5,
        5,
        5,
        10,
        10,
        10,
        10,
        10,
        10,
        10,
        10,
        10,
        10,
        10,
        10,
        10,
        10,
        10,
        10,
    ]

    solar = [
        0,
        0,
        0,
        0,
        4,
        4,
        4,
        4,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    ]

    schedule = optimize_workloads(
        state=state,
        horizon_hours=24,
        electricity_prices=prices,
        solar_power_by_hour=solar,
    )

    summary = summarize_optimization(
        schedule
    )

    assert summary["total_count"] == 2

    assert summary["scheduled_count"] == 2

    assert summary["unscheduled_count"] == 0

    assert summary["success_rate_percent"] == 100.0


# =============================================================
# ADMISSION CONTROL → OPTIMIZER INTEGRATION TEST
# =============================================================

def test_admission_control_integration():

    gpus = [
        GPU(
            gpu_id=f"GPU-{i:03d}",
            utilization_percent=20,
            power_kw=0.2,
            temperature_c=50,
            memory_utilization_percent=20,
        )
        for i in range(1, 11)
    ]

    workloads = [
        Workload(
            workload_id="DELAY-ME",
            gpu_required=8,
            duration_hours=2,
            deadline_hour=20,
            priority="LOW",
        ),

        Workload(
            workload_id="ADMIT-ME",
            gpu_required=2,
            duration_hours=1,
            deadline_hour=20,
            priority="HIGH",
        ),
    ]

    power = PowerState(
        available_power_kw=20,
        grid_capacity_kw=25,
        electricity_price_per_kwh=8.5,
        solar_power_kw=0,
        battery_available_kw=0,
    )

    state = DataCenterState(
        timestamp="2026-09-20T17:00:00",
        gpus=gpus,
        workloads=workloads,
        power=power,
        pue=1.3,
    )

    # ---------------------------------------------------------
    # ADMISSION CONTROL RESULTS
    # ---------------------------------------------------------
    #
    # DELAY-ME must NOT be scheduled.
    #
    # ADMIT-ME is allowed to be scheduled.
    #
    # This verifies that the optimizer actually respects
    # the admission-control decision.
    # ---------------------------------------------------------

    admission_results = [
        {
            "workload_id": "DELAY-ME",
            "action": "DELAY",
        },

        {
            "workload_id": "ADMIT-ME",
            "action": "ADMIT",
        },
    ]

    schedule = optimize_workloads(
        state=state,
        horizon_hours=24,
        admission_results=admission_results,
    )

    scheduled_ids = [
        item["workload_id"]
        for item in schedule["scheduled"]
    ]

    unscheduled_ids = [
        item["workload_id"]
        for item in schedule["unscheduled"]
    ]

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    assert "DELAY-ME" not in scheduled_ids

    assert "DELAY-ME" in unscheduled_ids

    assert "ADMIT-ME" in scheduled_ids

    # Verify that the optimizer recorded the
    # admission action.
    admitted_job = next(
        item
        for item in schedule["scheduled"]
        if item["workload_id"] == "ADMIT-ME"
    )

    assert (
        admitted_job["admission_action"]
        == "ADMIT"
    )

    delayed_job = next(
        item
        for item in schedule["unscheduled"]
        if item["workload_id"] == "DELAY-ME"
    )

    assert (
        delayed_job["admission_action"]
        == "DELAY"
    )

    print(
        "ADMISSION -> OPTIMIZER INTEGRATION PASSED"
    )


# =============================================================
# MAIN
# =============================================================

def main():

    # Basic optimizer test
    test_optimizer()

    print(
        "BASIC OPTIMIZER TEST PASSED"
    )

    # Admission Control integration test
    test_admission_control_integration()

    print(
        "POWEROS OPTIMIZER TEST PASSED"
    )


if __name__ == "__main__":

    main()