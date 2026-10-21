import time

from poweros.telemetry.simulator import (
    TelemetrySimulator,
    print_telemetry_snapshot,
)

from poweros.telemetry.collector import (
    telemetry_to_data_center_state,
)


def main():
    simulator = TelemetrySimulator(gpu_count=20)

    print("=" * 60)
    print("ZYVARENTH POWEROS")
    print("LIVE TELEMETRY DEMO")
    print("=" * 60)

    for cycle in range(5):
        print(f"\n\nTELEMETRY CYCLE {cycle + 1}")

        snapshot = simulator.generate_snapshot()

        print_telemetry_snapshot(snapshot)

        state = telemetry_to_data_center_state(snapshot)

        print("\nPOWEROS STATE")
        print("-" * 60)

        print(f"GPUs: {state.total_gpu_count()}")
        print(
            f"GPU Power: "
            f"{state.total_gpu_power_kw():.2f} kW"
        )

        print(
            f"Facility Power: "
            f"{state.calculate_facility_power_kw():.2f} kW"
        )

        print(
            f"Average GPU Utilization: "
            f"{state.average_gpu_utilization():.2f}%"
        )

        if cycle < 4:
            time.sleep(2)

    print("\n")
    print("=" * 60)
    print("POWEROS TELEMETRY STREAM COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()