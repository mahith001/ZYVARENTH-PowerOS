# =============================================================
# ZYVARENTH POWEROS
# WORKLOAD LIFECYCLE SIMULATOR
# =============================================================

from copy import deepcopy


# =============================================================
# WORKLOAD STATES
# =============================================================

QUEUED = "QUEUED"
ADMITTED = "ADMITTED"
SCHEDULED = "SCHEDULED"
RUNNING = "RUNNING"
COMPLETED = "COMPLETED"

SHIFTED = "SHIFTED"
PAUSED = "PAUSED"
FAILED = "FAILED"


# =============================================================
# CREATE WORKLOAD RECORD
# =============================================================

def create_workload_record(
    workload_id,
    gpu_required,
    duration_hours,
    deadline_hour,
    priority="MEDIUM",
):
    """
    Create a workload lifecycle record.
    """

    return {
        "workload_id": workload_id,
        "gpu_required": gpu_required,
        "duration_hours": duration_hours,
        "remaining_hours": duration_hours,
        "deadline_hour": deadline_hour,
        "priority": priority,
        "state": QUEUED,
        "start_hour": None,
        "completion_hour": None,
        "shift_count": 0,
        "pause_count": 0,
        "deadline_met": None,
    }


# =============================================================
# LOAD WORKLOADS
# =============================================================

def initialize_workloads(
    workloads,
):
    """
    Convert optimizer workload records into
    lifecycle records.
    """

    records = []

    if not isinstance(
        workloads,
        list,
    ):
        return records

    for workload in workloads:

        if not isinstance(
            workload,
            dict,
        ):
            continue

        record = create_workload_record(
            workload_id=workload.get(
                "workload_id",
                "UNKNOWN",
            ),
            gpu_required=int(
                workload.get(
                    "gpu_required",
                    0,
                )
            ),
            duration_hours=int(
                workload.get(
                    "duration_hours",
                    0,
                )
            ),
            deadline_hour=int(
                workload.get(
                    "deadline_hour",
                    0,
                )
            ),
            priority=workload.get(
                "priority",
                "MEDIUM",
            ),
        )

        # -----------------------------------------------------
        # Copy scheduling information when available
        # -----------------------------------------------------

        if "start_hour" in workload:

            record["start_hour"] = workload.get(
                "start_hour"
            )

        if workload.get(
            "admission_action"
        ) == "ADMIT":

            record["state"] = ADMITTED

        records.append(
            record
        )

    return records


# =============================================================
# APPLY OPTIMIZER SCHEDULE
# =============================================================

def apply_schedule(
    lifecycle_workloads,
    schedule,
):
    """
    Apply optimizer output to lifecycle records.
    """

    if not isinstance(
        lifecycle_workloads,
        list,
    ):
        return lifecycle_workloads

    if not isinstance(
        schedule,
        dict,
    ):
        return lifecycle_workloads

    scheduled = schedule.get(
        "scheduled",
        [],
    )

    scheduled_map = {}

    if isinstance(
        scheduled,
        list,
    ):

        for item in scheduled:

            if not isinstance(
                item,
                dict,
            ):
                continue

            workload_id = item.get(
                "workload_id"
            )

            if workload_id:

                scheduled_map[
                    workload_id
                ] = item

    # ---------------------------------------------------------
    # Apply schedule
    # ---------------------------------------------------------

    for workload in lifecycle_workloads:

        workload_id = workload.get(
            "workload_id"
        )

        schedule_item = scheduled_map.get(
            workload_id
        )

        if schedule_item is None:

            if workload.get(
                "state"
            ) != COMPLETED:

                workload["state"] = QUEUED

            continue

        workload["state"] = SCHEDULED

        workload["start_hour"] = (
            schedule_item.get(
                "start_hour"
            )
        )

        workload["duration_hours"] = int(
            schedule_item.get(
                "duration_hours",
                workload.get(
                    "duration_hours",
                    0,
                ),
            )
        )

        workload["remaining_hours"] = (
            workload["duration_hours"]
        )

    return lifecycle_workloads


# =============================================================
# ADMISSION STEP
# =============================================================

def admit_workloads(
    lifecycle_workloads,
    admission_results,
):
    """
    Apply Admission Control results.
    """

    if not isinstance(
        lifecycle_workloads,
        list,
    ):
        return lifecycle_workloads

    admission_map = {}

    if isinstance(
        admission_results,
        list,
    ):

        for result in admission_results:

            if not isinstance(
                result,
                dict,
            ):
                continue

            workload_id = result.get(
                "workload_id"
            )

            if workload_id:

                admission_map[
                    workload_id
                ] = result

    for workload in lifecycle_workloads:

        workload_id = workload.get(
            "workload_id"
        )

        result = admission_map.get(
            workload_id
        )

        if result is None:
            continue

        action = result.get(
            "action"
        )

        if action == "ADMIT":

            if workload.get(
                "state"
            ) == QUEUED:

                workload["state"] = ADMITTED

        elif action == "SHIFT":

            workload["state"] = SHIFTED

            workload["shift_count"] += 1

        elif action == "DELAY":

            workload["state"] = QUEUED

        elif action == "PROTECT":

            workload["state"] = QUEUED

    return lifecycle_workloads


# =============================================================
# START WORKLOAD
# =============================================================

def start_workload(
    workload,
    current_hour,
):
    """
    Move a scheduled workload to RUNNING.
    """

    if not isinstance(
        workload,
        dict,
    ):
        return workload

    if workload.get(
        "state"
    ) not in (
        SCHEDULED,
        ADMITTED,
        SHIFTED,
    ):
        return workload

    start_hour = workload.get(
        "start_hour"
    )

    if start_hour is None:
        return workload

    if current_hour >= int(
        start_hour
    ):

        if workload.get(
            "start_hour"
        ) is None:

            workload["start_hour"] = (
                current_hour
            )

        workload["state"] = RUNNING

    return workload


# =============================================================
# ADVANCE RUNNING WORKLOAD
# =============================================================

def advance_workload(
    workload,
    current_hour,
):
    """
    Advance a running workload by one hour.
    """

    if not isinstance(
        workload,
        dict,
    ):
        return workload

    if workload.get(
        "state"
    ) != RUNNING:

        return workload

    remaining = int(
        workload.get(
            "remaining_hours",
            0,
        )
    )

    if remaining > 0:

        remaining -= 1

        workload[
            "remaining_hours"
        ] = remaining

    # ---------------------------------------------------------
    # Completed
    # ---------------------------------------------------------

    if remaining <= 0:

        workload["state"] = COMPLETED

        workload[
            "completion_hour"
        ] = current_hour + 1

        completion_hour = workload[
            "completion_hour"
        ]

        deadline_hour = int(
            workload.get(
                "deadline_hour",
                0,
            )
        )

        workload[
            "deadline_met"
        ] = (
            completion_hour
            <= deadline_hour
        )

    return workload


# =============================================================
# PAUSE WORKLOAD
# =============================================================

def pause_workload(
    workload,
):
    """
    Pause a running workload.
    """

    if not isinstance(
        workload,
        dict,
    ):
        return workload

    if workload.get(
        "state"
    ) == RUNNING:

        workload["state"] = PAUSED

        workload[
            "pause_count"
        ] += 1

    return workload


# =============================================================
# RESUME WORKLOAD
# =============================================================

def resume_workload(
    workload,
):
    """
    Resume a paused workload.
    """

    if not isinstance(
        workload,
        dict,
    ):
        return workload

    if workload.get(
        "state"
    ) == PAUSED:

        workload["state"] = RUNNING

    return workload


# =============================================================
# SHIFT WORKLOAD
# =============================================================

def shift_workload(
    workload,
    new_start_hour,
):
    """
    Shift workload to a future start hour.
    """

    if not isinstance(
        workload,
        dict,
    ):
        return workload

    workload[
        "start_hour"
    ] = new_start_hour

    workload[
        "state"
    ] = SHIFTED

    workload[
        "shift_count"
    ] += 1

    return workload


# =============================================================
# PROCESS ONE HOUR
# =============================================================

def process_hour(
    lifecycle_workloads,
    current_hour,
    power_available=True,
):
    """
    Process one simulated hour.

    If power is unavailable, running workloads
    are paused.

    Otherwise scheduled workloads can start.
    """

    if not isinstance(
        lifecycle_workloads,
        list,
    ):
        return lifecycle_workloads

    # ---------------------------------------------------------
    # POWER CONSTRAINT
    # ---------------------------------------------------------

    if not power_available:

        for workload in lifecycle_workloads:

            if workload.get(
                "state"
            ) == RUNNING:

                pause_workload(
                    workload
                )

        return lifecycle_workloads

    # ---------------------------------------------------------
    # RESUME PAUSED WORKLOADS
    # ---------------------------------------------------------

    for workload in lifecycle_workloads:

        if workload.get(
            "state"
        ) == PAUSED:

            resume_workload(
                workload
            )

    # ---------------------------------------------------------
    # START SCHEDULED WORKLOADS
    # ---------------------------------------------------------

    for workload in lifecycle_workloads:

        start_workload(
            workload,
            current_hour,
        )

    # ---------------------------------------------------------
    # ADVANCE RUNNING WORKLOADS
    # ---------------------------------------------------------

    for workload in lifecycle_workloads:

        if workload.get(
            "state"
        ) == RUNNING:

            advance_workload(
                workload,
                current_hour,
            )

    return lifecycle_workloads


# =============================================================
# RUN LIFECYCLE SIMULATION
# =============================================================

def run_lifecycle_simulation(
    workloads,
    schedule=None,
    admission_results=None,
    start_hour=0,
    horizon_hours=24,
    power_constraint_hours=None,
):
    """
    Run the complete workload lifecycle simulation.
    """

    lifecycle = initialize_workloads(
        workloads
    )

    # ---------------------------------------------------------
    # Admission
    # ---------------------------------------------------------

    if admission_results is not None:

        admit_workloads(
            lifecycle,
            admission_results,
        )

    # ---------------------------------------------------------
    # Schedule
    # ---------------------------------------------------------

    if schedule is not None:

        apply_schedule(
            lifecycle,
            schedule,
        )

    # ---------------------------------------------------------
    # Power constraint hours
    # ---------------------------------------------------------

    if power_constraint_hours is None:

        power_constraint_hours = set()

    else:

        power_constraint_hours = set(
            power_constraint_hours
        )

    # ---------------------------------------------------------
    # Hourly simulation
    # ---------------------------------------------------------

    history = []

    for hour in range(
        start_hour,
        start_hour + horizon_hours,
    ):

        power_available = (
            hour
            not in power_constraint_hours
        )

        process_hour(
            lifecycle_workloads=lifecycle,
            current_hour=hour,
            power_available=power_available,
        )

        snapshot = []

        for workload in lifecycle:

            snapshot.append(
                {
                    "workload_id":
                        workload.get(
                            "workload_id"
                        ),

                    "state":
                        workload.get(
                            "state"
                        ),

                    "remaining_hours":
                        workload.get(
                            "remaining_hours"
                        ),
                }
            )

        history.append(
            {
                "hour": hour,
                "power_available":
                    power_available,
                "workloads":
                    snapshot,
            }
        )

        # -----------------------------------------------------
        # Stop when everything completed
        # -----------------------------------------------------

        if all(
            workload.get(
                "state"
            )
            == COMPLETED
            for workload in lifecycle
        ):

            break

    return {
        "workloads": lifecycle,
        "history": history,
    }


# =============================================================
# LIFECYCLE SUMMARY
# =============================================================

def summarize_lifecycle(
    result,
):
    """
    Create lifecycle performance metrics.
    """

    workloads = result.get(
        "workloads",
        [],
    )

    summary = {
        "total_workloads": 0,
        "queued": 0,
        "admitted": 0,
        "scheduled": 0,
        "running": 0,
        "completed": 0,
        "shifted": 0,
        "paused": 0,
        "failed": 0,
        "deadline_met": 0,
        "deadline_missed": 0,
        "completion_rate_percent": 0.0,
        "deadline_success_rate_percent": 0.0,
    }

    if not isinstance(
        workloads,
        list,
    ):
        return summary

    summary[
        "total_workloads"
    ] = len(workloads)

    for workload in workloads:

        state = workload.get(
            "state"
        )

        if state == QUEUED:
            summary["queued"] += 1

        elif state == ADMITTED:
            summary["admitted"] += 1

        elif state == SCHEDULED:
            summary["scheduled"] += 1

        elif state == RUNNING:
            summary["running"] += 1

        elif state == COMPLETED:
            summary["completed"] += 1

        elif state == SHIFTED:
            summary["shifted"] += 1

        elif state == PAUSED:
            summary["paused"] += 1

        elif state == FAILED:
            summary["failed"] += 1

        deadline_met = workload.get(
            "deadline_met"
        )

        if deadline_met is True:

            summary[
                "deadline_met"
            ] += 1

        elif deadline_met is False:

            summary[
                "deadline_missed"
            ] += 1

    total = summary[
        "total_workloads"
    ]

    if total > 0:

        summary[
            "completion_rate_percent"
        ] = (
            summary["completed"]
            / total
            * 100
        )

        completed = summary[
            "completed"
        ]

        if completed > 0:

            summary[
                "deadline_success_rate_percent"
            ] = (
                summary["deadline_met"]
                / completed
                * 100
            )

    return summary


# =============================================================
# PRINT REPORT
# =============================================================

def print_lifecycle_report(
    result,
    summary,
):
    """
    Print workload lifecycle results.
    """

    print("\n" + "=" * 65)

    print(
        "POWEROS WORKLOAD LIFECYCLE"
    )

    print("=" * 65)

    print(
        f"Total Workloads: "
        f"{summary['total_workloads']}"
    )

    print(
        f"Completed: "
        f"{summary['completed']}"
    )

    print(
        f"Running: "
        f"{summary['running']}"
    )

    print(
        f"Queued: "
        f"{summary['queued']}"
    )

    print(
        f"Shifted: "
        f"{summary['shifted']}"
    )

    print(
        f"Paused: "
        f"{summary['paused']}"
    )

    print(
        f"Completion Rate: "
        f"{summary['completion_rate_percent']:.2f}%"
    )

    print(
        f"Deadline Met: "
        f"{summary['deadline_met']}"
    )

    print(
        f"Deadline Missed: "
        f"{summary['deadline_missed']}"
    )

    print(
        f"Deadline Success Rate: "
        f"{summary['deadline_success_rate_percent']:.2f}%"
    )

    print("\nWORKLOADS")
    print("-" * 65)

    for workload in result.get(
        "workloads",
        [],
    ):

        print(
            f"{workload.get('workload_id')} | "
            f"State: "
            f"{workload.get('state')} | "
            f"Start: "
            f"{workload.get('start_hour')} | "
            f"Completed: "
            f"{workload.get('completion_hour')} | "
            f"Deadline Met: "
            f"{workload.get('deadline_met')}"
        )