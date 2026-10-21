from typing import Dict


# ============================================================
# SAFETY LIMITS
# ============================================================

DEFAULT_RESERVE_PERCENT = 15.0
DEFAULT_WARNING_PERCENT = 80.0
DEFAULT_CRITICAL_PERCENT = 95.0


# ============================================================
# SAFE POWER LIMIT
# ============================================================

def calculate_safe_power_limit(
    available_power_kw: float,
    reserve_percent: float = DEFAULT_RESERVE_PERCENT,
) -> float:

    if available_power_kw < 0:
        raise ValueError(
            "available_power_kw cannot be negative"
        )

    reserve_percent = max(
        0.0,
        min(100.0, reserve_percent),
    )

    return (
        available_power_kw
        * (1.0 - reserve_percent / 100.0)
    )


# ============================================================
# UNCERTAINTY BUFFER
# ============================================================

def calculate_uncertainty_buffer(
    forecast_power_kw: float,
    uncertainty_percent: float,
) -> float:

    if forecast_power_kw < 0:
        raise ValueError(
            "forecast_power_kw cannot be negative"
        )

    uncertainty_percent = max(
        0.0,
        min(100.0, uncertainty_percent),
    )

    return (
        forecast_power_kw
        * uncertainty_percent
        / 100.0
    )


# ============================================================
# RISK CLASSIFICATION
# ============================================================

def classify_power_risk(
    forecast_power_kw: float,
    safe_power_limit_kw: float,
) -> str:

    if safe_power_limit_kw <= 0:

        return "CRITICAL"

    utilization_percent = (
        forecast_power_kw
        / safe_power_limit_kw
    ) * 100.0

    if utilization_percent >= 100:

        return "CRITICAL"

    if utilization_percent >= 90:

        return "HIGH"

    if utilization_percent >= 75:

        return "MEDIUM"

    return "LOW"


# ============================================================
# WORKLOAD RISK
# ============================================================

def classify_workload_risk(
    priority: str,
    deadline_hour: int,
    current_hour: int = 0,
) -> str:

    remaining_hours = (
        deadline_hour
        - current_hour
    )

    if priority == "HIGH":

        if remaining_hours <= 2:
            return "CRITICAL"

        if remaining_hours <= 6:
            return "HIGH"

        return "MEDIUM"

    if priority == "MEDIUM":

        if remaining_hours <= 2:
            return "HIGH"

        return "MEDIUM"

    if remaining_hours <= 2:

        return "MEDIUM"

    return "LOW"


# ============================================================
# SAFETY ANALYSIS
# ============================================================

def analyze_safety(
    available_power_kw: float,
    forecast_peak_power_kw: float,
    uncertainty_percent: float = 10.0,
    reserve_percent: float = DEFAULT_RESERVE_PERCENT,
) -> Dict:

    safe_power_limit_kw = (
        calculate_safe_power_limit(
            available_power_kw,
            reserve_percent,
        )
    )

    uncertainty_buffer_kw = (
        calculate_uncertainty_buffer(
            forecast_peak_power_kw,
            uncertainty_percent,
        )
    )

    protected_forecast_kw = (
        forecast_peak_power_kw
        + uncertainty_buffer_kw
    )

    risk = classify_power_risk(
        protected_forecast_kw,
        safe_power_limit_kw,
    )

    remaining_headroom_kw = (
        safe_power_limit_kw
        - protected_forecast_kw
    )

    if remaining_headroom_kw < 0:

        action = "REDUCE_OR_SHIFT_LOAD"

    elif risk in ("HIGH", "MEDIUM"):

        action = "LIMIT_NEW_LOAD"

    else:

        action = "NORMAL_OPERATION"

    return {
        "available_power_kw": (
            available_power_kw
        ),

        "reserve_percent": (
            reserve_percent
        ),

        "safe_power_limit_kw": (
            safe_power_limit_kw
        ),

        "forecast_peak_power_kw": (
            forecast_peak_power_kw
        ),

        "uncertainty_percent": (
            uncertainty_percent
        ),

        "uncertainty_buffer_kw": (
            uncertainty_buffer_kw
        ),

        "protected_forecast_kw": (
            protected_forecast_kw
        ),

        "remaining_headroom_kw": (
            remaining_headroom_kw
        ),

        "risk": risk,

        "action": action,
    }


# ============================================================
# REPORT
# ============================================================

def print_safety_report(
    safety: Dict,
):

    print()
    print("=" * 70)
    print("POWEROS SAFETY ANALYSIS")
    print("=" * 70)

    print()

    print(
        f"Available power: "
        f"{safety['available_power_kw']:.2f} kW"
    )

    print(
        f"Reserve: "
        f"{safety['reserve_percent']:.1f}%"
    )

    print(
        f"Safe power limit: "
        f"{safety['safe_power_limit_kw']:.2f} kW"
    )

    print(
        f"Forecast peak: "
        f"{safety['forecast_peak_power_kw']:.2f} kW"
    )

    print(
        f"Uncertainty buffer: "
        f"{safety['uncertainty_buffer_kw']:.2f} kW"
    )

    print(
        f"Protected forecast: "
        f"{safety['protected_forecast_kw']:.2f} kW"
    )

    print(
        f"Remaining headroom: "
        f"{safety['remaining_headroom_kw']:.2f} kW"
    )

    print(
        f"Risk: "
        f"{safety['risk']}"
    )

    print(
        f"Recommended action: "
        f"{safety['action']}"
    )

    print()
    print("=" * 70)