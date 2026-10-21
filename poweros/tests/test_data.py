from poweros.data.ingestion import (
    build_data_center_state,
    summarize_state,
)


def test_data_ingestion():

    gpu_data = [
        {
            "gpu_id": "GPU-001",
            "utilization_percent": 75,
            "power_kw": 0.55,
            "temperature_c": 65,
            "memory_utilization_percent": 70,
            "available": True,
        },
        {
            "gpu_id": "GPU-002",
            "utilization_percent": 40,
            "power_kw": 0.28,
            "temperature_c": 55,
            "memory_utilization_percent": 35,
            "available": True,
        },
    ]

    workload_data = [
        {
            "workload_id": "JOB-001",
            "gpu_required": 2,
            "duration_hours": 4,
            "deadline_hour": 12,
            "priority": "HIGH",
        }
    ]

    power_data = {
        "available_power_kw": 500,
        "grid_capacity_kw": 600,
        "electricity_price_per_kwh": 8.5,
        "solar_power_kw": 100,
        "battery_available_kw": 50,
    }

    resource_data = [
        {
            "name": "Grid",
            "available_power_kw": 500,
            "cost_per_kwh": 8.5,
            "renewable": False,
        },
        {
            "name": "Solar",
            "available_power_kw": 100,
            "cost_per_kwh": 0,
            "renewable": True,
        },
    ]

    state = build_data_center_state(
        timestamp="2026-09-14T19:00:00",
        gpu_data=gpu_data,
        workload_data=workload_data,
        power_data=power_data,
        resource_data=resource_data,
    )

    summary = summarize_state(state)

    assert summary["total_gpus"] == 2
    assert summary["available_gpus"] == 2
    assert summary["workloads"] == 1
    assert summary["solar_power_kw"] == 100
    assert summary["grid_capacity_kw"] == 600


if __name__ == "__main__":

    test_data_ingestion()

    print()
    print("POWEROS DATA LAYER TEST PASSED")