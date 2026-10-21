import random
import pandas as pd


def generate_gpu_telemetry(
    num_gpus: int = 100,
    hours: int = 24,
) -> pd.DataFrame:

    records = []

    for hour in range(hours):

        for gpu_id in range(num_gpus):

            utilization = random.uniform(20, 95)

            temperature = (
                45
                + (utilization * 0.35)
                + random.uniform(-3, 3)
            )

            power_kw = 0.7 * (utilization / 100)

            memory_utilization = random.uniform(20, 90)

            records.append({
                "hour": hour,
                "gpu_id": gpu_id,
                "gpu_utilization_percent": round(
                    utilization, 2
                ),
                "gpu_temperature_c": round(
                    temperature, 2
                ),
                "gpu_power_kw": round(
                    power_kw, 3
                ),
                "gpu_memory_utilization_percent": round(
                    memory_utilization, 2
                ),
            })

    return pd.DataFrame(records)


def calculate_telemetry_summary(
    telemetry: pd.DataFrame,
) -> dict:

    return {
        "average_gpu_utilization_percent":
            round(
                telemetry[
                    "gpu_utilization_percent"
                ].mean(),
                2,
            ),

        "peak_gpu_utilization_percent":
            round(
                telemetry[
                    "gpu_utilization_percent"
                ].max(),
                2,
            ),

        "average_gpu_temperature_c":
            round(
                telemetry[
                    "gpu_temperature_c"
                ].mean(),
                2,
            ),

        "peak_gpu_temperature_c":
            round(
                telemetry[
                    "gpu_temperature_c"
                ].max(),
                2,
            ),

        "average_gpu_power_kw":
            round(
                telemetry[
                    "gpu_power_kw"
                ].mean(),
                3,
            ),

        "peak_gpu_power_kw":
            round(
                telemetry[
                    "gpu_power_kw"
                ].max(),
                3,
            ),

        "average_gpu_memory_utilization_percent":
            round(
                telemetry[
                    "gpu_memory_utilization_percent"
                ].mean(),
                2,
            ),
    }


def print_telemetry_report(
    telemetry: pd.DataFrame,
    summary: dict,
):

    print("\n" + "=" * 60)
    print("POWEROS GPU TELEMETRY")
    print("=" * 60)

    print(
        f"GPUs monitored: "
        f"{telemetry['gpu_id'].nunique()}"
    )

    print(
        f"Average GPU utilization: "
        f"{summary['average_gpu_utilization_percent']}%"
    )

    print(
        f"Peak GPU utilization: "
        f"{summary['peak_gpu_utilization_percent']}%"
    )

    print(
        f"Average GPU temperature: "
        f"{summary['average_gpu_temperature_c']} °C"
    )

    print(
        f"Peak GPU temperature: "
        f"{summary['peak_gpu_temperature_c']} °C"
    )

    print(
        f"Average GPU power: "
        f"{summary['average_gpu_power_kw']} kW"
    )

    print(
        f"Peak GPU power: "
        f"{summary['peak_gpu_power_kw']} kW"
    )

    print(
        f"Average memory utilization: "
        f"{summary['average_gpu_memory_utilization_percent']}%"
    )

    print("=" * 60)