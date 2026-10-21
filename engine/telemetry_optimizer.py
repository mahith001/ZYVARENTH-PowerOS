import pandas as pd


def calculate_gpu_efficiency(telemetry: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate useful GPU work relative to GPU power consumption.
    """

    result = telemetry.copy()

    result["efficiency_score"] = (
        result["gpu_utilization_percent"]
        / result["gpu_power_kw"].replace(0, 0.001)
    )

    return result


def identify_idle_gpus(
    telemetry: pd.DataFrame,
    utilization_threshold: float = 20.0,
) -> pd.DataFrame:
    """
    Identify GPUs with very low utilization.
    """

    idle = telemetry[
        telemetry["gpu_utilization_percent"]
        < utilization_threshold
    ].copy()

    return idle


def identify_high_power_gpus(
    telemetry: pd.DataFrame,
    power_threshold_kw: float = 0.60,
) -> pd.DataFrame:
    """
    Identify GPUs consuming unusually high power.
    """

    high_power = telemetry[
        telemetry["gpu_power_kw"]
        > power_threshold_kw
    ].copy()

    return high_power


def create_telemetry_insights(
    telemetry: pd.DataFrame,
) -> dict:
    """
    Convert GPU telemetry into optimization signals.
    """

    idle_gpus = identify_idle_gpus(telemetry)

    high_power_gpus = identify_high_power_gpus(telemetry)

    average_utilization = (
        telemetry["gpu_utilization_percent"].mean()
    )

    average_power = telemetry["gpu_power_kw"].mean()

    return {
        "total_gpu_records": len(telemetry),

        "idle_gpu_records": len(idle_gpus),

        "high_power_gpu_records": len(high_power_gpus),

        "average_utilization_percent":
            round(average_utilization, 2),

        "average_power_kw":
            round(average_power, 3),

        "idle_gpu_percent":
            round(
                (len(idle_gpus) / len(telemetry)) * 100,
                2,
            ),
    }


def print_telemetry_insights(insights: dict):

    print("\n" + "=" * 60)
    print("POWEROS TELEMETRY OPTIMIZATION INSIGHTS")
    print("=" * 60)

    print(
        f"Average GPU utilization: "
        f"{insights['average_utilization_percent']}%"
    )

    print(
        f"Average GPU power: "
        f"{insights['average_power_kw']} kW"
    )

    print(
        f"Low-utilization GPU records: "
        f"{insights['idle_gpu_records']}"
    )

    print(
        f"Low-utilization percentage: "
        f"{insights['idle_gpu_percent']}%"
    )

    print(
        f"High-power GPU records: "
        f"{insights['high_power_gpu_records']}"
    )

    print("=" * 60)