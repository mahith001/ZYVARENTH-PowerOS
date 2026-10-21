GPU_POWER_KW = 0.7


def calculate_job_power(gpu_required: int) -> float:
    """Calculate approximate GPU power for a workload."""
    return gpu_required * GPU_POWER_KW


def calculate_energy(power_kw: float, duration_hours: int) -> float:
    """Calculate energy consumption in kWh."""
    return power_kw * duration_hours