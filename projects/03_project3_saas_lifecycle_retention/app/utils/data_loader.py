from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def load_tables(data_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    """Load the deterministic lifecycle source tables."""
    source = data_dir or DEFAULT_DATA_DIR
    tables = {
        "organizations": pd.read_csv(source / "organizations.csv", parse_dates=["created_at"]),
        "users": pd.read_csv(source / "users.csv", parse_dates=["signup_timestamp"]),
        "event_logs": pd.read_csv(source / "event_logs.csv", parse_dates=["event_timestamp"]),
        "subscriptions": pd.read_csv(source / "subscriptions.csv", parse_dates=["start_date", "end_date"]),
        "experiment_assignments": pd.read_csv(source / "experiment_assignments.csv", parse_dates=["assigned_at"]),
    }
    return tables
