from poweros.core.models import (
    GPU,
    DataCenterState,
)


def main():

    gpus = [

        GPU(
            gpu_id="GPU-001",
            utilization_percent=70,
            power_kw=10,
            temperature_c=65,
            memory_utilization_percent=60,
        ),

        GPU(
            gpu_id="GPU-002",
            utilization_percent=70,
            power_kw=10,
            temperature_c=65,
            memory_utilization_percent=60,
        ),
    ]

    state = DataCenterState(
        timestamp="2026-09-20T15:00:00",
        gpus=gpus,
        pue=1.3,
    )

    it_power = (
        state.calculate_it_power_kw()
    )

    facility_power = (
        state.calculate_facility_power_kw()
    )

    overhead_power = (
        state.calculate_overhead_power_kw()
    )

    assert it_power == 20

    assert facility_power == 26

    assert overhead_power == 6

    print(
        "POWEROS PUE TEST PASSED"
    )


if __name__ == "__main__":

    main()