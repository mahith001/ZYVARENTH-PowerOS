from typing import Dict

from poweros.intelligence.safety_engine import (
    classify_workload_risk,
)


# ============================================================
# ADMISSION ACTIONS
# ============================================================

ADMIT = "ADMIT"
DELAY = "DELAY"
SHIFT = "SHIFT"
PROTECT = "PROTECT"


# ============================================================
# WORKLOAD ADMISSION
# ============================================================

def evaluate_workload_admission(
    priority: str,
    deadline_hour: int,
    current_hour: int,
    required_power_kw: float,
    available_safe_power_kw: float,
) -> Dict:
    """
    Decide whether a workload should be admitted,
    delayed, shifted, or protected.
    """

    workload_risk = classify_workload_risk(
        priority=priority,
        deadline_hour=deadline_hour,
        current_hour=current_hour,
    )

    power_available = (
        required_power_kw
        <= available_safe_power_kw
    )

    # --------------------------------------------------------
    # CRITICAL WORKLOAD
    # --------------------------------------------------------

    if workload_risk == "CRITICAL":

        if power_available:

            action = PROTECT
            reason = (
                "Critical workload has "
                "sufficient safe power."
            )

        else:

            action = PROTECT
            reason = (
                "Critical workload requires "
                "deadline protection."
            )

    # --------------------------------------------------------
    # HIGH RISK
    # --------------------------------------------------------

    elif workload_risk == "HIGH":

        if power_available:

            action = ADMIT
            reason = (
                "High-priority workload "
                "can run safely."
            )

        else:

            action = SHIFT
            reason = (
                "Insufficient safe power; "
                "shift workload to a safer window."
            )

    # --------------------------------------------------------
    # MEDIUM RISK
    # --------------------------------------------------------

    elif workload_risk == "MEDIUM":

        if power_available:

            action = ADMIT
            reason = (
                "Workload can run within "
                "the safe power limit."
            )

        else:

            action = DELAY
            reason = (
                "Workload can wait for "
                "additional power headroom."
            )

    # --------------------------------------------------------
    # LOW RISK
    # --------------------------------------------------------

    else:

        if power_available:

            action = ADMIT
            reason = (
                "Low-risk workload can run."
            )

        else:

            action = DELAY
            reason = (
                "Low-priority workload "
                "should be delayed."
            )

    return {
        "priority": priority,
        "deadline_hour": deadline_hour,
        "current_hour": current_hour,
        "required_power_kw": required_power_kw,
        "available_safe_power_kw": (
            available_safe_power_kw
        ),
        "workload_risk": workload_risk,
        "action": action,
        "reason": reason,
    }


# ============================================================
# BATCH ADMISSION
# ============================================================

def evaluate_workloads(
    workloads,
    current_hour: int,
    available_safe_power_kw: float,
) -> list:

    results = []

    for workload in workloads:

        required_power_kw = (
            workload.gpu_required
            * 0.7
        )

        result = evaluate_workload_admission(
            priority=workload.priority,
            deadline_hour=workload.deadline_hour,
            current_hour=current_hour,
            required_power_kw=required_power_kw,
            available_safe_power_kw=(
                available_safe_power_kw
            ),
        )

        result["workload_id"] = (
            workload.workload_id
        )

        results.append(
            result
        )

    return results


# ============================================================
# SUMMARY
# ============================================================

def summarize_admission(
    results,
) -> Dict:

    summary = {
        "total": len(results),
        "admit": 0,
        "delay": 0,
        "shift": 0,
        "protect": 0,
    }

    for result in results:

        action = result["action"]

        if action == ADMIT:
            summary["admit"] += 1

        elif action == DELAY:
            summary["delay"] += 1

        elif action == SHIFT:
            summary["shift"] += 1

        elif action == PROTECT:
            summary["protect"] += 1

    return summary


# ============================================================
# REPORT
# ============================================================

def print_admission_report(
    results,
    summary,
):

    print()
    print("=" * 70)
    print("POWEROS WORKLOAD ADMISSION CONTROL")
    print("=" * 70)

    print()

    for result in results:

        print(
            f"{result.get('workload_id', 'UNKNOWN')} | "
            f"Priority: {result['priority']} | "
            f"Risk: {result['workload_risk']} | "
            f"Action: {result['action']}"
        )

        print(
            f"  Required: "
            f"{result['required_power_kw']:.2f} kW | "
            f"Safe available: "
            f"{result['available_safe_power_kw']:.2f} kW"
        )

        print(
            f"  Reason: "
            f"{result['reason']}"
        )

    print()

    print(
        f"ADMIT: {summary['admit']}"
    )

    print(
        f"DELAY: {summary['delay']}"
    )

    print(
        f"SHIFT: {summary['shift']}"
    )

    print(
        f"PROTECT: {summary['protect']}"
    )

    print()
    print("=" * 70)