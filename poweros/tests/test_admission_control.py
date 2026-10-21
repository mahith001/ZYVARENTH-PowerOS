from poweros.decisions.admission_control import (
    evaluate_workload_admission,
    evaluate_workloads,
    summarize_admission,
)

from poweros.core.models import (
    Workload,
)


def main():

    # --------------------------------------------------------
    # CRITICAL WORKLOAD
    # --------------------------------------------------------

    critical = evaluate_workload_admission(
        priority="HIGH",
        deadline_hour=2,
        current_hour=0,
        required_power_kw=5,
        available_safe_power_kw=10,
    )

    assert critical["action"] == "PROTECT"

    # --------------------------------------------------------
    # HIGH WORKLOAD
    # --------------------------------------------------------

    high = evaluate_workload_admission(
        priority="HIGH",
        deadline_hour=10,
        current_hour=0,
        required_power_kw=5,
        available_safe_power_kw=10,
    )

    assert high["action"] == "ADMIT"

    # --------------------------------------------------------
    # LOW WORKLOAD WITH NO POWER
    # --------------------------------------------------------

    low = evaluate_workload_admission(
        priority="LOW",
        deadline_hour=20,
        current_hour=0,
        required_power_kw=10,
        available_safe_power_kw=5,
    )

    assert low["action"] == "DELAY"

    # --------------------------------------------------------
    # BATCH TEST
    # --------------------------------------------------------

    workloads = [

        Workload(
            workload_id="JOB-001",
            gpu_required=4,
            duration_hours=2,
            deadline_hour=2,
            priority="HIGH",
        ),

        Workload(
            workload_id="JOB-002",
            gpu_required=2,
            duration_hours=2,
            deadline_hour=20,
            priority="LOW",
        ),
    ]

    results = evaluate_workloads(
        workloads=workloads,
        current_hour=0,
        available_safe_power_kw=10,
    )

    summary = summarize_admission(
        results
    )

    assert summary["total"] == 2

    assert summary["protect"] == 1

    assert summary["admit"] == 1

    print(
        "POWEROS ADMISSION CONTROL TEST PASSED"
    )


if __name__ == "__main__":

    main()