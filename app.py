"""Streamlit dashboard for the ServiceNow SLA Risk Predictor.

Works from the CSVs in data/ if the .db / model files are missing, and
tells the user to run the pipeline first when they are absent.
"""
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
MODEL_PATH = ROOT / "models" / "sla_breach_model.joblib"


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "tickets.csv", parse_dates=["opened_at"])
    df["month"] = df["opened_at"].dt.to_period("M").astype(str)
    return df


def load_model():
    if MODEL_PATH.exists():
        return joblib.load(MODEL_PATH)
    return None


def make_text(row) -> str:
    return (f"{row['short_description']} {row['category']} "
            f"{row['subcategory']} {row['priority']} "
            f"{row['assignment_group']} {row['channel']}")


def main() -> None:
    st.set_page_config(page_title="ServiceNow SLA Risk Predictor", layout="wide")
    st.title("ServiceNow SLA Risk Predictor")
    st.caption("Synthetic data only — no real employer or ticket data is used.")

    try:
        df = load_data()
    except FileNotFoundError:
        st.error("No data found. Run the pipeline first:\n\n"
                 "python src/generate_data.py\npython src/load_to_db.py\npython src/train.py")
        return

    model = load_model()
    if model is None:
        st.warning("Model file not found (models/sla_breach_model.joblib). "
                   "Run `python src/train.py` to enable risk scoring and triage.")

    # --- Filters -----------------------------------------------------------
    st.sidebar.header("Filters")
    priorities = st.sidebar.multiselect("Priority", sorted(df["priority"].unique()),
                                        default=sorted(df["priority"].unique()))
    groups = st.sidebar.multiselect("Assignment group", sorted(df["assignment_group"].unique()),
                                    default=sorted(df["assignment_group"].unique()))
    fdf = df[df["priority"].isin(priorities) & df["assignment_group"].isin(groups)]
    if fdf.empty:
        st.warning("No tickets match the selected filters.")
        return

    # --- KPI cards ---------------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tickets", len(fdf))
    c2.metric("SLA breach rate", f"{100 * fdf['sla_breach'].mean():.1f}%")
    c3.metric("Avg resolution (h)", f"{fdf['resolution_hours'].mean():.1f}")
    c4.metric("Avg queue (h)", f"{fdf['queue_hours'].mean():.1f}")

    # --- Charts ------------------------------------------------------------
    st.subheader("Breach rate by priority")
    st.bar_chart(fdf.groupby("priority")["sla_breach"].mean() * 100)
    st.subheader("Breach rate trend (monthly)")
    st.line_chart(fdf.groupby("month")["sla_breach"].mean() * 100)
    st.subheader("MTTR by assignment group (avg resolution hours)")
    st.bar_chart(fdf.groupby("assignment_group")["resolution_hours"].mean())

    # --- Breach-risk queue -------------------------------------------------
    st.subheader("Breach-risk queue")
    if model is not None:
        scored = fdf.copy()
        scored["risk"] = model.predict_proba(
            scored.apply(make_text, axis=1))[:, 1]
        scored = scored.sort_values("risk", ascending=False)
        st.dataframe(scored[["ticket_id", "short_description", "priority",
                             "assignment_group", "resolution_hours",
                             "risk"]].head(50), use_container_width=True)
        st.subheader("Actionable recommendations")
        top = scored.head(10)
        for _, r in top.iterrows():
            st.write(f"- **{r['ticket_id']}** ({r['priority']}, {r['assignment_group']}, "
                     f"risk {r['risk']:.0%}): escalate — reassign or add staff; "
                     f"target resolution within SLA, currently {r['resolution_hours']:.1f}h.")
    else:
        st.info("Risk scoring unavailable — run `python src/train.py` first.")

    # --- Triage demo -------------------------------------------------------
    st.subheader("Live triage demo")
    text = st.text_area("Ticket description",
                        "SAP MM purchase order stuck in approval, urgent")
    col_a, col_b = st.columns(2)
    cat = col_a.selectbox("Category", ["Incident", "Request", "Problem"])
    prio = col_b.selectbox("Priority", ["P1", "P2", "P3", "P4"])
    group = st.selectbox("Assignment group",
                         sorted(df["assignment_group"].unique()))
    if st.button("Predict breach risk"):
        if model is None:
            st.error("Model file missing — run `python src/train.py` first.")
        else:
            sample = f"{text} {cat} {prio} {group} Portal"
            prob = float(model.predict_proba([sample])[0][1])
            st.metric("Predicted SLA breach risk", f"{prob:.0%}")
            if prob >= 0.6:
                st.error("High risk — escalate immediately and assign a senior engineer.")
            elif prob >= 0.3:
                st.warning("Medium risk — monitor closely and set a reminder before the SLA deadline.")
            else:
                st.success("Low risk — standard queue handling should be fine.")


if __name__ == "__main__":
    main()
