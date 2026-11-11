"""Generate ~3000 synthetic ServiceNow-style tickets.

Synthetic data ONLY -- no real employer or ticket data is used anywhere
in this project. Templates are hand-written realistic phrases; all
names, IDs and timestamps are generated with a fixed seed.
"""
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
N_TICKETS = 3000
SEED = 42

# (template, category, subcategory, assignment_group)
# ~40 hand-written templates across Incident / Request / Problem.
TEMPLATES = [
    ("VPN not connecting from home network", "Incident", "Network", "Network"),
    ("VPN keeps disconnecting every few minutes", "Incident", "Network", "Network"),
    ("Internet is down on the 3rd floor", "Incident", "Network", "Network"),
    ("Wi-Fi signal very weak in meeting room", "Incident", "Network", "Network"),
    ("Unable to access shared drive folder", "Incident", "Network", "Network"),
    ("Outlook not syncing new emails", "Incident", "Email", "Service Desk"),
    ("Laptop screen flickering after update", "Incident", "Hardware", "Hardware"),
    ("Laptop battery drains in under an hour", "Incident", "Hardware", "Hardware"),
    ("Printer not responding in accounts department", "Incident", "Hardware", "Hardware"),
    ("Keyboard keys not working on laptop", "Incident", "Hardware", "Hardware"),
    ("Password reset needed for SAP account", "Request", "Access", "Service Desk"),
    ("Password reset for email account", "Request", "Access", "Service Desk"),
    ("New joiner laptop and access setup", "Request", "Access", "Service Desk"),
    ("Request access to SAP MM purchase order module", "Request", "Access", "SAP Support"),
    ("SAP MM purchase order stuck in approval", "Incident", "SAP", "SAP Support"),
    ("SAP MM goods receipt posting error", "Incident", "SAP", "SAP Support"),
    ("SAP login failing with authorisation error", "Incident", "SAP", "SAP Support"),
    ("SAP invoice verification blocked by price variance", "Incident", "SAP", "SAP Support"),
    ("SAP material master data needs correction", "Request", "SAP", "SAP Support"),
    ("SAP vendor master update request", "Request", "SAP", "SAP Support"),
    ("Database query running very slow in production", "Incident", "Database", "Database"),
    ("Database connection timeout in reporting tool", "Incident", "Database", "Database"),
    ("Production database backup failed overnight", "Incident", "Database", "Database"),
    ("Disk space almost full on database server", "Incident", "Database", "Database"),
    ("Application crashing on startup after patch", "Incident", "Software", "Service Desk"),
    ("Software installation request for new tool", "Request", "Software", "Service Desk"),
    ("Teams call audio breaking up during meetings", "Incident", "Software", "Service Desk"),
    ("Urgent: production server down, users cannot log in", "Incident", "Software", "Service Desk"),
    ("Urgent: email server outage affecting all users", "Incident", "Email", "Service Desk"),
    ("Security alert: suspicious login attempts detected", "Incident", "Security", "Security"),
    ("Phishing email reported by multiple users", "Incident", "Security", "Security"),
    ("Antivirus blocking legitimate business application", "Incident", "Security", "Security"),
    ("Recurring VPN drops every morning for whole team", "Problem", "Network", "Network"),
    ("Repeated printer failures across the office", "Problem", "Hardware", "Hardware"),
    ("Recurring SAP posting errors at month end", "Problem", "SAP", "SAP Support"),
    ("Repeated database deadlocks during peak hours", "Problem", "Database", "Database"),
    ("Intermittent login failures for remote users", "Problem", "Access", "Service Desk"),
    ("Mobile app crashing for many users after release", "Problem", "Software", "Service Desk"),
    ("Request new monitor for workstation", "Request", "Hardware", "Hardware"),
    ("Request VPN access for new contractor", "Request", "Access", "Security"),
]

SUFFIXES = [
    "", "", "", " - user unable to work", " - affecting multiple users",
    " - reported twice this week", " - urgent, blocking daily work",
    " - happening since yesterday", " - please help asap",
]

PRIORITIES = ["P1", "P2", "P3", "P4"]
PRIORITY_W = [0.06, 0.22, 0.47, 0.25]
CHANNELS = ["Portal", "Email", "Phone", "Chat"]
SLA_HOURS = {"P1": 4, "P2": 8, "P3": 24, "P4": 72}
# Base breach probability by priority; groups / keywords / queue push it up.
BASE_BREACH = {"P1": 0.55, "P2": 0.35, "P3": 0.15, "P4": 0.07}
GROUP_BREACH_BOOST = {"SAP Support": 0.12, "Database": 0.10, "Security": 0.08,
                       "Network": 0.05, "Hardware": 0.0, "Service Desk": 0.0}
HIGH_RISK_WORDS = ["urgent", "outage", "down", "production", "stuck in approval",
                   "failed", "blocking", "cannot log in"]

GROUPS = [
    ("Network", "network@example.com", 5),
    ("Hardware", "hardware@example.com", 6),
    ("Service Desk", "servicedesk@example.com", 12),
    ("SAP Support", "sap-support@example.com", 4),
    ("Database", "dba@example.com", 3),
    ("Security", "security@example.com", 3),
]


def main() -> None:
    rng = random.Random(SEED)
    start = datetime(2026, 1, 1, 8, 0, 0)
    rows = []
    for i in range(1, N_TICKETS + 1):
        template, category, subcategory, group = rng.choice(TEMPLATES)
        description = template + rng.choice(SUFFIXES)
        priority = rng.choices(PRIORITIES, weights=PRIORITY_W)[0]
        channel = rng.choice(CHANNELS)
        opened = start + timedelta(minutes=rng.randint(0, 60 * 24 * 300))
        queue_hours = round(rng.expovariate(1 / 6), 1)  # avg ~6h in queue

        # --- SLA breach: learnable but not trivial -------------------------
        p = BASE_BREACH[priority] + GROUP_BREACH_BOOST.get(group, 0.0)
        low = description.lower()
        if any(w in low for w in HIGH_RISK_WORDS):
            p += 0.10
        if queue_hours > 12:
            p += 0.12
        elif queue_hours > 6:
            p += 0.05
        p = min(max(p, 0.02), 0.92)
        breach = 1 if rng.random() < p else 0

        # Resolution time consistent with the breach flag (mostly).
        sla = SLA_HOURS[priority]
        if breach:
            resolution_hours = round(rng.uniform(sla * 1.05, sla * 3.0), 1)
        else:
            resolution_hours = round(rng.uniform(0.5, sla * 0.95), 1)
        resolved = opened + timedelta(hours=resolution_hours)

        rows.append({
            "ticket_id": f"INC{i:05d}",
            "short_description": description,
            "category": category,
            "subcategory": subcategory,
            "priority": priority,
            "channel": channel,
            "assignment_group": group,
            "opened_at": opened.strftime("%Y-%m-%d %H:%M:%S"),
            "resolved_at": resolved.strftime("%Y-%m-%d %H:%M:%S"),
            "resolution_hours": resolution_hours,
            "queue_hours": queue_hours,
            "sla_breach": breach,
        })

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(DATA_DIR / "tickets.csv", index=False)
    pd.DataFrame(GROUPS, columns=["group_name", "contact_email", "member_count"]
                 ).to_csv(DATA_DIR / "assignment_groups.csv", index=False)
    pd.DataFrame(
        [{"priority": k, "target_hours": v} for k, v in SLA_HOURS.items()]
    ).to_csv(DATA_DIR / "sla_policy.csv", index=False)
    print(f"Wrote {len(df)} tickets to {DATA_DIR / 'tickets.csv'}")
    print(f"Breach rate: {df['sla_breach'].mean():.3f}")
    print(df.groupby("priority")["sla_breach"].mean().round(3).to_dict())


if __name__ == "__main__":
    main()
