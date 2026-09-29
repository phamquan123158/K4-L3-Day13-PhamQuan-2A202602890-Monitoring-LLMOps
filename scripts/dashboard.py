from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
import yaml


ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "data" / "logs.jsonl"
CONFIG_PATH = ROOT / "config" / "dashboard.yaml"


def load_records() -> list[dict[str, Any]]:
    if not LOG_PATH.exists():
        return []

    records = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)

    if not records:
        return []

    frame = pd.DataFrame(records)
    if "ts" not in frame:
        return []
    frame["ts"] = pd.to_datetime(frame["ts"], utc=True, errors="coerce")
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=60)
    frame = frame.loc[frame["ts"].notna() & (frame["ts"] >= cutoff)].copy()
    if frame.empty:
        return []
    frame["_minute"] = frame["ts"].dt.floor("min")
    return frame.to_dict(orient="records")


def numeric(frame: pd.DataFrame, field: str) -> pd.Series:
    if field not in frame:
        return pd.Series(dtype="float64")
    return pd.to_numeric(frame[field], errors="coerce")


def panel_heading(panel: dict[str, Any]) -> None:
    threshold = panel["threshold"]
    operator = "≤" if threshold["operator"] == "lte" else "≥"
    st.subheader(panel["title"])
    st.caption(
        f"{panel['unit']} · threshold {threshold['aggregation']} "
        f"{operator} {threshold['value']}"
    )


def render_dashboard() -> None:
    st.set_page_config(page_title="Day 13 Monitoring & LLMOps", layout="wide")
    render_dashboard_content()


@st.fragment(run_every="30s")
def render_dashboard_content() -> None:
    dashboard = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))["dashboard"]
    panels = {panel["id"]: panel for panel in dashboard["panels"]}

    st.title(dashboard["title"])
    st.caption(
        f"Last {dashboard['time_range_minutes']} minutes · "
        f"auto-refresh {dashboard['refresh_seconds']}s · source: data/logs.jsonl"
    )
    if st.button("Refresh", type="primary"):
        st.rerun(scope="fragment")

    records = load_records()
    if not records:
        st.info("No valid log records in the last 60 minutes. Run the API and load test first.")
        return

    frame = pd.DataFrame(records)
    events = frame.get("event", pd.Series(index=frame.index, dtype="object"))
    response_rows = frame.loc[events == "response_sent"].copy()
    request_rows = frame.loc[events == "request_received"].copy()
    failure_rows = frame.loc[events == "request_failed"].copy()

    left, right = st.columns(2)
    with left:
        panel_heading(panels["latency"])
        latency = response_rows.assign(
            latency_ms=numeric(response_rows, "latency_ms"),
            ttft_ms=numeric(response_rows, "ttft_ms"),
        )
        if not latency.empty:
            latency_chart = latency.groupby("_minute").agg(
                p50_ms=("latency_ms", "median"),
                p95_ms=("latency_ms", lambda values: values.quantile(0.95)),
                p99_ms=("latency_ms", lambda values: values.quantile(0.99)),
                ttft_p95_ms=("ttft_ms", lambda values: values.quantile(0.95)),
            )
            st.line_chart(latency_chart)
        else:
            st.caption("No completed requests in this time window.")

    with right:
        panel_heading(panels["traffic"])
        if not request_rows.empty:
            traffic = request_rows.groupby("_minute").size().rename("requests/minute")
            st.bar_chart(traffic)
            st.metric("Requests", len(request_rows))
        else:
            st.caption("No requests in this time window.")

    left, right = st.columns(2)
    with left:
        panel_heading(panels["errors"])
        request_count = len(request_rows)
        error_rate = len(failure_rows) * 100 / request_count if request_count else 0
        tool_rows = frame.loc[frame.get("tool_success", pd.Series(index=frame.index)).notna()]
        tool_success = (
            tool_rows["tool_success"].astype(bool).mean() * 100 if not tool_rows.empty else 0
        )
        error_metrics = pd.DataFrame(
            {"rate_percent": [error_rate, tool_success]},
            index=["Request errors", "Retrieval success"],
        )
        st.bar_chart(error_metrics)
        st.caption(f"Failed requests: {len(failure_rows)} · retrieval success: {tool_success:.1f}%")

    with right:
        panel_heading(panels["cost"])
        cost = response_rows.assign(cost_usd=numeric(response_rows, "cost_usd"))
        if not cost.empty:
            st.area_chart(cost.groupby("_minute")["cost_usd"].sum().rename("USD/minute"))
            st.metric("Total cost", f"${cost['cost_usd'].sum():.4f}")
        else:
            st.caption("No cost records in this time window.")

    left, right = st.columns(2)
    with left:
        panel_heading(panels["tokens"])
        tokens = response_rows.assign(
            tokens_in=numeric(response_rows, "tokens_in"),
            tokens_out=numeric(response_rows, "tokens_out"),
        )
        if not tokens.empty:
            token_chart = tokens.groupby("_minute")[["tokens_in", "tokens_out"]].sum()
            st.bar_chart(token_chart)
        else:
            st.caption("No token records in this time window.")

    with right:
        panel_heading(panels["quality"])
        quality = response_rows.assign(quality_score=numeric(response_rows, "quality_score"))
        if not quality.empty:
            st.line_chart(quality.groupby("_minute")["quality_score"].mean())
            st.metric("Mean quality", f"{quality['quality_score'].mean():.2f}")
        else:
            st.caption("No quality records in this time window.")


if __name__ == "__main__":
    render_dashboard()