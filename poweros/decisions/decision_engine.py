# =============================================================
# ZYVARENTH POWEROS
# DECISION ENGINE
# =============================================================


RUN = "RUN"
WAIT = "WAIT"
SHIFT = "SHIFT"
PROTECT_DEADLINE = "PROTECT_DEADLINE"


# =============================================================
# CREATE ONE WORKLOAD DECISION
# =============================================================

def create_workload_decision(
    workload,
    current_hour=0,
):
    """
    Create an operational decision for one workload.
    """

    # ---------------------------------------------------------
    # SAFETY CHECK
    # ---------------------------------------------------------

    if not isinstance(
        workload,
        dict,
    ):
        return {
            "workload_id": "UNKNOWN",
            "action": WAIT,
            "reason": "Invalid workload record",
            "status": "INVALID",
        }

    # ---------------------------------------------------------
    # READ WORKLOAD
    # ---------------------------------------------------------

    workload_id = workload.get(
        "workload_id",
        "UNKNOWN",
    )

    status = workload.get(
        "status",
        "SCHEDULED",
    )

    start_hour = workload.get(
        "start_hour",
        None,
    )

    duration_hours = workload.get(
        "duration_hours",
        0,
    )

    deadline_hour = workload.get(
        "deadline_hour",
        0,
    )

    priority = str(
        workload.get(
            "priority",
            "MEDIUM",
        )
    ).upper()

    admission_action = workload.get(
        "admission_action",
        "ADMIT",
    )

    # ---------------------------------------------------------
    # UNSCHEDULED WORKLOAD
    # ---------------------------------------------------------

    if status != "SCHEDULED":

        if admission_action == "SHIFT":

            return {
                "workload_id": workload_id,
                "action": SHIFT,
                "reason": (
                    "Workload must be shifted "
                    "to another safe slot"
                ),
                "status": status,
                "priority": priority,
                "deadline_hour": deadline_hour,
                "admission_action": admission_action,
            }

        return {
            "workload_id": workload_id,
            "action": PROTECT_DEADLINE,
            "reason": (
                "Workload is unscheduled "
                "and requires deadline protection"
            ),
            "status": status,
            "priority": priority,
            "deadline_hour": deadline_hour,
            "admission_action": admission_action,
        }

    # ---------------------------------------------------------
    # NO START TIME
    # ---------------------------------------------------------

    if start_hour is None:

        return {
            "workload_id": workload_id,
            "action": WAIT,
            "reason": (
                "Scheduled workload has no start time"
            ),
            "status": status,
            "priority": priority,
            "deadline_hour": deadline_hour,
            "admission_action": admission_action,
        }

    # ---------------------------------------------------------
    # NORMALIZE VALUES
    # ---------------------------------------------------------

    try:
        start_hour = int(
            start_hour
        )
    except (
        TypeError,
        ValueError,
    ):
        start_hour = 0

    try:
        duration_hours = int(
            duration_hours
        )
    except (
        TypeError,
        ValueError,
    ):
        duration_hours = 0

    try:
        deadline_hour = int(
            deadline_hour
        )
    except (
        TypeError,
        ValueError,
    ):
        deadline_hour = 0

    # ---------------------------------------------------------
    # CALCULATE END HOUR
    # ---------------------------------------------------------

    end_hour = (
        start_hour
        + duration_hours
    )

    # ---------------------------------------------------------
    # DEADLINE PROTECTION
    # ---------------------------------------------------------

    if end_hour > deadline_hour:

        return {
            "workload_id": workload_id,
            "action": PROTECT_DEADLINE,
            "reason": (
                "Workload would exceed its deadline"
            ),
            "status": status,
            "priority": priority,
            "start_hour": start_hour,
            "duration_hours": duration_hours,
            "deadline_hour": deadline_hour,
            "admission_action": admission_action,
        }

    # ---------------------------------------------------------
    # RUN NOW
    # ---------------------------------------------------------

    if start_hour == current_hour:

        return {
            "workload_id": workload_id,
            "action": RUN,
            "reason": (
                "Workload is scheduled to run now"
            ),
            "status": status,
            "priority": priority,
            "start_hour": start_hour,
            "duration_hours": duration_hours,
            "deadline_hour": deadline_hour,
            "admission_action": admission_action,
        }

    # ---------------------------------------------------------
    # HIGH PRIORITY FUTURE WORKLOAD
    # ---------------------------------------------------------

    if (
        priority == "HIGH"
        and start_hour > current_hour
    ):

        return {
            "workload_id": workload_id,
            "action": PROTECT_DEADLINE,
            "reason": (
                "High-priority workload is scheduled "
                "for a future time"
            ),
            "status": status,
            "priority": priority,
            "start_hour": start_hour,
            "duration_hours": duration_hours,
            "deadline_hour": deadline_hour,
            "admission_action": admission_action,
        }

    # ---------------------------------------------------------
    # FUTURE WORKLOAD
    # ---------------------------------------------------------

    if start_hour > current_hour:

        return {
            "workload_id": workload_id,
            "action": SHIFT,
            "reason": (
                "Workload is scheduled for a future time"
            ),
            "status": status,
            "priority": priority,
            "start_hour": start_hour,
            "duration_hours": duration_hours,
            "deadline_hour": deadline_hour,
            "admission_action": admission_action,
        }

    # ---------------------------------------------------------
    # FALLBACK
    # ---------------------------------------------------------

    return {
        "workload_id": workload_id,
        "action": WAIT,
        "reason": (
            "No immediate action required"
        ),
        "status": status,
        "priority": priority,
        "start_hour": start_hour,
        "duration_hours": duration_hours,
        "deadline_hour": deadline_hour,
        "admission_action": admission_action,
    }


# =============================================================
# CREATE DECISIONS
# =============================================================

def create_decisions(
    schedule,
    current_hour=0,
):
    """
    Accepts either:

    1. Optimizer schedule dictionary

    OR

    2. Direct list of workload dictionaries.
    """

    decisions = []

    # =========================================================
    # OPTIMIZER DICTIONARY
    # =========================================================

    if isinstance(
        schedule,
        dict,
    ):

        scheduled_workloads = schedule.get(
            "scheduled",
            [],
        )

        unscheduled_workloads = schedule.get(
            "unscheduled",
            [],
        )

        if not isinstance(
            scheduled_workloads,
            list,
        ):
            scheduled_workloads = []

        if not isinstance(
            unscheduled_workloads,
            list,
        ):
            unscheduled_workloads = []

        # Scheduled
        for workload in scheduled_workloads:

            decisions.append(
                create_workload_decision(
                    workload,
                    current_hour,
                )
            )

        # Unscheduled
        for workload in unscheduled_workloads:

            decisions.append(
                create_workload_decision(
                    workload,
                    current_hour,
                )
            )

        return decisions

    # =========================================================
    # DIRECT LIST
    # =========================================================

    if isinstance(
        schedule,
        list,
    ):

        for workload in schedule:

            decisions.append(
                create_workload_decision(
                    workload,
                    current_hour,
                )
            )

        return decisions

    return decisions


# =============================================================
# SUMMARIZE DECISIONS
# =============================================================

def summarize_decisions(
    decisions,
):
    """
    Create a decision summary.

    Multiple key names are intentionally provided
    for compatibility with the existing PowerOS
    tests and orchestrator.
    """

    # ---------------------------------------------------------
    # MAIN SUMMARY
    # ---------------------------------------------------------

    total_decisions = 0

    run_decisions = 0
    wait_decisions = 0
    shift_decisions = 0
    protect_deadline_decisions = 0

    # ---------------------------------------------------------
    # PROCESS
    # ---------------------------------------------------------

    if isinstance(
        decisions,
        list,
    ):

        for decision in decisions:

            if not isinstance(
                decision,
                dict,
            ):
                continue

            action = decision.get(
                "action",
                WAIT,
            )

            total_decisions += 1

            if action == RUN:

                run_decisions += 1

            elif action == WAIT:

                wait_decisions += 1

            elif action == SHIFT:

                shift_decisions += 1

            elif action == PROTECT_DEADLINE:

                protect_deadline_decisions += 1

    # ---------------------------------------------------------
    # RETURN
    # ---------------------------------------------------------

    return {

        # =====================================================
        # ORIGINAL / EXPLICIT NAMES
        # =====================================================

        "total_decisions":
            total_decisions,

        "run_decisions":
            run_decisions,

        "wait_decisions":
            wait_decisions,

        "shift_decisions":
            shift_decisions,

        "protect_deadline_decisions":
            protect_deadline_decisions,

        # =====================================================
        # SHORT NAMES
        # =====================================================

        "total":
            total_decisions,

        "run":
            run_decisions,

        "wait":
            wait_decisions,

        "shift":
            shift_decisions,

        "protect_deadline":
            protect_deadline_decisions,

        # =====================================================
        # ORCHESTRATOR COMPATIBILITY
        # =====================================================

        "run_actions":
            run_decisions,

        "shift_actions":
            shift_decisions,

        "deadline_protection_actions":
            protect_deadline_decisions,
    }


# =============================================================
# PRINT DECISION REPORT
# =============================================================

def print_decision_report(
    decisions,
    summary,
):

    print("\n" + "=" * 60)

    print(
        "POWEROS DECISION ENGINE"
    )

    print("=" * 60)

    print(
        f"Total Decisions: "
        f"{summary.get('total_decisions', 0)}"
    )

    print(
        f"RUN: "
        f"{summary.get('run_decisions', 0)}"
    )

    print(
        f"WAIT: "
        f"{summary.get('wait_decisions', 0)}"
    )

    print(
        f"SHIFT: "
        f"{summary.get('shift_decisions', 0)}"
    )

    print(
        f"PROTECT DEADLINE: "
        f"{summary.get('protect_deadline_decisions', 0)}"
    )

    print("\nDECISIONS")
    print("-" * 60)

    if not isinstance(
        decisions,
        list,
    ):
        return

    for decision in decisions:

        if not isinstance(
            decision,
            dict,
        ):
            continue

        print(
            f"{decision.get('workload_id', 'UNKNOWN')} | "
            f"Action: "
            f"{decision.get('action', WAIT)} | "
            f"Reason: "
            f"{decision.get('reason', '')}"
        )