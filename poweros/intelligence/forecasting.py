from typing import Dict, List

from poweros.core.models import DataCenterState


# =========================================================
# WORKLOAD DEMAND FORECAST
# =========================================================

def forecast_workload_demand(
    state: DataCenterState,
    horizon_hours: int = 24,
) -> List[Dict]:
    """
    Estimate workload demand across the forecast horizon.

    This V1 model distributes currently known workloads
    according to their deadlines.
    """

    forecast = []

    for hour in range(horizon_hours):

        active_gpu_demand = 0
        active_workloads = 0

        for workload in state.workloads:

            duration = int(
                workload.duration_hours
            )

            latest_start = max(
                0,
                workload.deadline_hour
                - duration,
            )

            # V1 planning assumption:
            # workload may need to execute
            # before its deadline.

            if (
                hour >= latest_start
                and hour < workload.deadline_hour
            ):

                active_gpu_demand += (
                    workload.gpu_required
                )

                active_workloads += 1

        forecast.append({
            "hour": hour,
            "gpu_demand": active_gpu_demand,
            "active_workloads": active_workloads,
        })

    return forecast


# =========================================================
# POWER DEMAND FORECAST
# =========================================================

def forecast_power_demand(
    state: DataCenterState,
    workload_forecast: List[Dict],
    gpu_power_kw: float = 0.7,
) -> List[Dict]:
    """
    Convert forecast GPU demand into estimated
    compute power demand.
    """

    forecast = []

    for item in workload_forecast:

        gpu_demand = item["gpu_demand"]

        power_demand = (
            gpu_demand
            * gpu_power_kw
        )

        forecast.append({
            "hour": item["hour"],
            "gpu_demand": gpu_demand,
            "active_workloads":
                item["active_workloads"],
            "power_demand_kw":
                round(
                    power_demand,
                    3,
                ),
        })

    return forecast


# =========================================================
# POWER PRESSURE FORECAST
# =========================================================

def calculate_forecast_pressure(
    power_forecast: List[Dict],
    available_power_kw: float,
) -> List[Dict]:
    """
    Estimate future power pressure.
    """

    results = []

    for item in power_forecast:

        demand = item[
            "power_demand_kw"
        ]

        if available_power_kw <= 0:

            pressure = 100.0

        else:

            pressure = (
                demand
                / available_power_kw
            ) * 100

        if pressure >= 100:

            risk = "CRITICAL"

        elif pressure >= 80:

            risk = "WARNING"

        else:

            risk = "NORMAL"

        results.append({
            **item,

            "power_pressure_percent":
                round(
                    pressure,
                    2,
                ),

            "risk":
                risk,
        })

    return results


# =========================================================
# FIND PEAK DEMAND
# =========================================================

def find_peak_forecast(
    forecast: List[Dict],
) -> Dict:
    """
    Find the hour with the highest forecast
    power demand.
    """

    if not forecast:

        return {
            "hour": None,
            "peak_power_kw": 0.0,
            "peak_gpu_demand": 0,
        }

    peak = max(
        forecast,
        key=lambda item:
            item["power_demand_kw"],
    )

    return {
        "hour":
            peak["hour"],

        "peak_power_kw":
            peak["power_demand_kw"],

        "peak_gpu_demand":
            peak["gpu_demand"],
    }


# =========================================================
# COMPLETE FORECAST
# =========================================================

def generate_forecast(
    state: DataCenterState,
    horizon_hours: int = 24,
    gpu_power_kw: float = 0.7,
) -> Dict:
    """
    Generate the complete PowerOS forecast.
    """

    workload_forecast = (
        forecast_workload_demand(
            state,
            horizon_hours,
        )
    )

    power_forecast = (
        forecast_power_demand(
            state,
            workload_forecast,
            gpu_power_kw,
        )
    )

    pressure_forecast = (
        calculate_forecast_pressure(
            power_forecast,
            state.power.available_power_kw
            if state.power
            else 0,
        )
    )

    peak = find_peak_forecast(
        pressure_forecast
    )

    critical_hours = sum(
        1
        for item in pressure_forecast
        if item["risk"] == "CRITICAL"
    )

    warning_hours = sum(
        1
        for item in pressure_forecast
        if item["risk"] == "WARNING"
    )

    return {
        "horizon_hours":
            horizon_hours,

        "hourly_forecast":
            pressure_forecast,

        "peak":
            peak,

        "critical_hours":
            critical_hours,

        "warning_hours":
            warning_hours,
    }


# =========================================================
# FORECAST REPORT
# =========================================================

def print_forecast_report(
    forecast: Dict,
):

    print()
    print("=" * 60)
    print("POWEROS FORECASTING ENGINE")
    print("=" * 60)

    print(
        f"Forecast horizon: "
        f"{forecast['horizon_hours']} hours"
    )

    peak = forecast["peak"]

    print(
        f"Peak forecast power: "
        f"{peak['peak_power_kw']} kW"
    )

    print(
        f"Peak GPU demand: "
        f"{peak['peak_gpu_demand']}"
    )

    print(
        f"Peak hour: "
        f"{peak['hour']}"
    )

    print(
        f"Critical hours: "
        f"{forecast['critical_hours']}"
    )

    print(
        f"Warning hours: "
        f"{forecast['warning_hours']}"
    )

    print()
    print("HOURLY FORECAST")

    for item in forecast[
        "hourly_forecast"
    ]:

        print(
            f"Hour {item['hour']:02d} | "
            f"GPUs: {item['gpu_demand']} | "
            f"Power: "
            f"{item['power_demand_kw']} kW | "
            f"Pressure: "
            f"{item['power_pressure_percent']}% | "
            f"{item['risk']}"
        )

    print("=" * 60)