"""Load generated CSVs into SQLite (demo DB) and create analytical views.

SQLite is used for the runnable demo (stdlib sqlite3). The same schema
is also provided as MySQL-compatible DDL in schema.sql at the repo root.
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "tickets.db"

VIEWS = {
    "vw_mttr_by_group": """
        CREATE VIEW IF NOT EXISTS vw_mttr_by_group AS
        SELECT assignment_group,
               COUNT(*) AS ticket_count,
               ROUND(AVG(resolution_hours), 2) AS avg_resolution_hours,
               ROUND(AVG(queue_hours), 2) AS avg_queue_hours,
               ROUND(100.0 * SUM(sla_breach) / COUNT(*), 1) AS breach_rate_pct
        FROM tickets GROUP BY assignment_group
    """,
    "vw_breach_rate_by_priority": """
        CREATE VIEW IF NOT EXISTS vw_breach_rate_by_priority AS
        SELECT priority, category,
               COUNT(*) AS ticket_count,
               ROUND(100.0 * SUM(sla_breach) / COUNT(*), 1) AS breach_rate_pct,
               ROUND(AVG(resolution_hours), 2) AS avg_resolution_hours
        FROM tickets GROUP BY priority, category
    """,
    "vw_breach_trend_monthly": """
        CREATE VIEW IF NOT EXISTS vw_breach_trend_monthly AS
        SELECT substr(opened_at, 1, 7) AS month,
               COUNT(*) AS ticket_count,
               ROUND(100.0 * SUM(sla_breach) / COUNT(*), 1) AS breach_rate_pct
        FROM tickets GROUP BY substr(opened_at, 1, 7)
    """,
}


def main() -> None:
    tickets = pd.read_csv(DATA_DIR / "tickets.csv")
    groups = pd.read_csv(DATA_DIR / "assignment_groups.csv")
    policy = pd.read_csv(DATA_DIR / "sla_policy.csv")

    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    tickets.to_sql("tickets", conn, index=False)
    groups.to_sql("assignment_groups", conn, index=False)
    policy.to_sql("sla_policy", conn, index=False)
    for name, sql in VIEWS.items():
        conn.execute(sql)
        print(f"Created view {name}")
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    conn.close()
    print(f"Loaded {n} tickets into {DB_PATH}")


if __name__ == "__main__":
    main()
