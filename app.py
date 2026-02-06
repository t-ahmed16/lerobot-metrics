from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_PATH = Path("data/weekly_snapshots.csv")

st.set_page_config(page_title="LeRobot Metrics Dashboard", layout="wide")
st.title("LeRobot Ecosystem Weekly Metrics")
st.caption("Source: GitHub API + Hugging Face API snapshots")

if not DATA_PATH.exists():
    st.warning("No snapshots yet. Run: `python scripts/fetch_snapshot.py`")
    st.stop()

try:
    df = pd.read_csv(DATA_PATH)
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not read {DATA_PATH}: {exc}")
    st.stop()

if df.empty:
    st.warning("Snapshot file is empty. Add one snapshot first.")
    st.stop()

for col in [
    "lerobot_github_stars",
    "hf_lerobot_dataset_count",
    "hf_unique_dataset_uploaders",
    "github_topic_robotics_repo_count",
    "github_topic_lerobot_repo_count",
]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["snapshot_date"] = pd.to_datetime(df["snapshot_date"], errors="coerce")
df = df.dropna(subset=["snapshot_date"]).sort_values("snapshot_date")

latest = df.iloc[-1]

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("LeRobot Stars", int(latest["lerobot_github_stars"]))
k2.metric("HF LeRobot Datasets", int(latest["hf_lerobot_dataset_count"]))
k3.metric("Unique HF Uploaders", int(latest["hf_unique_dataset_uploaders"]))
k4.metric("GitHub topic:robotics repos", int(latest["github_topic_robotics_repo_count"]))
k5.metric("GitHub topic:lerobot repos", int(latest["github_topic_lerobot_repo_count"]))

plot_df = df[[
    "snapshot_date",
    "lerobot_github_stars",
    "hf_lerobot_dataset_count",
    "hf_unique_dataset_uploaders",
    "github_topic_robotics_repo_count",
    "github_topic_lerobot_repo_count",
]].rename(
    columns={
        "snapshot_date": "Date",
        "lerobot_github_stars": "LeRobot GitHub Stars",
        "hf_lerobot_dataset_count": "HF LeRobot Dataset Count",
        "hf_unique_dataset_uploaders": "HF Unique Dataset Uploaders",
        "github_topic_robotics_repo_count": "GitHub topic:robotics repo count",
        "github_topic_lerobot_repo_count": "GitHub topic:lerobot repo count",
    }
)

long_df = plot_df.melt(id_vars="Date", var_name="Metric", value_name="Value")

fig = px.line(long_df, x="Date", y="Value", color="Metric", markers=True)
fig.update_layout(height=520, margin=dict(l=10, r=10, t=20, b=10))
st.plotly_chart(fig, use_container_width=True)

st.subheader("Raw Snapshot Data")
st.dataframe(df, use_container_width=True)
