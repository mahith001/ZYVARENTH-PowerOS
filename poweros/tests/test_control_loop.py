from typing import Dict, List, Optional

from poweros.core.models import DataCenterState
from poweros.core.orchestrator import run_poweros
from poweros.simulation.workload_lifecycle import (
    run_lifecycle_simulation,
    summarize_lifecycle,
)


# =========================================================
# POWEROS CONTROL LOOP
# =========================================================

class PowerOSControlLoop:
    """
    Main continuous control loop for ZYVARENTH PowerOS.

    Each cycle:

        DATA CENTER STATE
              ↓
        POWEROS ORCHESTRATOR
              ↓
        OPTIMIZATION
              ↓
        DECISIONS
              ↓
        WORKLOAD LIFECYCLE
              ↓
        EXECUTIVE RESULT
    """

    def __init__(
        self,
        state: DataCenterState,
        electricity_prices: Optional[List[float]] = None,
        solar_power_by_hour: Optional[List[float]] = None,
        battery_capacity_kwh: float = 100.0,
        initial_battery_soc_percent: float = 80.0,
        battery_max_discharge_kw: float = 10.0,
        reserve_percent: float = 15.0,
    ):
        """
        Create a PowerOS control loop.

        Parameters
        ----------
        state:
            Current data-center state.

        electricity_prices:
            Hourly electricity prices.

        solar_power_by_hour:
            Hourly solar availability.

        battery_capacity_kwh:
            Battery storage capacity.

        initial_battery_soc_percent:
            Initial battery state of charge.

        battery_max_discharge_kw:
            Maximum battery discharge power.

        reserve_percent:
            Power reserve kept for safety.
        """

        if not isinstance(
            state,
            DataCenterState,
        ):
            raise TypeError(
                "state must be a DataCenterState"
            )

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

        # Store every completed control cycle.
        self.history: List[Dict] = []

        self.cycle_count = 0

    # =====================================================
    # WORKLOAD CONVERSION
    # =====================================================

    @staticmethod
    def workload_to_dict(
        workload,
    ) -> Dict:
        """
        Convert a Workload dataclass into a
        lifecycle-compatible dictionary.
        """

        return {
            "workload_id": workload.workload_id,
            "gpu_required": workload.gpu_required,
            "duration_hours": workload.duration_hours,
            "deadline_hour": workload.deadline_hour,
            "priority": workload.priority,
        }

    # =====================================================
    # EXECUTIVE SUMMARY
    # =====================================================

    @staticmethod
    def build_executive_summary(
        poweros_result: Dict,
        lifecycle_result: Dict,
        lifecycle_summary: Dict,
        current_hour: int,
    ) -> Dict:
        """
        Build a compact executive summary for one
        PowerOS control cycle.
        """

        optimization_summary = (
            poweros_result.get(
                "optimization_summary",
                {},
            )
        )

        decision_summary = (
            poweros_result.get(
                "decision_summary",
                {},
            )
        )

        state_analysis = (
            poweros_result.get(
                "state_analysis",
                {},
            )
        )

        scheduled_count = (
            optimization_summary.get(
                "scheduled_count",
                optimization_summary.get(
                    "scheduled_workloads",
                    0,
                ),
            )
        )

        unscheduled_count = (
            optimization_summary.get(
                "unscheduled_count",
                optimization_summary.get(
                    "unscheduled_workloads",
                    0,
                ),
            )
        )

        total_count = (
            optimization_summary.get(
                "total_count",
                optimization_summary.get(
                    "total_workloads",
                    0,
                ),
            )
        )

        return {
            # ---------------------------------------------
            # CYCLE
            # ---------------------------------------------

            "cycle_hour": current_hour,

            # ---------------------------------------------
            # SYSTEM
            # ---------------------------------------------

            "system_status": state_analysis.get(
                "status",
                "UNKNOWN",
            ),

            "primary_bottleneck": state_analysis.get(
                "primary_bottleneck",
                "NONE",
            ),

            # ---------------------------------------------
            # POWER
            # ---------------------------------------------

            "power_pressure_percent": state_analysis.get(
                "power_pressure_percent",
                0.0,
            ),

            "power_headroom_kw": state_analysis.get(
                "power_headroom_kw",
                0.0,
            ),

            "safe_power_limit_kw": poweros_result.get(
                "safe_power_limit_kw",
                0.0,
            ),

            # ---------------------------------------------
            # OPTIMIZATION
            # ---------------------------------------------

            "total_workloads": total_count,

            "scheduled_workloads": scheduled_count,

            "unscheduled_workloads": unscheduled_count,

            # ---------------------------------------------
            # DECISIONS
            # ---------------------------------------------

            "run_decisions": decision_summary.get(
                "run",
                decision_summary.get(
                    "run_decisions",
                    0,
                ),
            ),

            "shift_decisions": decision_summary.get(
                "shift",
                decision_summary.get(
                    "shift_decisions",
                    0,
                ),
            ),

            "deadline_protection_decisions": (
                decision_summary.get(
                    "protect_deadline",
                    decision_summary.get(
                        "deadline_protection_decisions",
                        0,
                    ),
                )
            ),

            # ---------------------------------------------
            # LIFECYCLE
            # ---------------------------------------------

            "completed_workloads": lifecycle_summary.get(
                "completed",
                0,
            ),

            "running_workloads": lifecycle_summary.get(
                "running",
                0,
            ),

            "paused_workloads": lifecycle_summary.get(
                "paused",
                0,
            ),

            "shifted_workloads": lifecycle_summary.get(
                "shifted",
                0,
            ),

            "failed_workloads": lifecycle_summary.get(
                "failed",
                0,
            ),

            "completion_rate_percent": (
                lifecycle_summary.get(
                    "completion_rate_percent",
                    0.0,
                )
            ),

            "deadline_success_rate_percent": (
                lifecycle_summary.get(
                    "deadline_success_rate_percent",
                    0.0,
                )
            ),
        }

    # =====================================================
    # RUN ONE CONTROL CYCLE
    # =====================================================

    def run_cycle(
        self,
        current_hour: int = 0,
        horizon_hours: int = 24,
        power_constraint_hours: Optional[List[int]] = None,
    ) -> Dict:
        """
        Execute one complete PowerOS control cycle.
        """

        # -------------------------------------------------
        # 1. RUN POWEROS ORCHESTRATOR
        # -------------------------------------------------

        poweros_result = run_poweros(
            state=self.state,
            horizon_hours=horizon_hours,
            electricity_prices=self.electricity_prices,
            solar_power_by_hour=self.solar_power_by_hour,
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

        # -------------------------------------------------
        # 2. CONVERT WORKLOADS
        # -------------------------------------------------

        lifecycle_workloads = [
            self.workload_to_dict(
                workload
            )
            for workload in self.state.workloads
        ]

        # -------------------------------------------------
        # 3. EXTRACT SCHEDULE
        # -------------------------------------------------

        schedule = poweros_result.get(
            "schedule",
            None,
        )

        # -------------------------------------------------
        # 4. EXTRACT ADMISSION RESULTS
        # -------------------------------------------------

        admission_results = (
            poweros_result.get(
                "admission_results",
                None,
            )
        )

        # -------------------------------------------------
        # 5. RUN WORKLOAD LIFECYCLE
        # -------------------------------------------------

        lifecycle_result = (
            run_lifecycle_simulation(
                workloads=lifecycle_workloads,
                schedule=schedule,
                admission_results=admission_results,
                start_hour=current_hour,
                horizon_hours=horizon_hours,
                power_constraint_hours=(
                    power_constraint_hours
                ),
            )
        )

        # -------------------------------------------------
        # 6. SUMMARIZE LIFECYCLE
        # -------------------------------------------------

        lifecycle_summary = summarize_lifecycle(
            lifecycle_result
        )

        # -------------------------------------------------
        # 7. BUILD EXECUTIVE SUMMARY
        # -------------------------------------------------

        executive_summary = (
            self.build_executive_summary(
                poweros_result=poweros_result,
                lifecycle_result=lifecycle_result,
                lifecycle_summary=lifecycle_summary,
                current_hour=current_hour,
            )
        )

        # -------------------------------------------------
        # 8. CREATE COMPLETE CYCLE RESULT
        # -------------------------------------------------

        cycle_result = {
            # ---------------------------------------------
            # IDENTIFICATION
            # ---------------------------------------------

            "cycle": self.cycle_count + 1,

            "current_hour": current_hour,

            # ---------------------------------------------
            # MAIN POWEROS RESULT
            # ---------------------------------------------

            "poweros_result": poweros_result,

            # ---------------------------------------------
            # LIFECYCLE
            # ---------------------------------------------

            "lifecycle": lifecycle_result,

            "lifecycle_summary": lifecycle_summary,

            # ---------------------------------------------
            # EXECUTIVE SUMMARY
            # ---------------------------------------------

            "executive_summary": executive_summary,

            # ---------------------------------------------
            # DIRECT ACCESS TO IMPORTANT RESULTS
            # ---------------------------------------------

            "schedule": poweros_result.get(
                "schedule",
                {},
            ),

            "decisions": poweros_result.get(
                "decisions",
                [],
            ),

            "decision_summary": poweros_result.get(
                "decision_summary",
                {},
            ),

            "optimization_summary": (
                poweros_result.get(
                    "optimization_summary",
                    {},
                )
            ),

            "state_analysis": poweros_result.get(
                "state_analysis",
                {},
            ),

            "forecast": poweros_result.get(
                "forecast",
                {},
            ),

            "battery_dispatch": (
                poweros_result.get(
                    "battery_dispatch",
                    {},
                )
            ),

            "power_summary": poweros_result.get(
                "power_summary",
                {},
            ),
        }

        # -------------------------------------------------
        # 9. UPDATE COUNTERS / HISTORY
        # -------------------------------------------------

        self.cycle_count += 1

        cycle_result["cycle"] = (
            self.cycle_count
        )

        self.history.append(
            cycle_result
        )

        return cycle_result

    # =====================================================
    # RUN MULTIPLE CONTROL CYCLES
    # =====================================================

    def run(
        self,
        cycles: int = 3,
        start_hour: int = 0,
        horizon_hours: int = 24,
        power_constraint_hours: Optional[
            List[int]
        ] = None,
    ) -> List[Dict]:
        """
        Run multiple PowerOS control cycles.
        """

        results = []

        for index in range(cycles):

            current_hour = (
                start_hour + index
            )

            result = self.run_cycle(
                current_hour=current_hour,
                horizon_hours=horizon_hours,
                power_constraint_hours=(
                    power_constraint_hours
                ),
            )

            results.append(
                result
            )

        return results

    # =====================================================
    # PRINT ONE CYCLE
    # =====================================================

    @staticmethod
    def print_cycle(
        cycle_record: Dict,
    ) -> None:
        """
        Print a readable summary of one cycle.
        """

        summary = cycle_record.get(
            "executive_summary",
            {},
        )

        print()
        print("=" * 70)
        print("POWEROS CONTROL CYCLE")
        print("=" * 70)

        print(
            f"Cycle: "
            f"{cycle_record.get('cycle', 0)}"
        )

        print(
            f"Hour: "
            f"{summary.get('cycle_hour', 0)}"
        )

        print(
            f"System status: "
            f"{summary.get('system_status', 'UNKNOWN')}"
        )

        print(
            f"Bottleneck: "
            f"{summary.get('primary_bottleneck', 'NONE')}"
        )

        print(
            f"Power pressure: "
            f"{summary.get('power_pressure_percent', 0.0)}%"
        )

        print(
            f"Power headroom: "
            f"{summary.get('power_headroom_kw', 0.0)} kW"
        )

        print(
            f"Safe power limit: "
            f"{summary.get('safe_power_limit_kw', 0.0)} kW"
        )

        print(
            f"Total workloads: "
            f"{summary.get('total_workloads', 0)}"
        )

        print(
            f"Scheduled workloads: "
            f"{summary.get('scheduled_workloads', 0)}"
        )

        print(
            f"Unscheduled workloads: "
            f"{summary.get('unscheduled_workloads', 0)}"
        )

        print(
            f"RUN decisions: "
            f"{summary.get('run_decisions', 0)}"
        )

        print(
            f"SHIFT decisions: "
            f"{summary.get('shift_decisions', 0)}"
        )

        print(
            f"Deadline protection: "
            f"{summary.get('deadline_protection_decisions', 0)}"
        )

        print(
            f"Completed workloads: "
            f"{summary.get('completed_workloads', 0)}"
        )

        print(
            f"Running workloads: "
            f"{summary.get('running_workloads', 0)}"
        )

        print(
            f"Paused workloads: "
            f"{summary.get('paused_workloads', 0)}"
        )

        print(
            f"Completion rate: "
            f"{summary.get('completion_rate_percent', 0.0)}%"
        )

        print(
            f"Deadline success rate: "
            f"{summary.get('deadline_success_rate_percent', 0.0)}%"
        )

        print("=" * 70)

    # =====================================================
    # PRINT COMPLETE HISTORY
    # =====================================================

    def print_history(self) -> None:
        """
        Print all completed control cycles.
        """

        print()
        print("=" * 70)
        print("POWEROS CONTROL LOOP HISTORY")
        print("=" * 70)

        print(
            f"Total cycles: "
            f"{len(self.history)}"
        )

        for cycle in self.history:
            self.print_cycle(
                cycle
            )


# =========================================================
# DEMO / DIRECT EXECUTION
# =========================================================

def main():
    """
    Run the PowerOS control loop directly.
    """

    from poweros.demo import (
        create_demo_state,
        create_hourly_prices,
        create_hourly_solar,
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