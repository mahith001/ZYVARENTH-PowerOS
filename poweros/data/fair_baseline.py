from math import ceil

from poweros.core.models import (
    GPU,
    Workload,
    PowerState,
    EnergyResource,
    DataCenterState,
)


# ============================================================
# CONSTANTS
# ============================================================

GPU_POWER_KW = 0.70


# ============================================================
# REALISTIC WORKLOAD DATA
# ============================================================

def create_realistic_workloads():
    """Create the 14-workload realistic validation dataset."""

    return [
        Workload(
            workload_id="LLM-TRAIN-001",
            gpu_required=8,
            duration_hours=6,
            deadline_hour=12,
            priority="HIGH",
        ),

        Workload(
            workload_id="LLM-TRAIN-002",
            gpu_required=16,
            duration_hours=8,
            deadline_hour=18,
            priority="HIGH",
        ),

        Workload(
            workload_id="LLM-FINETUNE-001",
            gpu_required=4,
            duration_hours=4,
            deadline_hour=14,
            priority="HIGH",
        ),

        Workload(
            workload_id="LLM-FINETUNE-002",
            gpu_required=4,
            duration_hours=3,
            deadline_hour=20,
            priority="MEDIUM",
        ),

        Workload(
            workload_id="LLM-INFER-001",
            gpu_required=2,
            duration_hours=2,
            deadline_hour=10,
            priority="HIGH",
        ),

        Workload(
            workload_id="LLM-INFER-002",
            gpu_required=2,
            duration_hours=4,
            deadline_hour=22,
            priority="MEDIUM",
        ),

        Workload(
            workload_id="IMG-GEN-001",
            gpu_required=4,
            duration_hours=3,
            deadline_hour=16,
            priority="MEDIUM",
        ),

        Workload(
            workload_id="IMG-GEN-002",
            gpu_required=8,
            duration_hours=4,
            deadline_hour=21,
            priority="MEDIUM",
        ),

        Workload(
            workload_id="CV-TRAIN-001",
            gpu_required=4,
            duration_hours=5,
            deadline_hour=17,
            priority="MEDIUM",
        ),

        Workload(
            workload_id="CV-TRAIN-002",
            gpu_required=2,
            duration_hours=3,
            deadline_hour=23,
            priority="LOW",
        ),

        Workload(
            workload_id="BATCH-001",
            gpu_required=4,
            duration_hours=4,
            deadline_hour=23,
            priority="LOW",
        ),

        Workload(
            workload_id="BATCH-002",
            gpu_required=2,
            duration_hours=2,
            deadline_hour=24,
            priority="LOW",
        ),

        Workload(
            workload_id="EMBED-001",
            gpu_required=2,
            duration_hours=2,
            deadline_hour=15,
            priority="MEDIUM",
        ),

        Workload(
            workload_id="RESEARCH-001",
            gpu_required=8,
            duration_hours=5,
            deadline_hour=24,
            priority="LOW",
        ),
    ]


# ============================================================
# REALISTIC DATA CENTER
# ============================================================

def create_realistic_state():
    """Create the same 32-GPU state used by realistic validation."""

    gpus = []

    for i in range(1, 33):

        gpus.append(
            GPU(
                gpu_id=f"GPU-{i:03d}",
                utilization_percent=55,
                power_kw=0.70,
                temperature_c=65,
                memory_utilization_percent=60,
                available=True,
            )
        )

    workloads = create_realistic_workloads()

    power = PowerState(
        available_power_kw=40,
        grid_capacity_kw=50,
        electricity_price_per_kwh=8.50,
        solar_power_kw=10,
        battery_available_kw=10,
    )

    energy_resources = [
        EnergyResource(
            name="GRID",
            available_power_kw=50,
            cost_per_kwh=8.50,
            renewable=False,
        ),

        EnergyResource(
            name="SOLAR",
            available_power_kw=10,
            cost_per_kwh=0.0,
            renewable=True,
        ),

        EnergyResource(
            name="BATTERY",
            available_power_kw=10,
            cost_per_kwh=6.0,
            renewable=False,
        ),
    ]

    return DataCenterState(
        timestamp="2026-09-20T15:00:00",
        gpus=gpus,
        workloads=workloads,
        power=power,
        energy_resources=energy_resources,
        pue=1.30,
    )


# ============================================================
# REALISTIC HOURLY PRICES
# ============================================================

def create_realistic_prices():

    return [
        9.5,
        9.2,
        9.0,
        8.8,
        8.0,
        7.5,
        7.0,
        6.5,
        6.0,
        5.8,
        5.5,
        5.8,
        6.2,
        6.8,
        7.5,
        8.5,
        9.5,
        10.5,
        11.0,
        10.5,
        10.0,
        9.8,
        9.6,
        9.5,
    ]


# ============================================================
# REALISTIC SOLAR
# ============================================================

def create_realistic_solar():

    return [
        0,
        0,
        0,
        0,
        1,
        3,
        5,
        8,
        12,
        16,
        20,
        24,
        27,
        25,
        22,
        18,
        13,
        8,
        4,
        1,
        0,
        0,
        0,
        0,
    ]


# ============================================================
# WORKLOAD POWER
# ============================================================

def workload_power_kw(workload):
    """IT power required by a workload."""

    return (
        workload.gpu_required
        * GPU_POWER_KW
    )


def workload_facility_power_kw(
    workload,
    pue,
):
    """Facility power including PUE."""

    return (
        workload_power_kw(workload)
        * pue
    )


# ============================================================
# FEASIBILITY CHECK
# ============================================================

def can_place_workload(
    workload,
    start_hour,
    gpu_usage,
    power_usage,
    total_gpus,
    available_power_kw,
    pue,
):
    """
    Check whether a workload can run
    at the proposed start time.
    """

    duration_hours = ceil(
        workload.duration_hours
    )

    required_gpus = workload.gpu_required

    required_power = workload_facility_power_kw(
        workload,
        pue,
    )

    finish_hour = (
        start_hour
        + duration_hours
    )

    # --------------------------------------------------------
    # DEADLINE
    # --------------------------------------------------------

    if finish_hour > workload.deadline_hour:
        return False

    # --------------------------------------------------------
    # HOURLY RESOURCE CHECK
    # --------------------------------------------------------

    for hour in range(
        start_hour,
        finish_hour,
    ):

        if hour >= len(gpu_usage):
            return False

        if (
            gpu_usage[hour]
            + required_gpus
            > total_gpus
        ):
            return False

        if (
            power_usage[hour]
            + required_power
            > available_power_kw
        ):
            return False

    return True


# ============================================================
# BASELINE 2 SCHEDULER
# ============================================================

def schedule_earliest_start(
    state,
    horizon_hours=24,
):
    """
    Fair baseline scheduler.

    Rules:

    1. Process workloads in their existing order.
    2. Start each workload as early as possible.
    3. Respect GPU capacity.
    4. Respect facility power capacity.
    5. Respect deadlines.
    6. Do NOT optimize electricity prices.
    7. Do NOT use solar-aware scheduling.
    8. Do NOT use battery-aware scheduling.
    9. Do NOT use PowerOS intelligence.
    """

    workloads = state.workloads

    total_gpus = state.total_gpu_count()

    available_power_kw = (
        state.power.available_power_kw
    )

    pue = state.pue

    gpu_usage = [
        0.0
        for _ in range(horizon_hours)
    ]

    power_usage = [
        0.0
        for _ in range(horizon_hours)
    ]

    scheduled = []

    unscheduled = []

    # ========================================================
    # PROCESS EACH WORKLOAD
    # ========================================================

    for workload in workloads:

        scheduled_this_workload = False

        duration_hours = ceil(
            workload.duration_hours
        )

        latest_start = max(
            0,
            workload.deadline_hour
            - duration_hours,
        )

        # ----------------------------------------------------
        # TRY EVERY POSSIBLE START TIME
        # ----------------------------------------------------

        for start_hour in range(
            0,
            min(
                latest_start + 1,
                horizon_hours,
            ),
        ):

            feasible = can_place_workload(
                workload=workload,
                start_hour=start_hour,
                gpu_usage=gpu_usage,
                power_usage=power_usage,
                total_gpus=total_gpus,
                available_power_kw=available_power_kw,
                pue=pue,
            )

            if not feasible:
                continue

            required_power = (
                workload_facility_power_kw(
                    workload,
                    pue,
                )
            )

            # ------------------------------------------------
            # RESERVE RESOURCES
            # ------------------------------------------------

            for hour in range(
                start_hour,
                start_hour + duration_hours,
            ):

                gpu_usage[hour] += (
                    workload.gpu_required
                )

                power_usage[hour] += (
                    required_power
                )

            # ------------------------------------------------
            # SAVE SCHEDULE
            # ------------------------------------------------

            scheduled.append(
                {
                    "workload_id":
                        workload.workload_id,

                    "start_hour":
                        start_hour,

                    "duration_hours":
                        duration_hours,

                    "finish_hour":
                        start_hour
                        + duration_hours,

                    "gpu_required":
                        workload.gpu_required,

                    "facility_power_kw":
                        required_power,

                    "deadline_hour":
                        workload.deadline_hour,

                    "priority":
                        workload.priority,
                }
            )

            scheduled_this_workload = True

            break

        # ----------------------------------------------------
        # UNSCHEDULED
        # ----------------------------------------------------

        if not scheduled_this_workload:

            unscheduled.append(
                {
                    "workload_id":
                        workload.workload_id,

                    "gpu_required":
                        workload.gpu_required,

                    "duration_hours":
                        duration_hours,

                    "deadline_hour":
                        workload.deadline_hour,

                    "priority":
                        workload.priority,
                }
            )

    return {
        "scheduled": scheduled,
        "unscheduled": unscheduled,
        "hourly_gpu_usage": gpu_usage,
        "hourly_power_usage": power_usage,
    }


# ============================================================
# BASELINE METRICS
# ============================================================

def calculate_baseline_metrics(
    state,
    schedule,
    electricity_prices,
):
    """Calculate Baseline 2 metrics."""

    power_demand = (
        schedule["hourly_power_usage"]
    )

    # --------------------------------------------------------
    # ENERGY
    # --------------------------------------------------------

    total_energy_kwh = sum(
        power_demand
    )

    # --------------------------------------------------------
    # PEAK
    # --------------------------------------------------------

    peak_power_kw = max(
        power_demand,
        default=0.0,
    )

    # --------------------------------------------------------
    # WORKLOADS
    # --------------------------------------------------------

    scheduled = schedule["scheduled"]

    total_workloads = len(
        state.workloads
    )

    scheduled_count = len(
        scheduled
    )

    unscheduled_count = (
        total_workloads
        - scheduled_count
    )

    # --------------------------------------------------------
    # DEADLINES
    # --------------------------------------------------------

    deadline_met = 0

    for item in scheduled:

        if (
            item["finish_hour"]
            <= item["deadline_hour"]
        ):
            deadline_met += 1

    deadline_success_percent = (
        deadline_met
        / total_workloads
        * 100
        if total_workloads > 0
        else 0.0
    )

    # --------------------------------------------------------
    # ELECTRICITY COST
    # --------------------------------------------------------

    total_cost = 0.0

    for hour, power_kw in enumerate(
        power_demand
    ):

        if not electricity_prices:
            price = 0.0

        elif hour < len(
            electricity_prices
        ):
            price = electricity_prices[hour]

        else:
            price = electricity_prices[-1]

        total_cost += (
            power_kw
            * price
        )

    return {
        "total_workloads":
            total_workloads,

        "scheduled_count":
            scheduled_count,

        "unscheduled_count":
            unscheduled_count,

        "total_energy_kwh":
            total_energy_kwh,

        "peak_power_kw":
            peak_power_kw,

        "deadline_success_percent":
            deadline_success_percent,

        "estimated_cost":
            total_cost,

        # Baseline 2 deliberately does not
        # dispatch solar or battery.
        "solar_used_kwh":
            0.0,

        "battery_used_kwh":
            0.0,
    }


# ============================================================
# REPORT
# ============================================================

def print_baseline_report(
    schedule,
    metrics,
):

    print()

    print("=" * 70)

    print(
        "ZYVARENTH POWEROS"
    )

    print(
        "BASELINE 2"
    )

    print(
        "POWER-CONSTRAINED EARLIEST-START SCHEDULER"
    )

    print("=" * 70)

    print()

    print("WORKLOADS")

    print(
        f"Total workloads: "
        f"{metrics['total_workloads']}"
    )

    print(
        f"Scheduled: "
        f"{metrics['scheduled_count']}"
    )

    print(
        f"Unscheduled: "
        f"{metrics['unscheduled_count']}"
    )

    print()

    print("POWER")

    print(
        f"Peak facility power: "
        f"{metrics['peak_power_kw']:.2f} kW"
    )

    print(
        f"Total facility energy: "
        f"{metrics['total_energy_kwh']:.2f} kWh"
    )

    print()

    print("COST")

    print(
        f"Estimated electricity cost: "
        f"₹{metrics['estimated_cost']:.2f}"
    )

    print()

    print("DEADLINES")

    print(
        f"Deadline success: "
        f"{metrics['deadline_success_percent']:.2f}%"
    )

    print()

    print("ENERGY RESOURCES")

    print(
        f"Solar used: "
        f"{metrics['solar_used_kwh']:.2f} kWh"
    )

    print(
        f"Battery used: "
        f"{metrics['battery_used_kwh']:.2f} kWh"
    )

    print()

    print("SCHEDULE")

    print("-" * 70)

    for item in schedule["scheduled"]:

        print(
            f"{item['workload_id']:20} "
            f"START={item['start_hour']:2} "
            f"FINISH={item['finish_hour']:2} "
            f"GPU={item['gpu_required']:2} "
            f"POWER={item['facility_power_kw']:.2f} kW"
        )

    if schedule["unscheduled"]:

        print()

        print("UNSCHEDULED")

        for item in schedule["unscheduled"]:

            print(
                f"{item['workload_id']:20} "
                f"GPU={item['gpu_required']:2} "
                f"DEADLINE={item['deadline_hour']:2}"
            )

    print()

    print("=" * 70)


# ============================================================
# MAIN RUNNER
# ============================================================

def run_fair_baseline():

    state = create_realistic_state()

    prices = create_realistic_prices()

    solar = create_realistic_solar()

    # Solar is created so the dataset is identical
    # to the realistic validation environment.
    # Baseline 2 intentionally does not dispatch it.

    schedule = schedule_earliest_start(
        state=state,
        horizon_hours=24,
    )

    metrics = calculate_baseline_metrics(
        state=state,
        schedule=schedule,
        electricity_prices=prices,
    )

    print_baseline_report(
        schedule=schedule,
        metrics=metrics,
    )

    return {
        "state":
            state,

        "prices":
            prices,

        "solar":
            solar,

        "schedule":
            schedule,

        "metrics":
            metrics,
    }


# ============================================================
# ENTRY POINT
# ============================================================

def main():

    result = run_fair_baseline()

    print()

    print(
        "POWEROS FAIR BASELINE COMPLETED"
    )

    return result


if __name__ == "__main__":
    main()