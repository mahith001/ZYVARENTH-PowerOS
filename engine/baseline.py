import pandas as pd


def create_baseline_schedule(jobs: pd.DataFrame) -> pd.DataFrame:
    """
    Simple baseline:
    every job starts at hour 0.
    This is intentionally inefficient.
    """

    schedule = jobs.copy()

    schedule["start_hour"] = 0

    return schedule