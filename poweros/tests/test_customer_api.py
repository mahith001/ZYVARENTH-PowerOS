
"""
ZYVARENTH PowerOS
Customer API Integration Test

Tests customer configuration validation and a real
customer workload run through the Flask API.
"""

import unittest

from poweros.dashboard.web_app import app


def create_test_customer():
    """Return a realistic sample customer request."""

    return {
        "customer_name": "PowerOS API Test Customer",

        "gpus": [
            {
                "gpu_id": "TEST-GPU-001",
                "power_kw": 0.7,
                "utilization_percent": 40,
                "temperature_c": 60,
                "memory_utilization_percent": 50,
                "available": True,
            },
            {
                "gpu_id": "TEST-GPU-002",
                "power_kw": 0.7,
                "utilization_percent": 50,
                "temperature_c": 62,
                "memory_utilization_percent": 60,
                "available": True,
            },
            {
                "gpu_id": "TEST-GPU-003",
                "power_kw": 0.7,
                "utilization_percent": 30,
                "temperature_c": 58,
                "memory_utilization_percent": 40,
                "available": True,
            },
            {
                "gpu_id": "TEST-GPU-004",
                "power_kw": 0.7,
                "utilization_percent": 20,
                "temperature_c": 57,
                "memory_utilization_percent": 30,
                "available": True,
            },
        ],

        "workloads": [
            {
                "workload_id": "TEST-TRAIN-001",
                "gpu_required": 2,
                "duration_hours": 3,
                "deadline_hour": 12,
                "priority": "HIGH",
            },
            {
                "workload_id": "TEST-INFERENCE-001",
                "gpu_required": 1,
                "duration_hours": 2,
                "deadline_hour": 18,
                "priority": "MEDIUM",
            },
            {
                "workload_id": "TEST-BATCH-001",
                "gpu_required": 2,
                "duration_hours": 4,
                "deadline_hour": 23,
                "priority": "LOW",
            },
        ],

        "power": {
            "available_power_kw": 10.0,
            "grid_capacity_kw": 15.0,
            "electricity_price_per_kwh": 8.5,
            "solar_power_kw": 3.0,
            "battery_available_kw": 2.0,
        },

        "energy_resources": [
            {
                "name": "GRID",
                "available_power_kw": 15.0,
                "cost_per_kwh": 8.5,
                "renewable": False,
            },
            {
                "name": "SOLAR",
                "available_power_kw": 3.0,
                "cost_per_kwh": 0.0,
                "renewable": True,
            },
            {
                "name": "BATTERY",
                "available_power_kw": 2.0,
                "cost_per_kwh": 6.0,
                "renewable": False,
            },
        ],

        "pue": 1.3,
    }


class TestCustomerAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def test_customer_validation(self):
        """Test the customer validation endpoint."""

        response = self.client.post(
            "/api/customer/validate",
            json=create_test_customer(),
        )

        self.assertEqual(
            response.status_code,
            200,
            msg=response.get_data(as_text=True),
        )

        result = response.get_json()

        self.assertEqual(result["status"], "VALID")
        self.assertEqual(result["gpu_count"], 4)
        self.assertEqual(result["workload_count"], 3)

        print("\nPASS: Customer validation")

    def test_invalid_customer(self):
        """Test that missing customer data is rejected."""

        response = self.client.post(
            "/api/customer/validate",
            json={"customer_name": "Incomplete Customer"},
        )

        self.assertEqual(response.status_code, 400)

        result = response.get_json()

        self.assertEqual(result["status"], "INVALID")

        print("PASS: Invalid customer rejected")

    def test_customer_poweros_run(self):
        """Test a complete customer run through PowerOS."""

        response = self.client.post(
            "/api/customer/run",
            json=create_test_customer(),
        )

        result = response.get_json()

        self.assertEqual(
            response.status_code,
            200,
            msg=str(result),
        )

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(
            result["customer_name"],
            "PowerOS API Test Customer",
        )

        optimization = result["optimization"]

        self.assertIn("scheduled", optimization)
        self.assertIn("unscheduled", optimization)
        self.assertIn("scheduled_workloads", optimization)
        self.assertIn("unscheduled_workloads", optimization)

        self.assertEqual(
            optimization["scheduled"]
            + optimization["unscheduled"],
            3,
            msg="Every submitted workload should have a scheduling outcome.",
        )

        print("PASS: Customer PowerOS run")
        print(
            "Scheduled:",
            optimization["scheduled"],
        )
        print(
            "Unscheduled:",
            optimization["unscheduled"],
        )

        print(
            "Decision summary:",
            result.get("decision_summary"),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
