
from poweros.intelligence.state_analyzer import analyze_state
from poweros.intelligence.forecasting import generate_forecast
from poweros.intelligence.safety_engine import calculate_safe_power_limit
from poweros.intelligence.optimizer import optimize_workloads, summarize_optimization
from poweros.intelligence.energy_dispatch import simulate_battery_dispatch
from poweros.decisions.admission_control import evaluate_workloads, summarize_admission
from poweros.decisions.decision_engine import create_decisions, summarize_decisions


# =============================================================
# DEFAULT HOURLY DATA
# =============================================================

def create_default_prices(state, horizon_hours=24):
    """Create an electricity-price profile scaled to the customer's price."""
    if horizon_hours < 1:
        raise ValueError("horizon_hours must be at least 1")

    base_price = max(float(state.power.electricity_price_per_kwh), 0.01)

    profile = [
        9.0, 8.8, 8.5, 8.0, 7.0, 6.5,
        6.0, 5.5, 5.0, 5.5, 6.0, 7.0,
        8.0, 9.0, 10.0, 11.0, 12.0, 13.0,
        12.0, 11.0, 10.0, 9.5, 9.0, 8.5,
    ]

    return [
        round(profile[hour % len(profile)] * base_price / 8.5, 3)
        for hour in range(horizon_hours)
    ]


def create_default_solar(state, horizon_hours=24):
    """Create a 24-hour solar generation profile."""
    if horizon_hours < 1:
        raise ValueError("horizon_hours must be at least 1")

    profile = [
        0, 0, 0, 0, 1, 3, 6, 10, 15, 20, 25, 30,
        35, 32, 28, 22, 16, 10, 5, 2, 0, 0, 0, 0,
    ]

    current_solar = max(float(state.power.solar_power_kw), 0.0)
    scale = current_solar / 15.0 if current_solar > 0 else 1.0

    return [
        round(profile[hour % len(profile)] * scale, 3)
        for hour in range(horizon_hours)
    ]


# =============================================================
# POWER AND ENERGY HELPERS
# =============================================================

def calculate_workload_power(workload, gpu_power_kw=0.7):
    """Return workload IT power in kW."""
    return float(workload.gpu_required) * float(gpu_power_kw)


def build_power_demand_by_hour(schedule, horizon_hours=24, pue=1.3):
    """
    Build hourly facility power in kW.

    Each hour includes the IT power of every scheduled workload
    active during that hour, multiplied by PUE.
    """
    if horizon_hours < 1:
        raise ValueError("horizon_hours must be at least 1")
    if pue < 1:
        raise ValueError("PUE must be at least 1")

    demand = [0.0] * horizon_hours
    scheduled_items = schedule.get("scheduled", [])

    if not isinstance(scheduled_items, list):
        return demand

    for item in scheduled_items:
        if not isinstance(item, dict):
            continue
        if item.get("status", "SCHEDULED") != "SCHEDULED":
            continue

        start = int(item.get("start_hour", 0))
        duration = int(item.get("duration_hours", 0))
        power_kw = float(item.get("power_kw", 0.0))

        if start < 0 or duration < 0 or power_kw < 0:
            continue

        facility_power = power_kw * pue

        for hour in range(start, min(start + duration, horizon_hours)):
            demand[hour] += facility_power

    return demand


def calculate_power_summary(schedule, power_demand_by_hour, pue):
    """
    Calculate comparable peak IT/facility power and energy metrics.

    Energy is the sum of hourly average facility power over one-hour
    intervals. total_it_energy_kwh is energy, not instantaneous power.
    """
    hourly_it_power = [value / pue for value in power_demand_by_hour]

    peak_it_power_kw = max(hourly_it_power, default=0.0)
    peak_facility_power_kw = max(power_demand_by_hour, default=0.0)

    total_it_energy_kwh = sum(hourly_it_power)
    total_facility_energy_kwh = sum(power_demand_by_hour)

    cooling_overhead_kw = max(
        peak_facility_power_kw - peak_it_power_kw,
        0.0,
    )

    return {
        "total_it_power_kw": peak_it_power_kw,
        "peak_it_power_kw": peak_it_power_kw,
        "peak_facility_power_kw": peak_facility_power_kw,
        "cooling_overhead_kw": cooling_overhead_kw,
        "total_it_energy_kwh": total_it_energy_kwh,
        "total_facility_energy_kwh": total_facility_energy_kwh,
    }


# =============================================================
# RUN POWEROS
# =============================================================

def run_poweros(
    state,
    horizon_hours=24,
    electricity_prices=None,
    solar_power_by_hour=None,
    battery_capacity_kwh=100.0,
    initial_battery_soc_percent=80.0,
    battery_max_discharge_kw=10.0,
    reserve_percent=15.0,
):
    """Run the PowerOS analysis, scheduling, dispatch, and decision pipeline."""
    if not isinstance(horizon_hours, int) or horizon_hours < 1:
        raise ValueError("horizon_hours must be a positive integer")
    if not 0 <= initial_battery_soc_percent <= 100:
        raise ValueError("initial_battery_soc_percent must be between 0 and 100")
    if battery_capacity_kwh < 0 or battery_max_discharge_kw < 0:
        raise ValueError("Battery capacity and discharge power cannot be negative")
    if not 0 <= reserve_percent < 100:
        raise ValueError("reserve_percent must be in the range [0, 100)")
    if state.pue < 1:
        raise ValueError("PUE must be at least 1")

    if electricity_prices is None:
        electricity_prices = create_default_prices(state, horizon_hours)
    else:
        electricity_prices = list(electricity_prices)

    if solar_power_by_hour is None:
        solar_power_by_hour = create_default_solar(state, horizon_hours)
    else:
        solar_power_by_hour = list(solar_power_by_hour)

    if any(float(value) < 0 for value in electricity_prices):
        raise ValueError("Electricity prices cannot be negative")
    if any(float(value) < 0 for value in solar_power_by_hour):
        raise ValueError("Solar generation values cannot be negative")

    default_price = float(state.power.electricity_price_per_kwh)
    default_solar = float(state.power.solar_power_kw)

    electricity_prices = (
        electricity_prices[:horizon_hours]
        + [electricity_prices[-1] if electricity_prices else default_price]
        * max(0, horizon_hours - len(electricity_prices))
    )
    solar_power_by_hour = (
        solar_power_by_hour[:horizon_hours]
        + [solar_power_by_hour[-1] if solar_power_by_hour else default_solar]
        * max(0, horizon_hours - len(solar_power_by_hour))
    )

    # 1. State analysis and forecasting
    state_analysis = analyze_state(state)
    forecast = generate_forecast(
        state,
        horizon_hours=horizon_hours,
        gpu_power_kw=0.7,
    )

    # 2. Safe power limit
    safe_power_limit_kw = calculate_safe_power_limit(
        state.power.available_power_kw,
        reserve_percent=reserve_percent,
    )

    # 3. Admission control
    admission_results = evaluate_workloads(
        workloads=state.workloads,
        current_hour=0,
        available_safe_power_kw=safe_power_limit_kw,
    )
    admission_summary = summarize_admission(admission_results)

    # 4. Workload optimization
    schedule = optimize_workloads(
        state=state,
        horizon_hours=horizon_hours,
        electricity_prices=electricity_prices,
        solar_power_by_hour=solar_power_by_hour,
        gpu_power_kw=0.7,
        reserve_percent=reserve_percent,
        admission_results=admission_results,
    )
    optimization_summary = summarize_optimization(schedule)

    # 5. Hourly IT and facility power
    power_demand_by_hour = build_power_demand_by_hour(
        schedule=schedule,
        horizon_hours=horizon_hours,
        pue=state.pue,
    )
    power_summary = calculate_power_summary(
        schedule,
        power_demand_by_hour,
        state.pue,
    )

    # 6. Energy dispatch
    battery_result = simulate_battery_dispatch(
        power_demand_by_hour=power_demand_by_hour,
        solar_by_hour=solar_power_by_hour,
        electricity_prices=electricity_prices,
        battery_capacity_kwh=battery_capacity_kwh,
        initial_soc_percent=initial_battery_soc_percent,
        max_discharge_kw=battery_max_discharge_kw,
        grid_capacity_kw=state.power.grid_capacity_kw,
    )

    # 7. Decisions
    decisions = create_decisions(schedule, current_hour=0)
    decision_summary = summarize_decisions(decisions)

    return {
        "state_analysis": state_analysis,
        "forecast": forecast,
        "admission_results": admission_results,
        "admission_summary": admission_summary,
        "safe_power_limit_kw": safe_power_limit_kw,
        "schedule": schedule,
        "optimization_summary": optimization_summary,
        "battery_dispatch": battery_result,
        "power_summary": power_summary,
        "power_demand_by_hour": power_demand_by_hour,
        "decisions": decisions,
        "decision_summary": decision_summary,
    }


# =============================================================
# FORECAST HELPERS
# =============================================================

def get_forecast_peak_power(forecast):
    """Safely extract a forecast peak-power value."""
    if not isinstance(forecast, dict):
        return 0.0

    for key in ("power_kw", "peak_power_kw", "forecast_power_kw", "power"):
        value = forecast.get(key)
        if isinstance(value, (int, float)):
            return float(value)

    power_forecast = forecast.get("power_forecast")
    if isinstance(power_forecast, list):
        values = [
            float(item["power_kw"])
            for item in power_forecast
            if isinstance(item, dict)
            and isinstance(item.get("power_kw"), (int, float))
        ]
        if values:
            return max(values)

    return 0.0


def get_forecast_peak_hour(forecast):
    """Safely extract a forecast peak hour."""
    if not isinstance(forecast, dict):
        return 0

    for key in ("hour", "peak_hour"):
        value = forecast.get(key)
        if isinstance(value, int):
            return value

    return 0


# =============================================================
# EXECUTIVE SUMMARY
# =============================================================

def create_executive_summary(result):
    """Create a compact operator-facing summary."""
    state_analysis = result.get("state_analysis", {})
    forecast = result.get("forecast", {})
    admission_summary = result.get("admission_summary", {})
    optimization_summary = result.get("optimization_summary", {})
    power_summary = result.get("power_summary", {})
    battery_result = result.get("battery_dispatch", {})
    decision_summary = result.get("decision_summary", {})

    return {
        "system_status": state_analysis.get("status", "UNKNOWN"),
        "primary_bottleneck": state_analysis.get("primary_bottleneck", "NONE"),
        "power_pressure_percent": state_analysis.get("power_pressure_percent", 0.0),
        "power_headroom_kw": state_analysis.get("power_headroom_kw", 0.0),
        "safe_power_limit_kw": result.get("safe_power_limit_kw", 0.0),
        "forecast_peak_power_kw": get_forecast_peak_power(forecast),
        "forecast_peak_hour": get_forecast_peak_hour(forecast),
        "scheduled_workloads": optimization_summary.get(
            "scheduled_count",
            optimization_summary.get("scheduled_workloads", 0),
        ),
        "unscheduled_workloads": optimization_summary.get(
            "unscheduled_count",
            optimization_summary.get("unscheduled_workloads", 0),
        ),
        "admit_workloads": admission_summary.get("admit", 0),
        "delay_workloads": admission_summary.get("delay", 0),
        "shift_workloads": admission_summary.get("shift", 0),
        "protect_workloads": admission_summary.get("protect", 0),
        "it_power_kw": power_summary.get("peak_it_power_kw", 0.0),
        "peak_facility_power_kw": power_summary.get("peak_facility_power_kw", 0.0),
        "cooling_overhead_kw": power_summary.get("cooling_overhead_kw", 0.0),
        "total_it_energy_kwh": power_summary.get("total_it_energy_kwh", 0.0),
        "total_facility_energy_kwh": power_summary.get(
            "total_facility_energy_kwh", 0.0
        ),
        "total_solar_energy_kwh": battery_result.get("total_solar_energy_kwh", 0.0),
        "total_battery_energy_kwh": battery_result.get("total_battery_energy_kwh", 0.0),
        "total_grid_energy_kwh": battery_result.get("total_grid_energy_kwh", 0.0),
        "final_battery_soc_percent": battery_result.get(
            "final_soc_percent",
            battery_result.get("final_battery_soc_percent", 0.0),
        ),
        "total_energy_cost": battery_result.get(
            "total_cost",
            battery_result.get("total_energy_cost", 0.0),
        ),
        "run_actions": decision_summary.get(
            "run", decision_summary.get("run_actions", 0)
        ),
        "shift_actions": decision_summary.get(
            "shift", decision_summary.get("shift_actions", 0)
        ),
        "deadline_protection_actions": decision_summary.get(
            "protect_deadline",
            decision_summary.get(
                "deadline_protection",
                decision_summary.get("deadline_protection_actions", 0),
            ),
        ),
    }


# =============================================================
# PRINT REPORT
# =============================================================

def print_poweros_report(result):
    """Print a readable PowerOS report."""
    summary = create_executive_summary(result)

    print("\n" + "=" * 70)
    print("ZYVARENTH POWEROS REPORT")
    print("=" * 70)

    print("\nSYSTEM STATUS")
    print("-" * 70)
    print(f"Status: {summary['system_status']}")
    print(f"Primary Bottleneck: {summary['primary_bottleneck']}")

    print("\nPOWER SAFETY")
    print("-" * 70)
    print(f"Power Pressure: {summary['power_pressure_percent']:.2f}%")
    print(f"Power Headroom: {summary['power_headroom_kw']:.2f} kW")
    print(f"Safe Power Limit: {summary['safe_power_limit_kw']:.2f} kW")

    print("\nFORECAST")
    print("-" * 70)
    print(f"Peak Forecast Power: {summary['forecast_peak_power_kw']:.2f} kW")
    print(f"Peak Forecast Hour: {summary['forecast_peak_hour']}")

    print("\nWORKLOAD ADMISSION")
    print("-" * 70)
    print(f"Admit: {summary['admit_workloads']}")
    print(f"Delay: {summary['delay_workloads']}")
    print(f"Shift: {summary['shift_workloads']}")
    print(f"Protect: {summary['protect_workloads']}")

    print("\nFACILITY POWER")
    print("-" * 70)
    print(f"Peak IT Power: {summary['it_power_kw']:.2f} kW")
    print(f"Peak Facility Power: {summary['peak_facility_power_kw']:.2f} kW")
    print(f"Cooling / Overhead: {summary['cooling_overhead_kw']:.2f} kW")
    print(f"IT Energy: {summary['total_it_energy_kwh']:.2f} kWh")
    print(f"Facility Energy: {summary['total_facility_energy_kwh']:.2f} kWh")

    print("\nOPTIMIZATION")
    print("-" * 70)
    print(f"Scheduled: {summary['scheduled_workloads']}")
    print(f"Unscheduled: {summary['unscheduled_workloads']}")

    print("\nENERGY MANAGEMENT")
    print("-" * 70)
    print(f"Solar Energy: {summary['total_solar_energy_kwh']:.2f} kWh")
    print(f"Battery Energy: {summary['total_battery_energy_kwh']:.2f} kWh")
    print(f"Grid Energy: {summary['total_grid_energy_kwh']:.2f} kWh")
    print(f"Final Battery SOC: {summary['final_battery_soc_percent']:.2f}%")
    print(f"Estimated Energy Cost: ₹{summary['total_energy_cost']:.2f}")

    print("\nFINAL DECISIONS")
    print("-" * 70)
    print(f"RUN: {summary['run_actions']}")
    print(f"SHIFT: {summary['shift_actions']}")
    print(f"DEADLINE PROTECTION: {summary['deadline_protection_actions']}")
    print("=" * 70)
