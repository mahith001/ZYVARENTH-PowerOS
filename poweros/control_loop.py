# =============================================================
# ZYVARENTH POWEROS
# CONTINUOUS CONTROL LOOP
# =============================================================

from datetime import datetime

from poweros.core.orchestrator import (
    run_poweros,
    create_executive_summary,
)

from poweros.simulation.workload_lifecycle import (
    run_lifecycle_simulation,
    summarize_lifecycle,
)


# =============================================================
# CONTROL LOOP
# =============================================================

class PowerOSControlLoop:

    def __init__(
        self,
        state,
        electricity_prices=None,
        solar_power_by_hour=None,
        battery_capacity_kwh=100.0,
        initial_battery_soc_percent=80.0,
        battery_max_discharge_kw=10.0,
        reserve_percent=15.0,
    ):

        self.state = state

        self.electricity_prices = (
            electricity_prices
        )

        self.solar_power_by_hour = (
            solar_power_by_hour
        )

        self.battery_capacity_kwh = (
            battery_capacity_kwh
        )

        self.initial_battery_soc_percent = (
            initial_battery_soc_percent
        )

        self.battery_max_discharge_kw = (
            battery_max_discharge_kw
        )

        self.reserve_percent = (
            reserve_percent
        )

        self.cycle_number = 0

        self.history = []

        self.lifecycle_result = None

    # =========================================================
    # RUN ONE CYCLE
    # =========================================================

    def run_cycle(
        self,
        current_hour=0,
        horizon_hours=24,
        power_constraint_hours=None,
    ):
        """
        Run one complete PowerOS control cycle.
        """

        self.cycle_number += 1

        # -----------------------------------------------------
        # OBSERVE → ANALYZE → PREDICT → OPTIMIZE → DECIDE
        # -----------------------------------------------------

        result = run_poweros(
            state=self.state,
            horizon_hours=horizon_hours,
            electricity_prices=(
                self.electricity_prices
            ),
            solar_power_by_hour=(
                self.solar_power_by_hour
            ),
            battery_capacity_kwh=(
                self.battery_capacity_kwh
            ),
            initial_battery_soc_percent=(
                self.initial_battery_soc_percent
            ),
            battery_max_discharge_kw=(
                self.battery_max_discharge_kw
            ),
            reserve_percent=(
                self.reserve_percent
            ),
        )

        # -----------------------------------------------------
        # WORKLOAD LIFECYCLE
        # -----------------------------------------------------

        lifecycle_result = (
            run_lifecycle_simulation(
                workloads=[
                    self.workload_to_dict(
                        workload
                    )
                    for workload
                    in self.state.workloads
                ],
                schedule=result.get(
                    "schedule",
                    {},
                ),
                admission_results=result.get(
                    "admission_results",
                    [],
                ),
                start_hour=current_hour,
                horizon_hours=horizon_hours,
                power_constraint_hours=(
                    power_constraint_hours
                ),
            )
        )

        lifecycle_summary = (
            summarize_lifecycle(
                lifecycle_result
            )
        )

        self.lifecycle_result = (
            lifecycle_result
        )

        # -----------------------------------------------------
        # EXECUTIVE SUMMARY
        # -----------------------------------------------------

        executive_summary = (
            create_executive_summary(
                result
            )
        )

        # Add lifecycle metrics
        executive_summary[
            "lifecycle"
        ] = lifecycle_summary

        # -----------------------------------------------------
        # RECORD HISTORY
        # -----------------------------------------------------

        cycle_record = {
            "cycle": self.cycle_number,

            "timestamp":
                datetime.now().isoformat(),

            "current_hour":
                current_hour,

            "poweros_result":
                result,

            "executive_summary":
                executive_summary,

            "lifecycle_result":
                lifecycle_result,

            "lifecycle_summary":
                lifecycle_summary,
        }

        self.history.append(
            cycle_record
        )

        return cycle_record

    # =========================================================
    # RUN MULTIPLE CYCLES
    # =========================================================

    def run(
        self,
        cycles=3,
        start_hour=0,
        horizon_hours=24,
    ):
        """
        Run multiple PowerOS control cycles.
        """

        results = []

        for cycle in range(
            cycles
        ):

            current_hour = (
                start_hour
                + cycle
            )

            result = self.run_cycle(
                current_hour=current_hour,
                horizon_hours=horizon_hours,
            )

            results.append(
                result
            )

        return results

    # =========================================================
    # WORKLOAD CONVERTER
    # =========================================================

    @staticmethod
    def workload_to_dict(
        workload
    ):
        """
        Convert a Workload dataclass into
        the dictionary format expected by
        the lifecycle simulator.
        """

        return {
            "workload_id":
                workload.workload_id,

            "gpu_required":
                workload.gpu_required,

            "duration_hours":
                workload.duration_hours,

            "deadline_hour":
                workload.deadline_hour,

            "priority":
                workload.priority,
        }

    # =========================================================
    # PRINT ONE CYCLE
    # =========================================================

    def print_cycle(
        self,
        cycle_record,
    ):
        """
        Print an operator-friendly cycle report.
        """

        summary = cycle_record[
            "executive_summary"
        ]

        lifecycle = cycle_record[
            "lifecycle_summary"
        ]

        print("\n")
        print("=" * 70)

        print(
            f"POWEROS CONTROL LOOP - "
            f"CYCLE {cycle_record['cycle']}"
        )

        print("=" * 70)

        print(
            f"Timestamp: "
            f"{cycle_record['timestamp']}"
        )

        # -----------------------------------------------------
        # SYSTEM
        # -----------------------------------------------------

        print("\nSYSTEM")
        print("-" * 70)

        print(
            f"Status: "
            f"{summary.get('system_status')}"
        )

        print(
            f"Bottleneck: "
            f"{summary.get('primary_bottleneck')}"
        )

        print(
            f"Power Pressure: "
            f"{summary.get('power_pressure_percent', 0):.2f}%"
        )

        print(
            f"Power Headroom: "
            f"{summary.get('power_headroom_kw', 0):.2f} kW"
        )

        # -----------------------------------------------------
        # FORECAST
        # -----------------------------------------------------

        print("\nFORECAST")
        print("-" * 70)

        print(
            f"Peak Forecast Power: "
            f"{summary.get('forecast_peak_power_kw', 0):.2f} kW"
        )

        print(
            f"Peak Forecast Hour: "
            f"{summary.get('forecast_peak_hour', 0)}"
        )

        # -----------------------------------------------------
        # ADMISSION
        # -----------------------------------------------------

        print("\nADMISSION")
        print("-" * 70)

        print(
            f"Admit: "
            f"{summary.get('admit_workloads', 0)}"
        )

        print(
            f"Delay: "
            f"{summary.get('delay_workloads', 0)}"
        )

        print(
            f"Shift: "
            f"{summary.get('shift_workloads', 0)}"
        )

        print(
            f"Protect: "
            f"{summary.get('protect_workloads', 0)}"
        )

        # -----------------------------------------------------
        # OPTIMIZATION
        # -----------------------------------------------------

        print("\nOPTIMIZATION")
        print("-" * 70)

        print(
            f"Scheduled: "
            f"{summary.get('scheduled_workloads', 0)}"
        )

        print(
            f"Unscheduled: "
            f"{summary.get('unscheduled_workloads', 0)}"
        )

        # -----------------------------------------------------
        # LIFECYCLE
        # -----------------------------------------------------

        print("\nWORKLOAD LIFECYCLE")
        print("-" * 70)

        print(
            f"Total: "
            f"{lifecycle.get('total_workloads', 0)}"
        )

        print(
            f"Completed: "
            f"{lifecycle.get('completed', 0)}"
        )

        print(
            f"Running: "
            f"{lifecycle.get('running', 0)}"
        )

        print(
            f"Queued: "
            f"{lifecycle.get('queued', 0)}"
        )

        print(
            f"Shifted: "
            f"{lifecycle.get('shifted', 0)}"
        )

        print(
            f"Paused: "
            f"{lifecycle.get('paused', 0)}"
        )

        print(
            f"Completion Rate: "
            f"{lifecycle.get('completion_rate_percent', 0):.2f}%"
        )

        print(
            f"Deadline Success: "
            f"{lifecycle.get('deadline_success_rate_percent', 0):.2f}%"
        )

        # -----------------------------------------------------
        # ENERGY
        # -----------------------------------------------------

        print("\nENERGY")
        print("-" * 70)

        print(
            f"Solar: "
            f"{summary.get('total_solar_energy_kwh', 0):.2f} kWh"
        )

        print(
            f"Battery: "
            f"{summary.get('total_battery_energy_kwh', 0):.2f} kWh"
        )

        print(
            f"Grid: "
            f"{summary.get('total_grid_energy_kwh', 0):.2f} kWh"
        )

        print(
            f"Battery SOC: "
            f"{summary.get('final_battery_soc_percent', 0):.2f}%"
        )

        print(
            f"Energy Cost: "
            f"₹{summary.get('total_energy_cost', 0):.2f}"
        )

        print("=" * 70)


# =============================================================
# DEMO
# =============================================================

def main():

    from poweros.demo import (
        create_demo_state,
        create_hourly_prices,
        create_hourly_solar,
    )

    print()
    print("=" * 70)
    print("ZYVARENTH POWEROS")
    print("CONTINUOUS CONTROL LOOP")
    print("=" * 70)

    print(
        "\nPowerOS is now continuously "
        "observing → predicting → optimizing → "
        "deciding → executing."
    )

    state = create_demo_state()

    prices = create_hourly_prices()

    solar = create_hourly_solar()

    control_loop = PowerOSControlLoop(
        state=state,
        electricity_prices=prices,
        solar_power_by_hour=solar,
        battery_capacity_kwh=100,
        initial_battery_soc_percent=80,
        battery_max_discharge_kw=10,
        reserve_percent=15,
    )

    results = control_loop.run(
        cycles=3,
        start_hour=0,
        horizon_hours=24,
    )

    for result in results:

        control_loop.print_cycle(
            result
        )

    print()
    print("=" * 70)
    print("POWEROS CONTROL LOOP COMPLETED")
    print("=" * 70)


if __name__ == "__main__":

    main()