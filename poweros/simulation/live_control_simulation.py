"""
ZYVARENTH PowerOS
Live Closed-Loop Control Simulation

Simulates PowerOS making repeated decisions over a 24-hour
operating period.
"""

from copy import deepcopy

from poweros.data.fair_baseline import (
    create_realistic_state,
    create_realistic_prices,
    create_realistic_solar,
)

from poweros.core.orchestrator import run_poweros


HORIZON_HOURS = 24
BATTERY_CAPACITY_KWH = 100.0
INITIAL_BATTERY_SOC = 80.0
BATTERY_MAX_DISCHARGE_KW = 10.0
RESERVE_PERCENT = 15.0


def calculate_battery_soc(
    initial_energy_kwh,
    battery_used_kwh,
    capacity_kwh,
):
    """
    Calculate battery state of charge.
    """

    remaining = max(
        0.0,
        initial_energy_kwh - battery_used_kwh,
    )

    return (
        remaining / capacity_kwh
    ) * 100.0


def get_battery_usage(dispatch):
    """
    Safely extract battery usage.
    """

    if not isinstance(dispatch, dict):
        return 0.0

    return float(
        dispatch.get(
            "battery_energy_used_kwh",
            dispatch.get(
                "battery_used_kwh",
                dispatch.get(
                    "battery_used",
                    0.0,
                ),
            ),
        )
    )


def get_solar_usage(dispatch):
    """
    Safely extract solar usage.
    """

    if not isinstance(dispatch, dict):
        return 0.0

    return float(
        dispatch.get(
            "solar_energy_used_kwh",
            dispatch.get(
                "solar_used_kwh",
                dispatch.get(
                    "solar_used",
                    0.0,
                ),
            ),
        )
    )


def get_cost(dispatch):
    """
    Safely extract total energy cost.
    """

    if not isinstance(dispatch, dict):
        return 0.0

    return float(
        dispatch.get(
            "total_cost",
            dispatch.get(
                "total_energy_cost",
                dispatch.get(
                    "cost",
                    0.0,
                ),
            ),
        )
    )


def get_peak_power(result):
    """
    Safely extract peak facility power.
    """

    summary = result.get(
        "power_summary",
        {},
    )

    if not isinstance(summary, dict):
        return 0.0

    return float(
        summary.get(
            "peak_facility_power_kw",
            summary.get(
                "peak_power_kw",
                0.0,
            ),
        )
    )


def get_decision_count(result, key):
    """
    Safely extract decision count.
    """

    summary = result.get(
        "decision_summary",
        {},
    )

    if not isinstance(summary, dict):
        return 0

    return int(
        summary.get(
            key,
            0,
        )
    )


def run_live_control():

    print()
    print("=" * 90)
    print("ZYVARENTH POWEROS")
    print("LIVE CLOSED-LOOP CONTROL SIMULATION")
    print("=" * 90)

    # --------------------------------------------------------
    # INITIAL STATE
    # --------------------------------------------------------

    state = create_realistic_state()

    prices = create_realistic_prices()

    solar = create_realistic_solar()

    battery_initial_energy = (
        BATTERY_CAPACITY_KWH
        * INITIAL_BATTERY_SOC
        / 100.0
    )

    total_cost = 0.0
    total_solar = 0.0
    total_battery = 0.0
    peak_power = 0.0

    total_shift = 0
    total_protection = 0

    history = []

    # --------------------------------------------------------
    # CONTROL LOOP
    # --------------------------------------------------------

    for hour in range(HORIZON_HOURS):

        print()
        print("-" * 90)
        print(f"CONTROL CYCLE — HOUR {hour}")
        print("-" * 90)

        # ----------------------------------------------------
        # Create current state
        # ----------------------------------------------------

        current_state = deepcopy(state)

        # ----------------------------------------------------
        # Run PowerOS
        # ----------------------------------------------------

        result = run_poweros(
            state=current_state,
            electricity_prices=prices,
            solar_power_by_hour=solar,
            battery_capacity_kwh=BATTERY_CAPACITY_KWH,
            initial_battery_soc_percent=INITIAL_BATTERY_SOC,
            battery_max_discharge_kw=BATTERY_MAX_DISCHARGE_KW,
            reserve_percent=RESERVE_PERCENT,
        )

        # ----------------------------------------------------
        # Extract metrics
        # ----------------------------------------------------

        dispatch = result.get(
            "battery_dispatch",
            {},
        )

        cost = get_cost(dispatch)

        solar_used = get_solar_usage(
            dispatch
        )

        battery_used = get_battery_usage(
            dispatch
        )

        cycle_peak = get_peak_power(
            result
        )

        shift_count = get_decision_count(
            result,
            "shift_decisions",
        )

        protection_count = get_decision_count(
            result,
            "protect_deadline_decisions",
        )

        # ----------------------------------------------------
        # Accumulate
        # ----------------------------------------------------

        total_cost += cost

        total_solar += solar_used

        total_battery += battery_used

        peak_power = max(
            peak_power,
            cycle_peak,
        )

        total_shift += shift_count

        total_protection += protection_count

        # ----------------------------------------------------
        # Battery SOC
        # ----------------------------------------------------

        battery_soc = calculate_battery_soc(
            battery_initial_energy,
            total_battery,
            BATTERY_CAPACITY_KWH,
        )

        # ----------------------------------------------------
        # State analysis
        # ----------------------------------------------------

        state_analysis = result.get(
            "state_analysis",
            {},
        )

        status = state_analysis.get(
            "status",
            "UNKNOWN",
        )

        bottleneck = state_analysis.get(
            "primary_bottleneck",
            "NONE",
        )

        # ----------------------------------------------------
        # Print cycle
        # ----------------------------------------------------

        print(
            f"PowerOS status:       {status}"
        )

        print(
            f"Primary bottleneck:   {bottleneck}"
        )

        print(
            f"Peak facility power:  "
            f"{cycle_peak:.2f} kW"
        )

        print(
            f"Electricity cost:     "
            f"₹{cost:.2f}"
        )

        print(
            f"Solar used:           "
            f"{solar_used:.2f} kWh"
        )

        print(
            f"Battery used:         "
            f"{battery_used:.2f} kWh"
        )

        print(
            f"Battery SOC:          "
            f"{battery_soc:.2f}%"
        )

        print(
            f"Shift decisions:      "
            f"{shift_count}"
        )

        print(
            f"Deadline protection:  "
            f"{protection_count}"
        )

        # ----------------------------------------------------
        # Store history
        # ----------------------------------------------------

        history.append(
            {
                "hour": hour,
                "status": status,
                "bottleneck": bottleneck,
                "peak_power_kw": cycle_peak,
                "cost": cost,
                "solar_used_kwh": solar_used,
                "battery_used_kwh": battery_used,
                "battery_soc_percent": battery_soc,
                "shift_decisions": shift_count,
                "deadline_protection": protection_count,
            }
        )

    # ========================================================
    # FINAL REPORT
    # ========================================================

    print()
    print("=" * 90)
    print("LIVE CONTROL LOOP FINAL REPORT")
    print("=" * 90)

    print()

    print(
        f"Control cycles:           "
        f"{len(history)}"
    )

    print(
        f"Peak facility power:      "
        f"{peak_power:.2f} kW"
    )

    print(
        f"Total energy cost:        "
        f"₹{total_cost:.2f}"
    )

    print(
        f"Total solar used:         "
        f"{total_solar:.2f} kWh"
    )

    print(
        f"Total battery used:       "
        f"{total_battery:.2f} kWh"
    )

    print(
        f"Final battery SOC:        "
        f"{calculate_battery_soc(
            battery_initial_energy,
            total_battery,
            BATTERY_CAPACITY_KWH,
        ):.2f}%"
    )

    print(
        f"Total SHIFT decisions:    "
        f"{total_shift}"
    )

    print(
        f"Total deadline protection:"
        f" {total_protection}"
    )

    print()
    print("=" * 90)
    print("POWEROS LIVE CONTROL SIMULATION COMPLETED")
    print("=" * 90)
    print()

    return history


def main():

    run_live_control()


if __name__ == "__main__":
    main()