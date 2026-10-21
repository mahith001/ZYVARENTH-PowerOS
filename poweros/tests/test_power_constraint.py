from poweros.telemetry.simulator import (
    TelemetrySimulator,
)

from poweros.telemetry.collector import (
    telemetry_to_data_center_state,
)

from poweros.core.orchestrator import (
    run_poweros,
)


def main():

    simulator = TelemetrySimulator(
        gpu_count=20,
        start_hour=0,
    )

    # ---------------------------------------------------------
    # NORMAL CONDITION
    # ---------------------------------------------------------

    simulator.clear_power_constraint()

    normal_snapshot = (
        simulator.generate_snapshot()
    )

    normal_state = (
        telemetry_to_data_center_state(
            normal_snapshot
        )
    )

    normal_result = run_poweros(
        state=normal_state,
        horizon_hours=24,
    )

    normal_safe_limit = (
        normal_result[
            "safe_power_limit_kw"
        ]
    )

    # ---------------------------------------------------------
    # POWER CONSTRAINT
    # ---------------------------------------------------------

    simulator.apply_power_constraint(
        available_power_kw=8.0,
        grid_capacity_kw=10.0,
    )

    constrained_snapshot = (
        simulator.generate_snapshot()
    )

    constrained_state = (
        telemetry_to_data_center_state(
            constrained_snapshot
        )
    )

    constrained_result = run_poweros(
        state=constrained_state,
        horizon_hours=24,
    )

    constrained_safe_limit = (
        constrained_result[
            "safe_power_limit_kw"
        ]
    )

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    assert (
        normal_safe_limit
        > constrained_safe_limit
    )

    assert (
        constrained_safe_limit
        == 6.8
    )

    print(
        "NORMAL SAFE POWER LIMIT:",
        normal_safe_limit,
        "kW",
    )

    print(
        "CONSTRAINED SAFE POWER LIMIT:",
        constrained_safe_limit,
        "kW",
    )

    print(
        "POWEROS POWER CONSTRAINT TEST PASSED"
    )


if __name__ == "__main__":
    main()