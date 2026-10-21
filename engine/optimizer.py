import pandas as pd
from engine.battery import Battery


# ============================================================
# ZYVARENTH POWEROS V2
# AI COMPUTE - POWER OPTIMIZATION ENGINE
# ============================================================


# ============================================================
# 1. JOB PRIORITIZATION
# ============================================================

def prioritize_jobs(jobs: pd.DataFrame) -> pd.DataFrame:
    """
    Rank workloads according to business importance.

    HIGH workloads are handled first.
    Within the same priority, earlier deadlines are handled first.
    """

    priority_order = {
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3,
    }

    jobs = jobs.copy()

    jobs["priority_rank"] = (
        jobs["priority"]
        .map(priority_order)
        .fillna(3)
    )

    return jobs.sort_values(
        by=["priority_rank", "deadline", "job_id"]
    ).reset_index(drop=True)


# ============================================================
# 2. FIT JOBS INTO POWER LIMIT
# ============================================================

def fit_jobs_to_power_limit(
    jobs: pd.DataFrame,
    power_limit_kw: float,
):
    """
    Select workloads that can run together without exceeding
    the available power limit.
    """

    selected_jobs = []
    waiting_jobs = []

    current_power = 0.0

    for _, job in jobs.iterrows():

        job_power = float(job["power_kw"])

        if current_power + job_power <= power_limit_kw:

            selected_jobs.append(job)
            current_power += job_power

        else:

            waiting_jobs.append(job)

    return (
        pd.DataFrame(selected_jobs),
        pd.DataFrame(waiting_jobs),
    )


# ============================================================
# 3. GRID CAPACITY MODEL
# ============================================================

def get_grid_capacity() -> list:
    """
    Simulated grid capacity available during each hour.

    This represents an interconnection/grid constraint.
    """

    return [
        70.0, 70.0, 68.0, 65.0,
        60.0, 62.0, 65.0, 55.0,
        52.0, 50.0, 50.0, 55.0,
        58.0, 60.0, 65.0, 68.0,
        70.0, 70.0, 70.0, 70.0,
        70.0, 70.0, 70.0, 70.0,
    ]


# ============================================================
# 4. ELECTRICITY PRICE MODEL
# ============================================================

def get_electricity_prices() -> list:
    """
    Simulated time-of-use electricity price.

    Lower values = cheaper electricity.
    Higher values = expensive electricity.
    """

    return [
        5.0, 5.0, 5.0, 5.0,
        6.0, 6.0, 7.0, 8.0,
        10.0, 12.0, 12.0, 10.0,
        9.0, 8.0, 7.0, 6.0,
        5.0, 5.0, 5.0, 5.0,
        5.0, 5.0, 5.0, 5.0,
    ]


# ============================================================
# 5. ENERGY RESOURCE MODEL
# ============================================================

def get_energy_resources() -> dict:
    """
    Simulated renewable and battery-related resources.

    Solar represents renewable generation available to the
    data center during each hour.

    battery_power is retained for compatibility with the
    existing PowerOS interface.
    """

    solar_power_kw = [
        0, 0, 0, 0,
        0, 2, 5, 8,
        10, 12, 12, 10,
        8, 6, 4, 2,
        0, 0, 0, 0,
        0, 0, 0, 0,
    ]

    battery_power_kw = [
        5, 5, 5, 5,
        5, 5, 3, 0,
        0, 0, 0, 0,
        0, 0, 3, 5,
        5, 5, 5, 5,
        5, 5, 5, 5,
    ]

    return {
        "solar_power_kw": solar_power_kw,
        "battery_power_kw": battery_power_kw,
    }


# ============================================================
# 6. JOB COST
# ============================================================

def calculate_job_cost(
    power_kw: float,
    duration_hours: int,
    start_hour: int,
    electricity_prices: list,
) -> float:
    """
    Calculate electricity cost for one workload.
    """

    total_cost = 0.0

    for hour in range(
        start_hour,
        start_hour + duration_hours,
    ):

        if hour >= 24:
            break

        total_cost += (
            power_kw *
            electricity_prices[hour]
        )

    return total_cost


# ============================================================
# 7. DEADLINE SLACK
# ============================================================

def calculate_deadline_slack(
    start_hour: int,
    duration_hours: int,
    deadline: int,
) -> int:
    """
    Calculate remaining time between workload completion
    and its deadline.

    Larger slack = more flexibility.
    """

    finish_hour = start_hour + duration_hours

    return deadline - finish_hour


# ============================================================
# 8. CANDIDATE SCHEDULE SCORE
# ============================================================

def calculate_candidate_score(
    start_hour: int,
    duration_hours: int,
    power_kw: float,
    priority: str,
    deadline: int,
    electricity_prices: list,
    power_usage: list,
    solar_power: list,
) -> float:
    """
    ZYVARENTH PowerOS multi-objective scoring engine.

    Lower score = better scheduling decision.

    Objectives:
        1. Electricity cost
        2. Peak-power pressure
        3. Solar utilization
        4. Deadline risk
        5. Workload priority
    """

    if duration_hours <= 0:
        return float("inf")

    hours = list(
        range(
            start_hour,
            start_hour + duration_hours
        )
    )

    # ========================================================
    # 1. ELECTRICITY COST
    # ========================================================

    total_price = 0.0

    for hour in hours:

        if hour >= 24:
            return float("inf")

        total_price += float(
            electricity_prices[hour]
        )

    average_price = (
        total_price /
        duration_hours
    )

    # ========================================================
    # 2. PEAK-POWER PRESSURE
    # ========================================================

    projected_powers = []

    for hour in hours:

        projected_power = (
            power_usage[hour] +
            power_kw
        )

        projected_powers.append(
            projected_power
        )

    projected_peak = max(
        projected_powers
    )

    # Normalize against PowerOS power limit.

    peak_ratio = (
        projected_peak / 70.0
    )

    # Stronger penalty as the system approaches
    # its available power ceiling.

    peak_penalty = (
        peak_ratio ** 2
    ) * 3.0

    # ========================================================
    # 3. SOLAR UTILIZATION
    # ========================================================

    solar_energy = 0.0

    for hour in hours:

        solar_available = max(
            0.0,
            float(solar_power[hour])
        )

        solar_energy += min(
            power_kw,
            solar_available
        )

    total_workload_energy = (
        power_kw *
        duration_hours
    )

    solar_ratio = (
        solar_energy /
        max(
            total_workload_energy,
            0.01
        )
    )

    # Solar reduces the score.

    solar_benefit = (
        solar_ratio * 2.5
    )

    # ========================================================
    # 4. DEADLINE RISK
    # ========================================================

    finish_hour = (
        start_hour +
        duration_hours
    )

    slack = (
        deadline -
        finish_hour
    )

    if slack <= 0:

        deadline_penalty = 0.0

    elif slack == 1:

        deadline_penalty = 0.10

    elif slack <= 3:

        deadline_penalty = 0.30

    elif slack <= 6:

        deadline_penalty = 0.60

    else:

        deadline_penalty = 1.00

    # ========================================================
    # 5. WORKLOAD PRIORITY
    # ========================================================

    priority_weights = {
        "HIGH": 0.0,
        "MEDIUM": 0.25,
        "LOW": 0.50,
    }

    priority_penalty = (
        priority_weights.get(
            priority,
            0.50
        )
    )

    # ========================================================
    # 6. EARLY-SCHEDULE TIE BREAKER
    # ========================================================

    # Prevent PowerOS from unnecessarily pushing
    # workloads too far into the future.

    time_penalty = (
        start_hour * 0.02
    )

    # ========================================================
    # 7. FINAL MULTI-OBJECTIVE SCORE
    # ========================================================

    score = (
        average_price
        + peak_penalty
        + deadline_penalty
        + priority_penalty
        + time_penalty
        - solar_benefit
    )

    return score


# ============================================================
# 9. POWEROS V2 OPTIMIZER
# ============================================================

def optimize_schedule(
    jobs: pd.DataFrame,
    electricity_prices: list,
    power_limit_kw: float,
    num_gpus: int,
    grid_capacity: list = None,
) -> pd.DataFrame:
    """
    ZYVARENTH PowerOS V2 scheduler.

    Optimizes AI workloads using:

    - electricity price
    - GPU availability
    - power capacity
    - grid capacity
    - solar availability
    - workload priority
    - deadlines
    - peak-power pressure
    """

    jobs = prioritize_jobs(jobs)

    if grid_capacity is None:
        grid_capacity = (
            [power_limit_kw] * 24
        )

    resources = get_energy_resources()

    solar_power = resources[
        "solar_power_kw"
    ]

    power_usage = [0.0] * 24
    gpu_usage = [0] * 24

    scheduled_jobs = []

    # ========================================================
    # Schedule each workload
    # ========================================================

    for _, job in jobs.iterrows():

        job_id = int(job["job_id"])
        duration = int(job["duration_hours"])
        required_gpus = int(job["gpu_required"])
        power = float(job["power_kw"])
        deadline = int(job["deadline"])
        priority = str(job["priority"])

        latest_start = min(
            deadline - duration,
            24 - duration,
        )

        best_start = None
        best_score = float("inf")
        best_cost = None

        # ----------------------------------------------------
        # Impossible workload
        # ----------------------------------------------------

        if latest_start < 0:

            scheduled_jobs.append({
                "job_id": job_id,
                "start_hour": -1,
                "duration_hours": duration,
                "gpu_required": required_gpus,
                "power_kw": power,
                "deadline": deadline,
                "priority": priority,
                "cost": None,
            })

            continue

        # ----------------------------------------------------
        # Test every possible start hour
        # ----------------------------------------------------

        for start in range(
            latest_start + 1
        ):

            feasible = True

            # -----------------------------------------------
            # Check power + GPU constraints
            # -----------------------------------------------

            for hour in range(
                start,
                start + duration,
            ):

                if hour >= 24:
                    feasible = False
                    break

                available_power = min(
                    power_limit_kw,
                    float(grid_capacity[hour]),
                )

                projected_power = (
                    power_usage[hour] +
                    power
                )

                projected_gpus = (
                    gpu_usage[hour] +
                    required_gpus
                )

                if (
                    projected_power >
                    available_power
                ):
                    feasible = False
                    break

                if (
                    projected_gpus >
                    num_gpus
                ):
                    feasible = False
                    break

            if not feasible:
                continue

            # -----------------------------------------------
            # Calculate intelligent score
            # -----------------------------------------------

            score = calculate_candidate_score(
                start_hour=start,
                duration_hours=duration,
                power_kw=power,
                priority=priority,
                deadline=deadline,
                electricity_prices=electricity_prices,
                power_usage=power_usage,
                solar_power=solar_power,
            )

            cost = calculate_job_cost(
                power,
                duration,
                start,
                electricity_prices,
            )

            # -----------------------------------------------
            # Prefer lower score
            # -----------------------------------------------

            if score < best_score:

                best_score = score
                best_start = start
                best_cost = cost

        # ====================================================
        # Commit schedule
        # ====================================================

        if best_start is not None:

            for hour in range(
                best_start,
                best_start + duration,
            ):

                power_usage[hour] += power
                gpu_usage[hour] += required_gpus

            scheduled_jobs.append({
                "job_id": job_id,
                "start_hour": best_start,
                "duration_hours": duration,
                "gpu_required": required_gpus,
                "power_kw": power,
                "deadline": deadline,
                "priority": priority,
                "cost": best_cost,
            })

        else:

            scheduled_jobs.append({
                "job_id": job_id,
                "start_hour": -1,
                "duration_hours": duration,
                "gpu_required": required_gpus,
                "power_kw": power,
                "deadline": deadline,
                "priority": priority,
                "cost": None,
            })

    return pd.DataFrame(
        scheduled_jobs
    )


# ============================================================
# 10. NORMAL DATA CENTER BASELINE
# ============================================================

def calculate_baseline_cost(
    jobs: pd.DataFrame,
    electricity_prices: list,
) -> float:
    """
    Calculate the cost of a conventional scheduler.

    The conventional scheduler:

    - processes workloads by deadline
    - starts workloads at the earliest feasible time
    - respects a 70 kW power limit
    - assumes 100 GPUs
    - does NOT optimize electricity price
    - does NOT optimize solar
    - does NOT optimize battery
    """

    jobs = jobs.copy()

    jobs = jobs.sort_values(
        by=["deadline", "job_id"]
    ).reset_index(drop=True)

    power_usage = [0.0] * 24
    gpu_usage = [0] * 24

    total_cost = 0.0

    power_limit_kw = 70.0
    num_gpus = 100

    for _, job in jobs.iterrows():

        duration = int(
            job["duration_hours"]
        )

        gpu_required = int(
            job["gpu_required"]
        )

        power = float(
            job["power_kw"]
        )

        deadline = int(
            job["deadline"]
        )

        latest_start = min(
            deadline - duration,
            24 - duration,
        )

        scheduled = False

        # Conventional scheduler chooses
        # the FIRST feasible time.

        for start in range(
            max(0, latest_start + 1)
        ):

            feasible = True

            for hour in range(
                start,
                start + duration,
            ):

                if hour >= 24:
                    feasible = False
                    break

                if (
                    power_usage[hour] +
                    power >
                    min(
                        power_limit_kw,
                        get_grid_capacity()[hour],
                    )
                ):
                    feasible = False
                    break

                if (
                    gpu_usage[hour] +
                    gpu_required >
                    num_gpus
                ):
                    feasible = False
                    break

            if not feasible:
                continue

            # Commit earliest feasible schedule.

            for hour in range(
                start,
                start + duration,
            ):

                power_usage[hour] += power
                gpu_usage[hour] += gpu_required

                total_cost += (
                    power *
                    electricity_prices[hour]
                )

            scheduled = True
            break

        # If no feasible slot exists,
        # retain compatibility and do not
        # add impossible workload cost.

        if not scheduled:
            continue

    return total_cost


# ============================================================
# 11. SCHEDULE PERFORMANCE METRICS
# ============================================================

def calculate_schedule_metrics(
    schedule: pd.DataFrame,
    electricity_prices: list,
    num_gpus: int,
    power_limit_kw: float,
) -> dict:
    """
    Calculate complete schedule performance.
    """

    hourly_power = [0.0] * 24
    hourly_gpus = [0] * 24

    total_cost = 0.0

    missed_deadlines = 0
    completed_jobs = 0

    for _, job in schedule.iterrows():

        start_hour = int(
            job["start_hour"]
        )

        duration = int(
            job["duration_hours"]
        )

        power = float(
            job["power_kw"]
        )

        gpu_required = int(
            job["gpu_required"]
        )

        deadline = int(
            job["deadline"]
        )

        # ----------------------------------------------------
        # Unscheduled
        # ----------------------------------------------------

        if start_hour < 0:

            missed_deadlines += 1

            continue

        completed_jobs += 1

        finish_hour = (
            start_hour +
            duration
        )

        if finish_hour > deadline:

            missed_deadlines += 1

        # ----------------------------------------------------
        # Hourly usage
        # ----------------------------------------------------

        for hour in range(
            start_hour,
            start_hour + duration,
        ):

            if hour >= 24:
                break

            hourly_power[hour] += power

            hourly_gpus[hour] += (
                gpu_required
            )

            total_cost += (
                power *
                electricity_prices[hour]
            )

    peak_power = max(
        hourly_power
    )

    average_gpu_utilization = (
        sum(hourly_gpus)
        /
        (24 * num_gpus)
    ) * 100

    power_limit_violations = sum(
        1
        for power in hourly_power
        if power > power_limit_kw
    )

    return {
        "total_cost": total_cost,
        "peak_power_kw": peak_power,
        "gpu_utilization_percent":
            average_gpu_utilization,
        "completed_jobs":
            completed_jobs,
        "missed_deadlines":
            missed_deadlines,
        "power_limit_violations":
            power_limit_violations,
    }


# ============================================================
# 12. OPTIMIZED ENERGY DISPATCH
# ============================================================

def calculate_optimized_energy_cost(
    schedule: pd.DataFrame,
    electricity_prices: list,
    grid_capacity: list,
    solar_power: list,
    battery_power: list,
) -> dict:
    """
    PowerOS energy dispatch engine.

    Energy priority:

    1. Solar -> AI workloads
    2. Solar surplus -> battery
    3. Battery -> expensive grid periods
    4. Grid -> remaining demand

    Battery SOC is tracked continuously.
    """

    battery = Battery(
        capacity_kwh=100.0,
        initial_soc=0.80,
        min_soc=0.20,
        max_soc=1.00,
        max_charge_kw=20.0,
        max_discharge_kw=20.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
    )

    hourly_load = [0.0] * 24

    # ========================================================
    # Build hourly AI workload demand
    # ========================================================

    for _, job in schedule.iterrows():

        start = int(
            job["start_hour"]
        )

        duration = int(
            job["duration_hours"]
        )

        power = float(
            job["power_kw"]
        )

        if start < 0:
            continue

        for hour in range(
            start,
            start + duration,
        ):

            if hour >= 24:
                break

            hourly_load[hour] += power

    # ========================================================
    # Energy tracking
    # ========================================================

    hourly_grid = [0.0] * 24
    hourly_solar = [0.0] * 24
    hourly_battery = [0.0] * 24
    hourly_battery_charge = [0.0] * 24
    hourly_unserved = [0.0] * 24

    total_cost = 0.0

    CHEAP_PRICE_THRESHOLD = 6.0
    EXPENSIVE_PRICE_THRESHOLD = 10.0

    # ========================================================
    # Hourly dispatch
    # ========================================================

    for hour in range(24):

        load = hourly_load[hour]

        solar_available = max(
            0.0,
            float(solar_power[hour]),
        )

        # ----------------------------------------------------
        # 1. Solar directly powers AI
        # ----------------------------------------------------

        solar_used = min(
            load,
            solar_available,
        )

        hourly_solar[hour] = solar_used

        remaining_load = max(
            0.0,
            load - solar_used,
        )

        # ----------------------------------------------------
        # 2. Solar surplus charges battery
        # ----------------------------------------------------

        solar_surplus = max(
            0.0,
            solar_available -
            solar_used,
        )

        battery_charge = 0.0

        current_price = float(
            electricity_prices[hour]
        )

        if solar_surplus > 0:

            battery_charge = (
                battery.charge(
                    solar_surplus,
                    1.0,
                )
            )

        # ----------------------------------------------------
        # 3. Cheap grid charging
        # ----------------------------------------------------

        elif current_price <= (
            CHEAP_PRICE_THRESHOLD
        ):

            battery_charge = (
                battery.charge(
                    battery.max_charge_kw,
                    1.0,
                )
            )

        hourly_battery_charge[hour] = (
            battery_charge
        )

        # ----------------------------------------------------
        # 4. Battery discharge
        # ----------------------------------------------------

        battery_used = 0.0

        if (
            remaining_load > 0
            and
            current_price >=
            EXPENSIVE_PRICE_THRESHOLD
        ):

            battery_used = (
                battery.discharge(
                    remaining_load,
                    1.0,
                )
            )

            battery_used = min(
                battery_used,
                remaining_load,
            )

        hourly_battery[hour] = (
            battery_used
        )

        remaining_load = max(
            0.0,
            remaining_load -
            battery_used,
        )

        # ----------------------------------------------------
        # 5. Grid supplies remaining demand
        # ----------------------------------------------------

        available_grid = max(
            0.0,
            float(grid_capacity[hour]),
        )

        grid_used = min(
            remaining_load,
            available_grid,
        )

        hourly_grid[hour] = grid_used

        remaining_load = max(
            0.0,
            remaining_load -
            grid_used,
        )

        # ----------------------------------------------------
        # 6. Track unserved power
        # ----------------------------------------------------

        hourly_unserved[hour] = (
            remaining_load
        )

        # ----------------------------------------------------
        # 7. Electricity cost
        # ----------------------------------------------------

        total_cost += (
            grid_used *
            current_price
        )

    # ========================================================
    # Battery report
    # ========================================================

    battery_status = battery.status()

    total_unserved = sum(
        hourly_unserved
    )

    print("\n" + "=" * 55)
    print(
        "BATTERY ENERGY STORAGE STATUS"
    )
    print("=" * 55)

    print(
        f"Battery capacity       : "
        f"{battery_status['capacity_kwh']:.2f} kWh"
    )

    print(
        f"Final battery SOC      : "
        f"{battery_status['soc_percent']:.2f}%"
    )

    print(
        f"Energy remaining       : "
        f"{battery_status['energy_kwh']:.2f} kWh"
    )

    print(
        f"Energy discharged      : "
        f"{sum(hourly_battery):.2f} kWh"
    )

    print(
        f"Energy charged         : "
        f"{sum(hourly_battery_charge):.2f} kWh"
    )

    print(
        f"Available discharge    : "
        f"{battery_status['available_discharge_kwh']:.2f} kWh"
    )

    print("=" * 55)

    return {
        "total_cost": total_cost,
        "grid_energy_kwh":
            sum(hourly_grid),
        "solar_energy_kwh":
            sum(hourly_solar),
        "battery_energy_kwh":
            sum(hourly_battery),
        "battery_charged_kwh":
            sum(hourly_battery_charge),
        "unserved_energy_kwh":
            total_unserved,
        "final_battery_soc_percent":
            battery_status["soc_percent"],
        "remaining_battery_energy_kwh":
            battery_status["energy_kwh"],
    }