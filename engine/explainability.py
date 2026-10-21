import pandas as pd


# ============================================================
# ZYVARENTH POWEROS
# EXPLAINABILITY ENGINE
# ============================================================


def explain_schedule(
    schedule: pd.DataFrame,
    electricity_prices: list,
    grid_capacity: list,
    solar_power: list,
    power_limit_kw: float = 70.0,
) -> pd.DataFrame:
    """
    Explain why PowerOS selected the start time
    for each AI workload.
    """

    explanations = []

    for _, job in schedule.iterrows():

        job_id = int(job["job_id"])
        start_hour = int(job["start_hour"])
        duration = int(job["duration_hours"])
        power = float(job["power_kw"])
        deadline = int(job["deadline"])
        priority = str(job["priority"])

        # ----------------------------------------------------
        # Unscheduled workload
        # ----------------------------------------------------

        if start_hour < 0:

            explanations.append({
                "job_id": job_id,
                "start_hour": start_hour,
                "priority": priority,
                "deadline": deadline,
                "decision": "WAIT",
                "reason": "No feasible power/GPU slot",
            })

            continue

        # ----------------------------------------------------
        # Analyze selected hours
        # ----------------------------------------------------

        selected_hours = list(
            range(
                start_hour,
                min(
                    start_hour + duration,
                    24
                )
            )
        )

        prices = [
            float(electricity_prices[h])
            for h in selected_hours
        ]

        solar_values = [
            float(solar_power[h])
            for h in selected_hours
        ]

        grid_values = [
            float(grid_capacity[h])
            for h in selected_hours
        ]

        average_price = (
            sum(prices) / len(prices)
            if prices
            else 0.0
        )

        average_solar = (
            sum(solar_values) / len(solar_values)
            if solar_values
            else 0.0
        )

        minimum_grid = (
            min(grid_values)
            if grid_values
            else 0.0
        )

        finish_hour = (
            start_hour + duration
        )

        deadline_slack = (
            deadline - finish_hour
        )

        # ----------------------------------------------------
        # Determine primary reason
        # ----------------------------------------------------

        if average_solar > 0:

            reason = (
                "Uses available solar generation"
            )

        elif average_price <= 6.0:

            reason = (
                "Scheduled during low electricity price"
            )

        elif deadline_slack <= 2:

            reason = (
                "Moved earlier to protect deadline"
            )

        elif minimum_grid < power_limit_kw:

            reason = (
                "Fits within available grid capacity"
            )

        else:

            reason = (
                "Best feasible power/GPU schedule"
            )

        # ----------------------------------------------------
        # Decision classification
        # ----------------------------------------------------

        if start_hour == 0:

            decision = "RUN"

        else:

            decision = "SHIFTED"

        explanations.append({
            "job_id": job_id,
            "start_hour": start_hour,
            "duration_hours": duration,
            "priority": priority,
            "deadline": deadline,
            "finish_hour": finish_hour,
            "deadline_slack": deadline_slack,
            "average_price": round(
                average_price,
                2
            ),
            "average_solar_kw": round(
                average_solar,
                2
            ),
            "minimum_grid_capacity_kw": round(
                minimum_grid,
                2
            ),
            "decision": decision,
            "reason": reason,
        })

    return pd.DataFrame(
        explanations
    )


# ============================================================
# SUMMARY
# ============================================================

def summarize_explanations(
    explanations: pd.DataFrame,
) -> dict:
    """
    Create a high-level summary of PowerOS decisions.
    """

    if explanations.empty:

        return {
            "total_jobs": 0,
            "shifted_jobs": 0,
            "waiting_jobs": 0,
            "solar_optimized_jobs": 0,
            "low_price_jobs": 0,
        }

    total_jobs = len(
        explanations
    )

    shifted_jobs = len(
        explanations[
            explanations["decision"]
            == "SHIFTED"
        ]
    )

    waiting_jobs = len(
        explanations[
            explanations["decision"]
            == "WAIT"
        ]
    )

    solar_optimized_jobs = len(
        explanations[
            explanations["reason"].str.contains(
                "solar",
                case=False,
                na=False
            )
        ]
    )

    low_price_jobs = len(
        explanations[
            explanations["reason"].str.contains(
                "low electricity",
                case=False,
                na=False
            )
        ]
    )

    return {
        "total_jobs": total_jobs,
        "shifted_jobs": shifted_jobs,
        "waiting_jobs": waiting_jobs,
        "solar_optimized_jobs":
            solar_optimized_jobs,
        "low_price_jobs":
            low_price_jobs,
    }


# ============================================================
# DISPLAY
# ============================================================

def print_explainability_report(
    explanations: pd.DataFrame,
    summary: dict,
):
    """
    Print a clean PowerOS decision report.
    """

    print("\n")
    print("=" * 60)
    print("        POWEROS DECISION EXPLANATION")
    print("=" * 60)

    print(
        f"\nTotal workloads       : "
        f"{summary['total_jobs']}"
    )

    print(
        f"Workloads shifted     : "
        f"{summary['shifted_jobs']}"
    )

    print(
        f"Workloads waiting     : "
        f"{summary['waiting_jobs']}"
    )

    print(
        f"Solar-optimized jobs  : "
        f"{summary['solar_optimized_jobs']}"
    )

    print(
        f"Low-price jobs        : "
        f"{summary['low_price_jobs']}"
    )

    print("\nTOP POWEROS DECISIONS")
    print("-" * 60)

    if explanations.empty:

        print("No scheduling decisions available.")
        return

    display_columns = [
        "job_id",
        "start_hour",
        "priority",
        "deadline",
        "decision",
        "reason",
    ]

    available_columns = [
        column
        for column in display_columns
        if column in explanations.columns
    ]

    print(
        explanations[
            available_columns
        ].head(20).to_string(
            index=False
        )
    )

    print("=" * 60)