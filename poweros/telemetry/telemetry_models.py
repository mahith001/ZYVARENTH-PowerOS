from dataclasses import dataclass
from typing import List


@dataclass
class GPUTelemetry:
    gpu_id: str
    utilization_percent: float
    power_kw: float
    temperature_c: float
    memory_utilization_percent: float


@dataclass
class WorkloadTelemetry:
    workload_id: str
    gpu_required: int
    duration_hours: float
    deadline_hour: int
    priority: str


@dataclass
class PowerTelemetry:
    available_power_kw: float
    grid_capacity_kw: float
    electricity_price_per_kwh: float
    solar_power_kw: float
    battery_available_kw: float


@dataclass
class BatteryTelemetry:
    capacity_kwh: float
    soc_percent: float
    max_discharge_kw: float


@dataclass
class TelemetrySnapshot:
    timestamp: str
    gpus: List[GPUTelemetry]
    workloads: List[WorkloadTelemetry]
    power: PowerTelemetry
    battery: BatteryTelemetry