from poweros.telemetry.simulator import (
    TelemetrySimulator,
)

from poweros.telemetry.collector import (
    telemetry_to_data_center_state,
)


def main():

    simulator = TelemetrySimulator(
        gpu_count=10,
        start_hour=0,
    )

    # ---------------------------------------------------------
    # FIRST SNAPSHOT
    # ---------------------------------------------------------

    snapshot_1 = (
        simulator.generate_snapshot()
    )

    assert len(snapshot_1.gpus) == 10

    assert len(snapshot_1.workloads) == 4

    assert (
        snapshot_1.battery.soc_percent
        == 80.0
    )

    # ---------------------------------------------------------
    # SECOND SNAPSHOT
    # ---------------------------------------------------------

    snapshot_2 = (
        simulator.generate_snapshot()
    )

    assert len(snapshot_2.gpus) == 10

    # Simulation clock should move
    assert (
        snapshot_1.timestamp
        != snapshot_2.timestamp
    )

    # ---------------------------------------------------------
    # CONVERT TO POWEROS STATE
    # ---------------------------------------------------------

    state = (
        telemetry_to_data_center_state(
            snapshot_2
        )
    )

    assert (
        state.total_gpu_count()
        == 10
    )

    assert (
        len(state.workloads)
        == 4
    )

    assert (
        state.power.available_power_kw
        > 0
    )

    assert state.pue == 1.3

    print(
        "POWEROS TELEMETRY TEST PASSED"
    )


if __name__ == "__main__":
    main()