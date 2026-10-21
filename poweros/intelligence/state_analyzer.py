from typing import Dict

from poweros.core.models import DataCenterState


# =========================================================
# POWER PRESSURE
# =========================================================

def calculate_power_pressure(
    state: DataCenterState,
) -> float:
    """
    Calculate how much of the available power
    is currently being consumed.

    0%   = no power pressure
    100% = all available power being used
    """

    if not state.power:
        return 0.0

    available_power = state.power.available_power_kw

    if available_power <= 0:
        return 100.0

    current_power = state.total_gpu_power_kw()

    pressure = (
        current_power / available_power
    ) * 100

    return round(
        min(100.0, pressure),
        2,
    )


# =========================================================
# POWER HEADROOM
# =========================================================

def calculate_power_headroom(
    state: DataCenterState,
) -> float:
    """
    Calculate remaining available power.
    """

    if not state.power:
        return 0.0

    current_power = state.total_gpu_power_kw()

    headroom = (
        state.power.available_power_kw
        - current_power
    )

    return round(
        max(0.0, headroom),
        3,
    )


# =========================================================
# GPU UTILIZATION
# =========================================================

def analyze_gpu_utilization(
    state: DataCenterState,
) -> Dict:
    """
    Analyze GPU fleet utilization.
    """

    if not state.gpus:

        return {
            "average_utilization_percent": 0.0,
            "idle_gpu_count": 0,
            "high_utilization_gpu_count": 0,
        }

    idle_gpu_count = sum(
        1
        for gpu in state.gpus
        if gpu.utilization_percent < 20
    )

    high_utilization_gpu_count = sum(
        1
        for gpu in state.gpus
        if gpu.utilization_percent >= 80
    )

    return {
        "average_utilization_percent":
            round(
                state.average_gpu_utilization(),
                2,
            ),

        "idle_gpu_count":
            idle_gpu_count,

        "high_utilization_gpu_count":
            high_utilization_gpu_count,
    }


# =========================================================
# THERMAL ANALYSIS
# =========================================================

def analyze_thermal_pressure(
    state: DataCenterState,
) -> Dict:
    """
    Identify GPUs experiencing high temperatures.

    This is an initial software threshold.
    Real deployments will use hardware-specific limits.
    """

    warning_temperature = 80.0
    critical_temperature = 90.0

    warning_count = sum(
        1
        for gpu in state.gpus
        if gpu.temperature_c >= warning_temperature
    )

    critical_count = sum(
        1
        for gpu in state.gpus
        if gpu.temperature_c >= critical_temperature
    )

    return {
        "warning_temperature_c":
            warning_temperature,

        "critical_temperature_c":
            critical_temperature,

        "warning_gpu_count":
            warning_count,

        "critical_gpu_count":
            critical_count,
    }


# =========================================================
# WORKLOAD URGENCY
# =========================================================

def analyze_workload_urgency(
    state: DataCenterState,
) -> Dict:
    """
    Identify workloads that are approaching
    their deadlines.

    Current time is represented by hour 0.
    """

    urgent_count = 0
    high_priority_count = 0

    for workload in state.workloads:

        if workload.priority == "HIGH":
            high_priority_count += 1

        if workload.deadline_hour <= 6:
            urgent_count += 1

    return {
        "total_workloads":
            len(state.workloads),

        "high_priority_workloads":
            high_priority_count,

        "urgent_workloads":
            urgent_count,
    }


# =========================================================
# ENERGY OPPORTUNITIES
# =========================================================

def analyze_energy_opportunities(
    state: DataCenterState,
) -> Dict:
    """
    Identify available renewable and battery resources.
    """

    solar_power = 0.0
    battery_power = 0.0

    if state.power:

        solar_power = (
            state.power.solar_power_kw
        )

        battery_power = (
            state.power.battery_available_kw
        )

    return {
        "solar_available_kw":
            round(solar_power, 2),

        "battery_available_kw":
            round(battery_power, 2),

        "solar_available":
            solar_power > 0,

        "battery_available":
            battery_power > 0,
    }


# =========================================================
# COMPLETE STATE ANALYSIS
# =========================================================

def analyze_state(
    state: DataCenterState,
) -> Dict:
    """
    Produce a complete PowerOS analysis
    of the current data-center state.
    """

    gpu_analysis = analyze_gpu_utilization(
        state
    )

    thermal_analysis = analyze_thermal_pressure(
        state
    )

    workload_analysis = analyze_workload_urgency(
        state
    )

    energy_analysis = analyze_energy_opportunities(
        state
    )

    power_pressure = calculate_power_pressure(
        state
    )

    power_headroom = calculate_power_headroom(
        state
    )

    # -----------------------------------------------------
    # Determine the primary bottleneck
    # -----------------------------------------------------

    if thermal_analysis["critical_gpu_count"] > 0:

        bottleneck = "THERMAL"

    elif power_pressure >= 90:

        bottleneck = "POWER"

    elif gpu_analysis["idle_gpu_count"] > 0:

        bottleneck = "GPU_UTILIZATION"

    elif workload_analysis["urgent_workloads"] > 0:

        bottleneck = "WORKLOAD_DEADLINE"

    else:

        bottleneck = "NONE"

    # -----------------------------------------------------
    # Determine overall status
    # -----------------------------------------------------

    if (
        thermal_analysis["critical_gpu_count"] > 0
        or power_pressure >= 95
    ):

        status = "CRITICAL"

    elif (
        thermal_analysis["warning_gpu_count"] > 0
        or power_pressure >= 80
        or workload_analysis["urgent_workloads"] > 0
    ):

        status = "WARNING"

    else:

        status = "HEALTHY"

    return {
        "status": status,

        "primary_bottleneck":
            bottleneck,

        "power_pressure_percent":
            power_pressure,

        "power_headroom_kw":
            power_headroom,

        "gpu_analysis":
            gpu_analysis,

        "thermal_analysis":
            thermal_analysis,

        "workload_analysis":
            workload_analysis,

        "energy_analysis":
            energy_analysis,
    }


# =========================================================
# REPORT
# =========================================================

def print_state_analysis(
    analysis: Dict,
):

    print()
    print("=" * 60)
    print("POWEROS STATE INTELLIGENCE")
    print("=" * 60)

    print(
        f"Overall status: "
        f"{analysis['status']}"
    )

    print(
        f"Primary bottleneck: "
        f"{analysis['primary_bottleneck']}"
    )

    print(
        f"Power pressure: "
        f"{analysis['power_pressure_percent']}%"
    )

    print(
        f"Power headroom: "
        f"{analysis['power_headroom_kw']} kW"
    )

    gpu = analysis["gpu_analysis"]

    print()
    print("GPU STATE")

    print(
        f"Average utilization: "
        f"{gpu['average_utilization_percent']}%"
    )

    print(
        f"Idle GPUs: "
        f"{gpu['idle_gpu_count']}"
    )

    print(
        f"High-utilization GPUs: "
        f"{gpu['high_utilization_gpu_count']}"
    )

    thermal = analysis["thermal_analysis"]

    print()
    print("THERMAL STATE")

    print(
        f"Warning GPUs: "
        f"{thermal['warning_gpu_count']}"
    )

    print(
        f"Critical GPUs: "
        f"{thermal['critical_gpu_count']}"
    )

    workloads = analysis["workload_analysis"]

    print()
    print("WORKLOAD STATE")

    print(
        f"Total workloads: "
        f"{workloads['total_workloads']}"
    )

    print(
        f"High-priority workloads: "
        f"{workloads['high_priority_workloads']}"
    )

    print(
        f"Urgent workloads: "
        f"{workloads['urgent_workloads']}"
    )

    energy = analysis["energy_analysis"]

    print()
    print("ENERGY STATE")

    print(
        f"Solar available: "
        f"{energy['solar_available_kw']} kW"
    )

    print(
        f"Battery available: "
        f"{energy['battery_available_kw']} kW"
    )

    print("=" * 60)