from dataclasses import dataclass, field
from typing import List, Optional


# ============================================================
# WORKLOAD
# ============================================================

@dataclass
class Workload:

    workload_id: str
    gpu_required: int
    duration_hours: float
    deadline_hour: int
    priority: str = "MEDIUM"

    def __post_init__(self):

        if self.gpu_required <= 0:
            raise ValueError(
                "gpu_required must be greater than 0"
            )

        if self.duration_hours <= 0:
            raise ValueError(
                "duration_hours must be greater than 0"
            )

        if self.deadline_hour < 0:
            raise ValueError(
                "deadline_hour cannot be negative"
            )

        allowed_priorities = {
            "LOW",
            "MEDIUM",
            "HIGH",
        }

        if self.priority not in allowed_priorities:
            raise ValueError(
                "priority must be LOW, MEDIUM, or HIGH"
            )


# ============================================================
# GPU
# ============================================================

@dataclass
class GPU:

    gpu_id: str
    utilization_percent: float
    power_kw: float
    temperature_c: float
    memory_utilization_percent: float
    available: bool = True

    def __post_init__(self):

        self.utilization_percent = max(
            0,
            min(100, self.utilization_percent)
        )

        self.memory_utilization_percent = max(
            0,
            min(100, self.memory_utilization_percent)
        )

        self.power_kw = max(
            0,
            self.power_kw
        )


# ============================================================
# POWER STATE
# ============================================================

@dataclass
class PowerState:

    available_power_kw: float
    grid_capacity_kw: float
    electricity_price_per_kwh: float

    solar_power_kw: float = 0
    battery_available_kw: float = 0

    def __post_init__(self):

        if self.available_power_kw < 0:
            raise ValueError(
                "available_power_kw cannot be negative"
            )

        if self.grid_capacity_kw < 0:
            raise ValueError(
                "grid_capacity_kw cannot be negative"
            )

        if self.electricity_price_per_kwh < 0:
            raise ValueError(
                "electricity_price_per_kwh cannot be negative"
            )

        self.solar_power_kw = max(
            0,
            self.solar_power_kw
        )

        self.battery_available_kw = max(
            0,
            self.battery_available_kw
        )


# ============================================================
# ENERGY RESOURCE
# ============================================================

@dataclass
class EnergyResource:

    name: str
    available_power_kw: float
    cost_per_kwh: float
    renewable: bool = False

    def __post_init__(self):

        self.available_power_kw = max(
            0,
            self.available_power_kw
        )

        self.cost_per_kwh = max(
            0,
            self.cost_per_kwh
        )


# ============================================================
# DATA CENTER STATE
# ============================================================

@dataclass
class DataCenterState:

    timestamp: str

    gpus: List[GPU] = field(
        default_factory=list
    )

    workloads: List[Workload] = field(
        default_factory=list
    )

    power: Optional[PowerState] = None

    energy_resources: List[EnergyResource] = field(
        default_factory=list
    )

    # Power Usage Effectiveness.
    #
    # Example:
    # PUE = 1.0  -> idealized IT-only power
    # PUE = 1.3  -> 30% additional facility overhead
    #
    pue: float = 1.3

    def __post_init__(self):

        if self.pue < 1.0:
            raise ValueError(
                "PUE cannot be less than 1.0"
            )

    # --------------------------------------------------------
    # GPU COUNT
    # --------------------------------------------------------

    def total_gpu_count(self):

        return len(
            self.gpus
        )

    # --------------------------------------------------------
    # AVAILABLE GPU COUNT
    # --------------------------------------------------------

    def available_gpu_count(self):

        return sum(
            1
            for gpu in self.gpus
            if gpu.available
        )

    # --------------------------------------------------------
    # TOTAL GPU POWER
    # --------------------------------------------------------

    def total_gpu_power_kw(self):

        return sum(
            gpu.power_kw
            for gpu in self.gpus
        )

    # --------------------------------------------------------
    # AVERAGE GPU UTILIZATION
    # --------------------------------------------------------

    def average_gpu_utilization(self):

        if not self.gpus:
            return 0.0

        return (
            sum(
                gpu.utilization_percent
                for gpu in self.gpus
            )
            / len(self.gpus)
        )

    # --------------------------------------------------------
    # IT POWER
    # --------------------------------------------------------

    def calculate_it_power_kw(self):

        return self.total_gpu_power_kw()

    # --------------------------------------------------------
    # FACILITY POWER
    # --------------------------------------------------------

    def calculate_facility_power_kw(
        self,
        it_power_kw=None,
    ):

        if it_power_kw is None:

            it_power_kw = (
                self.calculate_it_power_kw()
            )

        return (
            it_power_kw
            * self.pue
        )

    # --------------------------------------------------------
    # COOLING / OVERHEAD POWER
    # --------------------------------------------------------

    def calculate_overhead_power_kw(
        self,
        it_power_kw=None,
    ):

        if it_power_kw is None:

            it_power_kw = (
                self.calculate_it_power_kw()
            )

        facility_power = (
            self.calculate_facility_power_kw(
                it_power_kw
            )
        )

        return (
            facility_power
            - it_power_kw
        )