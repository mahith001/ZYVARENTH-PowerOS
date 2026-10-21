from poweros.decisions.decision_engine import (
    create_decisions,
    summarize_decisions,
)


def test_decision_engine():

    schedule = [
        {
            "workload_id": "JOB-001",
            "start_hour": 0,
            "finish_hour": 2,
            "deadline_hour": 8,
            "priority": "HIGH",
            "status": "SCHEDULED",
        },
        {
            "workload_id": "JOB-002",
            "start_hour": 5,
            "finish_hour": 7,
            "deadline_hour": 12,
            "priority": "LOW",
            "status": "SCHEDULED",
        },
        {
            "workload_id": "JOB-003",
            "start_hour": None,
            "finish_hour": None,
            "deadline_hour": 10,
            "priority": "MEDIUM",
            "status": "UNSCHEDULED",
        },
    ]

    decisions = create_decisions(
        schedule,
        current_hour=0,
    )

    summary = summarize_decisions(
        decisions
    )

    assert len(decisions) == 3

    assert summary["run"] == 1

    assert summary["shift"] == 1

    assert summary["protect_deadline"] == 1

    assert summary["total_decisions"] == 3


if __name__ == "__main__":

    test_decision_engine()

    print()
    print("POWEROS DECISION ENGINE TEST PASSED")