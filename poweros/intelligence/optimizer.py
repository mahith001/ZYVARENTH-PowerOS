from poweros.intelligence.safety_engine import (
    calculate_safe_power_limit,
)


DEFAULT_GPU_POWER_KW = 0.7


def calculate_workload_power(
    gpu_required,
    gpu_power_kw=DEFAULT_GPU_POWER_KW,
):
    return gpu_required * gpu_power_kw


def find_feasible_start_times(
    state,
    workload,
    horizon_hours=24,
    gpu_power_kw=DEFAULT_GPU_POWER_KW,
    safe_power_limit_kw=None,
):
    """
    Find hours where the workload can run without
    exceeding GPU or safe power limits.
    """

    if safe_power_limit_kw is None:

        safe_power_limit_kw = (
            calculate_safe_power_limit(
                state.power.available_power_kw
            )
        )

    required_power = calculate_workload_power(
        workload.gpu_required,
        gpu_power_kw,
    )

    if required_power > safe_power_limit_kw:
        return []

    available_gpus = (
        state.available_gpu_count()
    )

    if workload.gpu_required > available_gpus:
        return []

    latest_start = min(
        horizon_hours - int(workload.duration_hours),
        workload.deadline_hour
        - int(workload.duration_hours),
    )

    if latest_start < 0:
        return []

    feasible = []

    for hour in range(
        latest_start + 1
    ):
        feasible.append(hour)

    return feasible


def calculate_energy_cost(
    power_kw,
    duration_hours,
    electricity_price,
    solar_power_kw=0.0,
    battery_power_kw=0.0,
):
    """

    Estimate energy cost after solar and battery
    contribution.

    Solar is treated as zero-cost energy.
    Battery has already been assigned a cost by
    the caller if required.
    """

    total_energy = (
        power_kw * duration_hours
    )

    solar_energy = min(
        total_energy,
        solar_power_kw * duration_hours,
    )

    remaining_energy = (
        total_energy
        - solar_energy
    )

    battery_energy = min(
        remaining_energy,
        battery_power_kw * duration_hours,
    )

    grid_energy = (
        remaining_energy
        - battery_energy
    )

    return (
        solar_energy * 0.0
        + battery_energy * 6.0
        + grid_energy * electricity_price
    )


def score_start_time(
    start_hour,
    workload,
    state,
    solar_power_by_hour=None,
    electricity_prices=None,
):
    """
    Lower score = better schedule.
    """

    if electricity_prices is None:

        electricity_prices = [
            state.power.electricity_price_per_kwh
            for _ in range(24)
        ]

    if solar_power_by_hour is None:

        solar_power_by_hour = [
            state.power.solar_power_kw
            for _ in range(24)
        ]

    duration = int(
        workload.duration_hours
    )

    power_kw = calculate_workload_power(
        workload.gpu_required
    )

    total_cost = 0.0

    for hour in range(
        start_hour,
        start_hour + duration,
    ):

        price = electricity_prices[
            hour % len(electricity_prices)
        ]

        solar = solar_power_by_hour[
            hour % len(solar_power_by_hour)
        ]

        total_cost += calculate_energy_cost(
            power_kw=power_kw,
            duration_hours=1,
            electricity_price=price,
            solar_power_kw=solar,
            battery_power_kw=state.power.battery_available_kw,
        )

    deadline_margin = (
        workload.deadline_hour
        - (
            start_hour
            + duration
        )
    )

    # Lower cost is better.
    # Earlier high-priority jobs receive
    # additional preference.
    priority_bonus = {
        "HIGH": -100.0,
        "MEDIUM": -25.0,
        "LOW": 0.0,
    }.get(
        workload.priority.upper(),
        0.0,
    )

    return (
        total_cost
        - deadline_margin
        + priority_bonus
    )


def optimize_workloads(
    state,
    horizon_hours=24,
    electricity_prices=None,
    solar_power_by_hour=None,
    gpu_power_kw=DEFAULT_GPU_POWER_KW,
    reserve_percent=15.0,
    admission_results=None,
):
    """
    Optimize workloads while respecting Admission Control.

    Admission actions:

        ADMIT   -> normal optimization
        SHIFT   -> optimization may find a future slot
        DELAY   -> do not schedule
        PROTECT -> prioritize deadline protection
    """

    if electricity_prices is None:

        electricity_prices = [
            state.power.electricity_price_per_kwh
            for _ in range(horizon_hours)
        ]

    if solar_power_by_hour is None:

        solar_power_by_hour = [
            state.power.solar_power_kw
            for _ in range(horizon_hours)
        ]

    safe_power_limit_kw = (
        state.power.available_power_kw
        * (
            1
            - reserve_percent / 100.0
        )
    )

    # ---------------------------------------------------------
    # BUILD ADMISSION MAP
    # ---------------------------------------------------------

    admission_map = {}

    if admission_results:

        for item in admission_results:

            workload_id = item.get(
                "workload_id"
            )

            if workload_id:

                admission_map[
                    workload_id
                ] = item.get(
                    "action",
                    "ADMIT",
                )

    # ---------------------------------------------------------
    # WORKLOAD PRIORITY
    # ---------------------------------------------------------

    priority_order = {
        "HIGH": 0,
        "MEDIUM": 1,
        "LOW": 2,
    }

    workloads = sorted(
        state.workloads,
        key=lambda workload: (
            priority_order.get(
                workload.priority.upper(),
                3,
            ),
            workload.deadline_hour,
        ),
    )

    # ---------------------------------------------------------
    # HOURLY RESOURCE TRACKING
    # ---------------------------------------------------------

    hourly_gpu_usage = [
        0
        for _ in range(horizon_hours)
    ]

    hourly_power_usage = [
        0.0
        for _ in range(horizon_hours)
    ]

    scheduled = []

    unscheduled = []

    # ---------------------------------------------------------
    # PROCESS WORKLOADS
    # ---------------------------------------------------------

    for workload in workloads:

        admission_action = (
            admission_map.get(
                workload.workload_id,
                "ADMIT",
            )
        )

        # -----------------------------------------------------
        # DELAY
        # -----------------------------------------------------

        if admission_action == "DELAY":

            unscheduled.append(
                {
                    "workload_id":
                        workload.workload_id,

                    "reason":
                        "Admission control requested delay",

                    "admission_action":
                        admission_action,
                }
            )

            continue

        # -----------------------------------------------------
        # POWER REQUIREMENT
        # -----------------------------------------------------

        required_power = (
            calculate_workload_power(
                workload.gpu_required,
                gpu_power_kw,
            )
        )

        # -----------------------------------------------------
        # FEASIBLE START TIMES
        # -----------------------------------------------------

        feasible_times = (
            find_feasible_start_times(
                state=state,
                workload=workload,
                horizon_hours=horizon_hours,
                gpu_power_kw=gpu_power_kw,
                safe_power_limit_kw=(
                    safe_power_limit_kw
                ),
            )
        )

        best_start = None
        best_score = None

        # -----------------------------------------------------
        # FIND BEST SLOT
        # -----------------------------------------------------

        for start_hour in feasible_times:

            duration = int(
                workload.duration_hours
            )

            valid = True

            for hour in range(
                start_hour,
                start_hour + duration,
            ):

                if hour >= horizon_hours:

                    valid = False
                    break

                projected_gpu_usage = (
                    hourly_gpu_usage[hour]
                    + workload.gpu_required
                )

                projected_power_usage = (
                    hourly_power_usage[hour]
                    + required_power
                )

                if (
                    projected_gpu_usage
                    > state.total_gpu_count()
                ):

                    valid = False
                    break

                if (
                    projected_power_usage
                    > safe_power_limit_kw
                ):

                    valid = False
                    break

            if not valid:
                continue

            score = score_start_time(
                start_hour=start_hour,
                workload=workload,
                state=state,
                solar_power_by_hour=(
                    solar_power_by_hour
                ),
                electricity_prices=(
                    electricity_prices
                ),
            )

            # -------------------------------------------------
            # PROTECT DEADLINE
            # -------------------------------------------------

            if admission_action == "PROTECT":

                deadline_margin = (
                    workload.deadline_hour
                    - (
                        start_hour
                        + int(
                            workload.duration_hours
                        )
                    )
                )

                # Strongly favor the earliest
                # feasible slot for protection.
                score += (
                    deadline_margin * 1000
                )

            # -------------------------------------------------
            # SHIFT
            # -------------------------------------------------

            elif admission_action == "SHIFT":

                # SHIFT means don't insist on
                # running immediately.
                #
                # Cost optimization can choose
                # a later feasible slot.
                score += (
                    start_hour * 0.1
                )

            if (
                best_score is None
                or score < best_score
            ):

                best_score = score
                best_start = start_hour

        # -----------------------------------------------------
        # NO FEASIBLE SLOT
        # -----------------------------------------------------

        if best_start is None:

            unscheduled.append(
                {
                    "workload_id":
                        workload.workload_id,

                    "reason":
                        "No safe feasible slot",

                    "admission_action":
                        admission_action,
                }
            )

            continue

        # -----------------------------------------------------
        # RESERVE RESOURCES
        # -----------------------------------------------------

        duration = int(
            workload.duration_hours
        )

        for hour in range(
            best_start,
            best_start + duration,
        ):

            hourly_gpu_usage[
                hour
            ] += workload.gpu_required

            hourly_power_usage[
                hour
            ] += required_power

        # -----------------------------------------------------
        # RECORD SCHEDULE
        # -----------------------------------------------------

        scheduled.append(
            {
                "workload_id":
                    workload.workload_id,

                "start_hour":
                    best_start,

                "duration_hours":
                    duration,

                "finish_hour": 
                    best_start + duration,

                "gpu_required":
                    workload.gpu_required,

                "power_kw":
                    required_power,

                "deadline_hour":
                    workload.deadline_hour,

                "priority":
                    workload.priority,

                "admission_action":
                    admission_action,

                "status":
                    "SCHEDULED",
            }
        )

    return {
        "scheduled": scheduled,
        "unscheduled": unscheduled,
        "hourly_gpu_usage":
            hourly_gpu_usage,
        "hourly_power_usage":
            hourly_power_usage,
        "safe_power_limit_kw":
            safe_power_limit_kw,
    }


def summarize_optimization(
    schedule
):
    scheduled = schedule.get(
        "scheduled",
        [],
    )

    unscheduled = schedule.get(
        "unscheduled",
        [],
    )

    return {
        "scheduled_count":
            len(scheduled),

        "unscheduled_count":
            len(unscheduled),

        "total_count":
            len(scheduled)
            + len(unscheduled),

        "success_rate_percent":
            (
                len(scheduled)
                / (
                    len(scheduled)
                    + len(unscheduled)
                )
                * 100
                if (
                    len(scheduled)
                    + len(unscheduled)
                )
                > 0
                else 0.0
            ),
    }


def print_optimization_report(
    schedule,
    summary,
):

    print("\n" + "=" * 60)
    print("POWEROS OPTIMIZATION")
    print("=" * 60)

    print(
        f"Scheduled: "
        f"{summary['scheduled_count']}"
    )

    print(
        f"Unscheduled: "
        f"{summary['unscheduled_count']}"
    )

    print(
        f"Success Rate: "
        f"{summary['success_rate_percent']:.2f}%"
    )

    print("\nSCHEDULE")

    for item in schedule[
        "scheduled"
    ]:

        print(
            f"{item['workload_id']} | "
            f"Start: {item['start_hour']} | "
            f"Duration: {item['duration_hours']}h | "
            f"GPUs: {item['gpu_required']} | "
            f"Power: {item['power_kw']:.2f} kW | "
            f"Admission: "
            f"{item['admission_action']}"
        )

    print("\nUNSCHEDULED")

    for item in schedule[
        "unscheduled"
    ]:

        print(
            f"{item['workload_id']} | "
            f"Reason: {item['reason']} | "
            f"Admission: "
            f"{item.get('admission_action', 'N/A')}"
        )