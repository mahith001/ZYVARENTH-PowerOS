"""
ZYVARENTH PowerOS
Customer Data Configuration

Creates and validates customer-provided infrastructure,
workload, and energy configuration.
"""

from dataclasses import dataclass, field
from typing import List


# ============================================================
# CUSTOMER GPU
# ============================================================

@dataclass
class CustomerGPU:

    gpu_id: str

    power_kw: float = 0.7

    utilization_percent: float = 0.0

    temperature_c: float = 60.0

    memory_utilization_percent: float = 0.0

    available: bool = True

    def validate(self):

        if not self.gpu_id:
            raise ValueError(
                "GPU ID cannot be empty."
            )

        if self.power_kw < 0:
            raise ValueError(
                "GPU power cannot be negative."
            )

        if not 0 <= self.utilization_percent <= 100:
            raise ValueError(
                "GPU utilization must be between 0 and 100."
            )

        if self.temperature_c < 0:
            raise ValueError(
                "GPU temperature cannot be negative."
            )

        if not 0 <= self.memory_utilization_percent <= 100:
            raise ValueError(
                "GPU memory utilization must be between 0 and 100."
            )


# ============================================================
# CUSTOMER WORKLOAD
# ============================================================

@dataclass
class CustomerWorkload:

    workload_id: str

    gpu_required: int

    duration_hours: float

    deadline_hour: int

    priority: str = "MEDIUM"

    def validate(self):

        if not self.workload_id:
            raise ValueError(
                "Workload ID cannot be empty."
            )

        if self.gpu_required <= 0:
            raise ValueError(
                "GPU requirement must be greater than zero."
            )

        if self.duration_hours <= 0:
            raise ValueError(
                "Workload duration must be greater than zero."
            )

        if self.deadline_hour < 0:
            raise ValueError(
                "Deadline cannot be negative."
            )

        if self.priority.upper() not in {
            "LOW",
            "MEDIUM",
            "HIGH",
        }:

            raise ValueError(
                "Priority must be LOW, MEDIUM, or HIGH."
            )


# ============================================================
# CUSTOMER POWER CONFIGURATION
# ============================================================

@dataclass
class CustomerPower:

    available_power_kw: float

    grid_capacity_kw: float

    electricity_price_per_kwh: float

    solar_power_kw: float = 0.0

    battery_available_kw: float = 0.0

    def validate(self):

        if self.available_power_kw < 0:
            raise ValueError(
                "Available power cannot be negative."
            )

        if self.grid_capacity_kw < 0:
            raise ValueError(
                "Grid capacity cannot be negative."
            )

        if self.electricity_price_per_kwh < 0:
            raise ValueError(
                "Electricity price cannot be negative."
            )

        if self.solar_power_kw < 0:
            raise ValueError(
                "Solar power cannot be negative."
            )

        if self.battery_available_kw < 0:
            raise ValueError(
                "Battery power cannot be negative."
            )


# ============================================================
# CUSTOMER ENERGY RESOURCE
# ============================================================

@dataclass
class CustomerEnergyResource:

    name: str

    available_power_kw: float

    cost_per_kwh: float

    renewable: bool = False

    def validate(self):

        if not self.name:
            raise ValueError(
                "Energy resource name cannot be empty."
            )

        if self.available_power_kw < 0:
            raise ValueError(
                "Energy resource power cannot be negative."
            )

        if self.cost_per_kwh < 0:
            raise ValueError(
                "Energy resource cost cannot be negative."
            )


# ============================================================
# COMPLETE CUSTOMER CONFIGURATION
# ============================================================

@dataclass
class CustomerConfiguration:

    customer_name: str

    gpus: List[CustomerGPU] = field(
        default_factory=list
    )

    workloads: List[CustomerWorkload] = field(
        default_factory=list
    )

    power: CustomerPower = None

    energy_resources: List[
        CustomerEnergyResource
    ] = field(
        default_factory=list
    )

    pue: float = 1.3

    def validate(self):

        if not self.customer_name:
            raise ValueError(
                "Customer name cannot be empty."
            )

        if not self.gpus:
            raise ValueError(
                "At least one GPU is required."
            )

        if not self.workloads:
            raise ValueError(
                "At least one workload is required."
            )

        if self.power is None:
            raise ValueError(
                "Power configuration is required."
            )

        if self.pue < 1.0:
            raise ValueError(
                "PUE must be at least 1.0."
            )

        for gpu in self.gpus:

            gpu.validate()

        for workload in self.workloads:

            workload.validate()

        self.power.validate()

        for resource in self.energy_resources:

            resource.validate()


# ============================================================
# CREATE EXAMPLE CUSTOMER
# ============================================================

def create_example_customer():

    gpus = [

        CustomerGPU(
            gpu_id="GPU-001",
            power_kw=0.7,
            utilization_percent=55,
            temperature_c=65,
            memory_utilization_percent=60,
        ),

        CustomerGPU(
            gpu_id="GPU-002",
            power_kw=0.7,
            utilization_percent=45,
            temperature_c=63,
            memory_utilization_percent=55,
        ),

        CustomerGPU(
            gpu_id="GPU-003",
            power_kw=0.7,
            utilization_percent=70,
            temperature_c=68,
            memory_utilization_percent=72,
        ),

        CustomerGPU(
            gpu_id="GPU-004",
            power_kw=0.7,
            utilization_percent=30,
            temperature_c=60,
            memory_utilization_percent=40,
        ),

    ]


    workloads = [

        CustomerWorkload(
            workload_id="CUSTOMER-LLM-001",
            gpu_required=2,
            duration_hours=4,
            deadline_hour=12,
            priority="HIGH",
        ),

        CustomerWorkload(
            workload_id="CUSTOMER-TRAIN-001",
            gpu_required=4,
            duration_hours=6,
            deadline_hour=18,
            priority="HIGH",
        ),

        CustomerWorkload(
            workload_id="CUSTOMER-INFER-001",
            gpu_required=1,
            duration_hours=2,
            deadline_hour=20,
            priority="MEDIUM",
        ),

        CustomerWorkload(
            workload_id="CUSTOMER-BATCH-001",
            gpu_required=2,
            duration_hours=3,
            deadline_hour=23,
            priority="LOW",
        ),

    ]


    power = CustomerPower(

        available_power_kw=10.0,

        grid_capacity_kw=15.0,

        electricity_price_per_kwh=8.5,

        solar_power_kw=3.0,

        battery_available_kw=2.0,

    )


    resources = [

        CustomerEnergyResource(
            name="GRID",
            available_power_kw=15.0,
            cost_per_kwh=8.5,
            renewable=False,
        ),

        CustomerEnergyResource(
            name="SOLAR",
            available_power_kw=3.0,
            cost_per_kwh=0.0,
            renewable=True,
        ),

        CustomerEnergyResource(
            name="BATTERY",
            available_power_kw=2.0,
            cost_per_kwh=6.0,
            renewable=False,
        ),

    ]


    customer = CustomerConfiguration(

        customer_name="ZYVARENTH Demo Customer",

        gpus=gpus,

        workloads=workloads,

        power=power,

        energy_resources=resources,

        pue=1.3,

    )


    return customer


# ============================================================
# VALIDATE CUSTOMER
# ============================================================

def validate_customer(
    customer
):

    customer.validate()

    return True


# ============================================================
# SUMMARY
# ============================================================

def summarize_customer(
    customer
):

    customer.validate()

    return {

        "customer_name":
            customer.customer_name,

        "gpu_count":
            len(customer.gpus),

        "workload_count":
            len(customer.workloads),

        "available_power_kw":
            customer.power.available_power_kw,

        "grid_capacity_kw":
            customer.power.grid_capacity_kw,

        "electricity_price_per_kwh":
            customer.power.electricity_price_per_kwh,

        "solar_power_kw":
            customer.power.solar_power_kw,

        "battery_available_kw":
            customer.power.battery_available_kw,

        "pue":
            customer.pue,

    }


# ============================================================
# PRINT SUMMARY
# ============================================================

def print_customer_summary(
    summary
):

    print()

    print("=" * 70)

    print(
        "ZYVARENTH POWEROS"
    )

    print(
        "CUSTOMER CONFIGURATION"
    )

    print("=" * 70)

    print()

    print(
        "Customer:",
        summary["customer_name"],
    )

    print(
        "GPUs:",
        summary["gpu_count"],
    )

    print(
        "Workloads:",
        summary["workload_count"],
    )

    print(
        "Available Power:",
        summary["available_power_kw"],
        "kW",
    )

    print(
        "Grid Capacity:",
        summary["grid_capacity_kw"],
        "kW",
    )

    print(
        "Electricity Price:",
        summary["electricity_price_per_kwh"],
        "₹/kWh",
    )

    print(
        "Solar:",
        summary["solar_power_kw"],
        "kW",
    )

    print(
        "Battery:",
        summary["battery_available_kw"],
        "kW",
    )

    print(
        "PUE:",
        summary["pue"],
    )

    print()

    print(
        "CUSTOMER CONFIGURATION VALIDATED"
    )

    print("=" * 70)


# ============================================================
# TEST
# ============================================================

def main():

    customer = (
        create_example_customer()
    )

    validate_customer(
        customer
    )

    summary = summarize_customer(
        customer
    )

    print_customer_summary(
        summary
    )


if __name__ == "__main__":

    main()