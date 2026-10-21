from poweros.simulation.workload_lifecycle import (
    QUEUED,
    ADMITTED,
    SCHEDULED,
    RUNNING,
    COMPLETED,
    PAUSED,
    SHIFTED,
    create_workload_record,
    initialize_workloads,
    apply_schedule,
    admit_workloads,
    process_hour,
    pause_workload,
    resume_workload,
    shift_workload,
    run_lifecycle_simulation,
    summarize_lifecycle,
)


def test_workload_lifecycle():

    workloads = [
        {
            "workload_id": "JOB-001",
            "gpu_required": 2,
            "duration_hours": 2,
            "deadline_hour": 6,
            "priority": "HIGH",
        },
        {
            "workload_id": "JOB-002",
            "gpu_required": 1,
            "duration_hours": 1,
            "deadline_hour": 8,
            "priority": "LOW",
        },
    ]

    # ---------------------------------------------------------
    # INITIALIZE
    # ---------------------------------------------------------

    lifecycle = initialize_workloads(
        workloads
    )

    assert len(lifecycle) == 2

    assert (
        lifecycle[0]["state"]
        == QUEUED
    )

    # ---------------------------------------------------------
    # ADMISSION
    # ---------------------------------------------------------

    admission_results = [
        {
            "workload_id": "JOB-001",
            "action": "ADMIT",
        },
        {
            "workload_id": "JOB-002",
            "action": "ADMIT",
        },
    ]

    admit_workloads(
        lifecycle,
        admission_results,
    )

    assert (
        lifecycle[0]["state"]
        == ADMITTED
    )

    # ---------------------------------------------------------
    # SCHEDULE
    # ---------------------------------------------------------

    schedule = {
        "scheduled": [
            {
                "workload_id": "JOB-001",
                "start_hour": 0,
                "duration_hours": 2,
                "gpu_required": 2,
                "power_kw": 1.4,
                "deadline_hour": 6,
                "priority": "HIGH",
                "status": "SCHEDULED",
                "admission_action": "ADMIT",
            },
            {
                "workload_id": "JOB-002",
                "start_hour": 2,
                "duration_hours": 1,
                "gpu_required": 1,
                "power_kw": 0.7,
                "deadline_hour": 8,
                "priority": "LOW",
                "status": "SCHEDULED",
                "admission_action": "ADMIT",
            },
        ],
        "unscheduled": [],
    }

    apply_schedule(
        lifecycle,
        schedule,
    )

    assert (
        lifecycle[0]["state"]
        == SCHEDULED
    )

    assert (
        lifecycle[0]["start_hour"]
        == 0
    )

    # ---------------------------------------------------------
    # HOUR 0
    # JOB-001 STARTS
    # ---------------------------------------------------------

    process_hour(
        lifecycle,
        current_hour=0,
        power_available=True,
    )

    assert (
        lifecycle[0]["state"]
        == RUNNING
    )

    # ---------------------------------------------------------
    # HOUR 1
    # JOB-001 COMPLETES
    # ---------------------------------------------------------

    process_hour(
        lifecycle,
        current_hour=1,
        power_available=True,
    )

    assert (
        lifecycle[0]["state"]
        == COMPLETED
    )

    assert (
        lifecycle[0]["deadline_met"]
        is True
    )

    # ---------------------------------------------------------
    # HOUR 2
    # JOB-002 STARTS AND COMPLETES
    # ---------------------------------------------------------

    process_hour(
        lifecycle,
        current_hour=2,
        power_available=True,
    )

    assert (
        lifecycle[1]["state"]
        == COMPLETED
    )

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    result = {
        "workloads": lifecycle,
        "history": [],
    }

    summary = summarize_lifecycle(
        result
    )

    assert (
        summary["total_workloads"]
        == 2
    )

    assert (
        summary["completed"]
        == 2
    )

    assert (
        summary["completion_rate_percent"]
        == 100.0
    )

    print(
        "POWEROS WORKLOAD LIFECYCLE TEST PASSED"
    )


def test_pause_and_resume():

    workload = create_workload_record(
        workload_id="PAUSE-JOB",
        gpu_required=2,
        duration_hours=3,
        deadline_hour=10,
        priority="HIGH",
    )

    workload["state"] = RUNNING

    pause_workload(
        workload
    )

    assert (
        workload["state"]
        == PAUSED
    )

    assert (
        workload["pause_count"]
        == 1
    )

    resume_workload(
        workload
    )

    assert (
        workload["state"]
        == RUNNING
    )


def test_shift():

    workload = create_workload_record(
        workload_id="SHIFT-JOB",
        gpu_required=2,
        duration_hours=2,
        deadline_hour=10,
        priority="MEDIUM",
    )

    shift_workload(
        workload,
        new_start_hour=5,
    )

    assert (
        workload["state"]
        == SHIFTED
    )

    assert (
        workload["start_hour"]
        == 5
    )

    assert (
        workload["shift_count"]
        == 1
    )


def test_power_constraint():

    workload = create_workload_record(
        workload_id="POWER-JOB",
        gpu_required=2,
        duration_hours=3,
        deadline_hour=10,
        priority="HIGH",
    )

    workload["state"] = SCHEDULED
    workload["start_hour"] = 0

    process_hour(
        [workload],
        current_hour=0,
        power_available=True,
    )

    assert (
        workload["state"]
        == RUNNING
    )

    process_hour(
        [workload],
        current_hour=1,
        power_available=False,
    )

    assert (
        workload["state"]
        == PAUSED
    )

    process_hour(
        [workload],
        current_hour=2,
        power_available=True,
    )

    assert (
        workload["state"]
        in (
            RUNNING,
            COMPLETED,
        )
    )


def main():

    test_workload_lifecycle()

    test_pause_and_resume()

    test_shift()

    test_power_constraint()

    print()

    print(
        "POWEROS WORKLOAD LIFECYCLE TEST PASSED"
    )


if __name__ == "__main__":

    main()