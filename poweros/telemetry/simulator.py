import random

from datetime import datetime, timedelta

from poweros.telemetry.telemetry_models import (
    GPUTelemetry,
    WorkloadTelemetry,
    PowerTelemetry,
    BatteryTelemetry,
    TelemetrySnapshot,
)


class TelemetrySimulator:

    def __init__(
        self,
        gpu_count=20,
        start_hour=0,
    ):
        self.gpu_count = gpu_count

        # -----------------------------------------------------
        # SIMULATION CLOCK
        # -----------------------------------------------------

        self.current_hour = start_hour

        self.simulation_start = datetime.now()

        # -----------------------------------------------------
        # GPU STATE
        # -----------------------------------------------------

        self.base_utilization = 45.0

        self.previous_utilization = [
            self.base_utilization
            for _ in range(gpu_count)
        ]

        # -----------------------------------------------------
        # BATTERY STATE
        # -----------------------------------------------------

        self.battery_capacity_kwh = 100.0

        self.battery_soc_percent = 80.0

        # -----------------------------------------------------
        # POWER CONSTRAINT STATE
        # -----------------------------------------------------

        self.forced_available_power_kw = None

        self.forced_grid_capacity_kw = None

    # =========================================================
    # SIMULATION CLOCK
    # =========================================================

    def get_timestamp(self):

        timestamp = (
            self.simulation_start
            + timedelta(
                hours=self.current_hour
            )
        )

        return timestamp.isoformat()

    # =========================================================
    # POWER CONSTRAINT
    # =========================================================

    def apply_power_constraint(
        self,
        available_power_kw,
        grid_capacity_kw=None,
    ):
        """
        Force the simulated data center into
        a temporary power-constrained condition.
        """

        self.forced_available_power_kw = (
            available_power_kw
        )

        if grid_capacity_kw is not None:

            self.forced_grid_capacity_kw = (
                grid_capacity_kw
            )

    # =========================================================
    # CLEAR POWER CONSTRAINT
    # =========================================================

    def clear_power_constraint(self):
        """
        Remove the forced power constraint and
        return to normal operating conditions.
        """

        self.forced_available_power_kw = None

        self.forced_grid_capacity_kw = None

    # =========================================================
    # SOLAR PROFILE
    # =========================================================

    def calculate_solar_power(self):

        hour = self.current_hour % 24

        # Night
        if hour < 6 or hour >= 19:

            return 0.0

        # Sunrise
        if 6 <= hour < 9:

            return (
                hour - 6
            ) * 5.0

        # Morning
        if 9 <= hour < 12:

            return (
                15.0
                + (hour - 9) * 5.0
            )

        # Peak solar
        if 12 <= hour < 15:

            return 30.0

        # Afternoon decline
        if 15 <= hour < 18:

            return (
                30.0
                - (hour - 15) * 8.0
            )

        # Evening
        return 6.0

    # =========================================================
    # ELECTRICITY PRICE
    # =========================================================

    def calculate_electricity_price(self):

        hour = self.current_hour % 24

        prices = [
            9.0,
            8.8,
            8.5,
            8.0,
            7.0,
            6.5,
            6.0,
            5.5,
            5.0,
            5.5,
            6.0,
            7.0,
            8.0,
            9.0,
            10.0,
            11.0,
            12.0,
            13.0,
            12.0,
            11.0,
            10.0,
            9.5,
            9.0,
            8.5,
        ]

        return prices[hour]

    # =========================================================
    # WORKLOAD DEMAND
    # =========================================================

    def calculate_demand_level(self):

        hour = self.current_hour % 24

        if 0 <= hour < 6:

            target = 35.0

        elif 6 <= hour < 10:

            target = 55.0

        elif 10 <= hour < 14:

            target = 75.0

        elif 14 <= hour < 18:

            target = 85.0

        elif 18 <= hour < 22:

            target = 65.0

        else:

            target = 45.0

        variation = random.uniform(
            -5.0,
            5.0,
        )

        return max(
            10.0,
            min(
                95.0,
                target + variation,
            ),
        )

    # =========================================================
    # GPU TELEMETRY
    # =========================================================

    def generate_gpu_telemetry(self):

        demand_level = (
            self.calculate_demand_level()
        )

        gpus = []

        for i in range(
            self.gpu_count
        ):

            previous = (
                self.previous_utilization[i]
            )

            target = (
                demand_level
                + random.uniform(
                    -8.0,
                    8.0,
                )
            )

            # Smooth transition
            utilization = (
                previous * 0.6
                + target * 0.4
            )

            utilization = max(
                5.0,
                min(
                    98.0,
                    utilization,
                ),
            )

            # GPU power model
            power = (
                0.30
                + (
                    utilization
                    / 100.0
                ) * 0.40
            )

            # Temperature model
            temperature = (
                42.0
                + (
                    utilization
                    / 100.0
                ) * 42.0
            )

            # Memory model
            memory = (
                utilization * 0.85
                + random.uniform(
                    -5.0,
                    5.0,
                )
            )

            memory = max(
                5.0,
                min(
                    98.0,
                    memory,
                ),
            )

            gpus.append(
                GPUTelemetry(
                    gpu_id=(
                        f"GPU-{i + 1:03d}"
                    ),
                    utilization_percent=round(
                        utilization,
                        2,
                    ),
                    power_kw=round(
                        power,
                        3,
                    ),
                    temperature_c=round(
                        temperature,
                        2,
                    ),
                    memory_utilization_percent=round(
                        memory,
                        2,
                    ),
                )
            )

            self.previous_utilization[i] = (
                utilization
            )

        return gpus

    # =========================================================
    # WORKLOAD TELEMETRY
    # =========================================================

    def generate_workload_telemetry(self):

        return [

            WorkloadTelemetry(
                workload_id="LLM-TRAIN-001",
                gpu_required=8,
                duration_hours=4,
                deadline_hour=12,
                priority="HIGH",
            ),

            WorkloadTelemetry(
                workload_id="LLM-TRAIN-002",
                gpu_required=6,
                duration_hours=3,
                deadline_hour=16,
                priority="HIGH",
            ),

            WorkloadTelemetry(
                workload_id="INFERENCE-001",
                gpu_required=2,
                duration_hours=2,
                deadline_hour=18,
                priority="MEDIUM",
            ),

            WorkloadTelemetry(
                workload_id="BATCH-001",
                gpu_required=4,
                duration_hours=3,
                deadline_hour=22,
                priority="LOW",
            ),

        ]

    # =========================================================
    # GRID CAPACITY
    # =========================================================

    def calculate_grid_capacity(self):

        hour = self.current_hour % 24

        # Forced external grid constraint
        if (
            self.forced_grid_capacity_kw
            is not None
        ):

            return (
                self.forced_grid_capacity_kw
            )

        # Normal simulated conditions
        if 14 <= hour < 18:

            return 55.0

        if 18 <= hour < 22:

            return 58.0

        return 60.0

    # =========================================================
    # AVAILABLE POWER
    # =========================================================

    def calculate_available_power(
        self,
        solar_power,
    ):

        grid_capacity = (
            self.calculate_grid_capacity()
        )

        # Normal operating limit
        base_limit = 50.0

        # Solar contribution
        available = (
            base_limit
            + min(
                solar_power,
                15.0,
            )
        )

        # Forced power constraint
        if (
            self.forced_available_power_kw
            is not None
        ):

            available = min(
                available,
                self.forced_available_power_kw,
            )

        # Never exceed grid capacity
        return min(
            available,
            grid_capacity,
        )

    # =========================================================
    # BATTERY AVAILABLE POWER
    # =========================================================

    def calculate_battery_available_power(self):

        if (
            self.battery_soc_percent
            <= 10.0
        ):

            return 0.0

        if (
            self.battery_soc_percent
            <= 25.0
        ):

            return 5.0

        return 10.0

    # =========================================================
    # POWER TELEMETRY
    # =========================================================

    def generate_power_telemetry(self):

        solar_power = (
            self.calculate_solar_power()
        )

        price = (
            self.calculate_electricity_price()
        )

        grid_capacity = (
            self.calculate_grid_capacity()
        )

        available_power = (
            self.calculate_available_power(
                solar_power
            )
        )

        battery_available = (
            self.calculate_battery_available_power()
        )

        return PowerTelemetry(

            available_power_kw=round(
                available_power,
                2,
            ),

            grid_capacity_kw=round(
                grid_capacity,
                2,
            ),

            electricity_price_per_kwh=round(
                price,
                2,
            ),

            solar_power_kw=round(
                solar_power,
                2,
            ),

            battery_available_kw=round(
                battery_available,
                2,
            ),

        )

    # =========================================================
    # BATTERY TELEMETRY
    # =========================================================

    def generate_battery_telemetry(self):

        return BatteryTelemetry(

            capacity_kwh=(
                self.battery_capacity_kwh
            ),

            soc_percent=round(
                self.battery_soc_percent,
                2,
            ),

            max_discharge_kw=10.0,

        )

    # =========================================================
    # UPDATE BATTERY
    # =========================================================

    def update_battery_state(
        self,
        solar_power,
    ):

        hour = self.current_hour % 24

        # Solar charging
        if 9 <= hour < 16:

            charging_amount = (
                solar_power * 0.08
            )

            self.battery_soc_percent += (
                charging_amount
            )

        # Evening discharge
        elif 17 <= hour < 22:

            discharge_amount = 3.0

            self.battery_soc_percent -= (
                discharge_amount
            )

        # Physical limits
        self.battery_soc_percent = max(
            5.0,
            min(
                100.0,
                self.battery_soc_percent,
            ),
        )

    # =========================================================
    # GENERATE COMPLETE SNAPSHOT
    # =========================================================

    def generate_snapshot(self):

        timestamp = (
            self.get_timestamp()
        )

        gpus = (
            self.generate_gpu_telemetry()
        )

        workloads = (
            self.generate_workload_telemetry()
        )

        power = (
            self.generate_power_telemetry()
        )

        battery = (
            self.generate_battery_telemetry()
        )

        snapshot = TelemetrySnapshot(

            timestamp=timestamp,

            gpus=gpus,

            workloads=workloads,

            power=power,

            battery=battery,

        )

        # Update battery after snapshot
        self.update_battery_state(
            power.solar_power_kw
        )

        # Advance simulation clock
        self.current_hour += 1

        return snapshot


# =============================================================
# TELEMETRY REPORT
# =============================================================

def print_telemetry_snapshot(
    snapshot
):

    print("\n" + "=" * 70)

    print(
        "POWEROS LIVE TELEMETRY"
    )

    print("=" * 70)

    print(
        f"Timestamp: "
        f"{snapshot.timestamp}"
    )

    # ---------------------------------------------------------
    # GPU
    # ---------------------------------------------------------

    print("\nGPU TELEMETRY")

    print("-" * 70)

    total_power = 0.0

    total_utilization = 0.0

    for gpu in snapshot.gpus[:5]:

        print(

            f"{gpu.gpu_id} | "

            f"Utilization: "
            f"{gpu.utilization_percent:.1f}% | "

            f"Power: "
            f"{gpu.power_kw:.3f} kW | "

            f"Temp: "
            f"{gpu.temperature_c:.1f} C | "

            f"Memory: "
            f"{gpu.memory_utilization_percent:.1f}%"

        )

    for gpu in snapshot.gpus:

        total_power += (
            gpu.power_kw
        )

        total_utilization += (
            gpu.utilization_percent
        )

    if snapshot.gpus:

        average_utilization = (
            total_utilization
            / len(snapshot.gpus)
        )

    else:

        average_utilization = 0.0

    print(
        f"\nTotal GPU Power: "
        f"{total_power:.2f} kW"
    )

    print(
        f"Average GPU Utilization: "
        f"{average_utilization:.2f}%"
    )

    if len(snapshot.gpus) > 5:

        print(
            f"... "
            f"{len(snapshot.gpus) - 5} "
            f"more GPUs"
        )

    # ---------------------------------------------------------
    # POWER
    # ---------------------------------------------------------

    print("\nPOWER")

    print("-" * 70)

    print(
        f"Available Power: "
        f"{snapshot.power.available_power_kw:.2f} kW"
    )

    print(
        f"Grid Capacity: "
        f"{snapshot.power.grid_capacity_kw:.2f} kW"
    )

    print(
        f"Electricity Price: "
        f"₹{snapshot.power.electricity_price_per_kwh:.2f}/kWh"
    )

    print(
        f"Solar Power: "
        f"{snapshot.power.solar_power_kw:.2f} kW"
    )

    print(
        f"Battery Available: "
        f"{snapshot.power.battery_available_kw:.2f} kW"
    )

    # ---------------------------------------------------------
    # BATTERY
    # ---------------------------------------------------------

    print("\nBATTERY")

    print("-" * 70)

    print(
        f"Capacity: "
        f"{snapshot.battery.capacity_kwh:.2f} kWh"
    )

    print(
        f"State of Charge: "
        f"{snapshot.battery.soc_percent:.2f}%"
    )

    print(
        f"Max Discharge: "
        f"{snapshot.battery.max_discharge_kw:.2f} kW"
    )

    # ---------------------------------------------------------
    # WORKLOADS
    # ---------------------------------------------------------

    print("\nWORKLOADS")

    print("-" * 70)

    for workload in snapshot.workloads:

        print(

            f"{workload.workload_id} | "

            f"GPUs: "
            f"{workload.gpu_required} | "

            f"Duration: "
            f"{workload.duration_hours}h | "

            f"Deadline: "
            f"{workload.deadline_hour} | "

            f"Priority: "
            f"{workload.priority}"

        )