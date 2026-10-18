"""Prism News API Playground: try the live news API with your own key. MIT licence.

The key is read from a password field, sent only to radar-api.fliarbi.com in the X-API-Key header for the
request you make, and never written to disk, logs, query parameters or browser storage.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(page_title="Prism News API Playground", page_icon="🧪", layout="wide")

API_BASE = "https://radar-api.fliarbi.com/news"
API_REPO = "https://github.com/fliarbi/prism-news-api"
GUIDE = "https://github.com/fliarbi/prism-news-api/blob/main/docs/USER_GUIDE.md"
KEY_PAGE = "https://fliarbi.com/radar/dashboard?tab=radarapi"
HUB = "https://fliarbi.github.io/news-datasets/"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
TONE = {"negative": "#e34948", "neutral": "#9a9890", "positive": "#1baf7a"}
ENDPOINTS = {
    "overview": "Volume, tone split and share of critical stories for a subject.",
    "trends": "Volume time series (daily, weekly or monthly) with critical and tone counts.",
    "geography": "Top countries where the subject is reported (1-5).",
    "themes": "Top themes inside the subject (1-5), with lift and change vs the previous period.",
    "headlines": "Matching headlines with publisher, date, tone and priority.",
}

st.title("🧪 Prism News API Playground")
st.markdown(
    f"Try the [Prism News API]({API_REPO}) (historical and real-time news, 2019 to now) without writing code. "
    "Paste your key, pick an endpoint, set the filters and run. You see the chart and the exact JSON the API "
    "returns, plus the matching curl and Python call to copy.")

with st.expander("How to get a key (free, about a minute)", expanded=False):
    st.markdown(
        f"1. Sign in to the [Fliar dashboard]({KEY_PAGE}) and open **API keys**.\n"
        "2. Choose **Create or manage API keys**, pick **News only** or **All data**, and create a key. "
        "It starts with `rdr_`.\n"
        "3. The Free plan gives 1,000 requests a month over the last 365 days; paid plans add full history. "
        f"See [plans and the user guide]({GUIDE}).\n\n"
        "**Your key is never stored.** This app runs entirely in your browser: the key stays in this tab, is "
        "sent only to `radar-api.fliarbi.com` for the request you run, and is gone when you close the tab.")

key = st.text_input("API key", type="password", placeholder="rdr_…",
                    help="Used for your requests only; never saved or logged by this app.")

endpoint = st.radio("Endpoint", list(ENDPOINTS), horizontal=True, format_func=lambda e: f"/v1/{e}")
st.caption(ENDPOINTS[endpoint])

with st.form("params"):
    c1, c2, c3 = st.columns([2, 1, 1])
    q = c1.text_input("Query (q)", value="heatwave", help="A subject, as you would type it in search.")
    today = dt.date.today()
    since = c2.date_input("Since", value=today - dt.timedelta(days=180))
    until = c3.date_input("Until", value=today)
    c4, c5, c6 = st.columns(3)
    country = c4.text_input("Country (optional)", placeholder="e.g. india, united states")
    sentiment = c5.selectbox("Tone filter", ["any", "negative", "neutral", "positive"])
    priority_min = c6.slider("Minimum priority (1-9)", 1, 9, 1)
    extra = {}
    if endpoint == "trends":
        extra["granularity"] = st.selectbox("Granularity", ["monthly", "weekly", "daily"])
    if endpoint in ("geography", "themes"):
        extra["limit"] = st.slider("Results", 1, 5, 5)
    if endpoint == "headlines":
        h1, h2 = st.columns(2)
        extra["limit"] = h1.slider("Headlines", 5, 100, 25, step=5)
        extra["sort"] = h2.selectbox("Sort", ["newest", "priority", "oldest"])
    run = st.form_submit_button("Run request", type="primary")

params = {"q": q.strip(), "since": str(since), "until": str(until), **extra}
if country.strip():
    params["country"] = country.strip().lower()
if sentiment != "any":
    params["sentiment"] = sentiment
if priority_min > 1:
    params["priority_min"] = priority_min

qs = " ".join(f"--data-urlencode '{k}={v}'" for k, v in params.items())
with st.expander("The same request as curl and Python"):
    st.code(f'curl -sS --get "{API_BASE}/v1/{endpoint}" -H "X-API-Key: $PRISM_API_KEY" {qs}', language="bash")
    st.code(f"""import os, requests
r = requests.get("{API_BASE}/v1/{endpoint}",
                 headers={{"X-API-Key": os.environ["PRISM_API_KEY"]}},
                 params={params!r}, timeout=60)
print(r.json())""", language="python")


def layout(fig: go.Figure, h: int = 360) -> go.Figure:
    fig.update_layout(height=h, margin=dict(l=8, r=8, t=28, b=8), legend=dict(orientation="h", y=1.1, x=0))
    fig.update_xaxes(showgrid=False)
    return fig


def show(endpoint: str, payload: dict) -> None:
    data = payload.get("data") or {}
    win = payload.get("window") or {}
    if win:
        st.caption(f"Window {win.get('since')} to {win.get('until')} · data through {win.get('data_through')}"
                   + (f" · {win['freshness']}" if win.get("freshness") else ""))
    for n in (payload.get("meta") or {}).get("notes", []) or []:
        st.info(n)
    if endpoint == "overview":
        a, b, c = st.columns(3)
        a.metric("Matched articles", f"{data.get('matched', 0):,}")
        crit = data.get("critical") or {}
        b.metric("Critical share", f"{crit.get('share_pct', 0)}%", help="priority 7 or higher")
        groups = (data.get("tone") or {}).get("groups") or []
        neg = next((g for g in groups if g["group"] == "negative"), None)
        c.metric("Negative tone", f"{neg['share_pct']}%" if neg else "n/a")
        if groups:
            fig = go.Figure(go.Bar(x=[g["share_pct"] for g in groups], y=[g["group"] for g in groups],
                                   orientation="h", marker_color=[TONE.get(g["group"], BLUE) for g in groups],
                                   hovertemplate="%{x}%<extra></extra>"))
            fig.update_xaxes(title="share of articles with a tone label, %")
            st.plotly_chart(layout(fig, 220))
    elif endpoint == "trends" and data.get("points"):
        p = pd.DataFrame(data["points"])
        p["period"] = pd.to_datetime(p["period"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=p.period, y=p.articles, name="articles", mode="lines",
                                 line=dict(width=2, color=BLUE)))
        if "critical" in p:
            fig.add_trace(go.Scatter(x=p.period, y=p.critical, name="critical (priority 7+)", mode="lines",
                                     line=dict(width=2, color=ORANGE)))
        fig.update_layout(hovermode="x unified")
        fig.update_yaxes(title="articles", rangemode="tozero")
        st.plotly_chart(layout(fig))
        if p.get("partial_period") is not None and p.partial_period.any():
            st.caption("The last period is partial.")
    elif endpoint == "geography" and data.get("items"):
        it = pd.DataFrame(data["items"]).iloc[::-1]
        fig = go.Figure(go.Bar(x=it.share_pct, y=it.country, orientation="h", marker_color=BLUE,
                               customdata=it[["count"]].values,
                               hovertemplate="%{x}% · %{customdata[0]:,} articles<extra></extra>"))
        fig.update_xaxes(title="share of all matching articles, %")
        st.plotly_chart(layout(fig, 280))
        st.caption(f"{data.get('availability_pct')}% of matching articles carry a location.")
    elif endpoint == "themes" and data.get("items"):
        it = pd.DataFrame(data["items"]).iloc[::-1]
        fig = go.Figure(go.Bar(x=it["count"], y=it.theme.str.slice(0, 60), orientation="h", marker_color=AQUA,
                               customdata=it[["share", "lift"]].values,
                               hovertemplate="%{x:,} articles · %{customdata[0]}% · lift %{customdata[1]}×"
                                             "<extra></extra>"))
        fig.update_xaxes(title="articles")
        st.plotly_chart(layout(fig, 300))
    elif endpoint == "headlines" and data.get("items"):
        rows = [{"date": str(i.get("published_at", ""))[:10], "headline": i.get("headline"),
                 "publisher": i.get("publisher"), "priority": i.get("priority"),
                 "tone": (i.get("sentiment") or {}).get("group"), "url": i.get("url")} for i in data["items"]]
        df = pd.DataFrame(rows)
        if df.priority.notna().any():
            cnt = df.groupby("tone").size().reindex(["negative", "neutral", "positive"]).fillna(0)
            fig = go.Figure(go.Bar(x=cnt.index, y=cnt.values, marker_color=[TONE[t] for t in cnt.index],
                                   hovertemplate="%{y} headlines<extra></extra>"))
            st.plotly_chart(layout(fig, 220))
        st.dataframe(df, hide_index=True,
                     column_config={"url": st.column_config.LinkColumn("link", display_text="open")})
    else:
        st.warning("No rows to chart; see the JSON below.")


if run:
    if not key.strip():
        st.warning("Paste your API key first. No key yet? Open 'How to get a key' above.")
    elif not params["q"]:
        st.warning("Enter a query.")
    else:
        with st.spinner(f"GET /v1/{endpoint} …"):
            try:
                r = requests.get(f"{API_BASE}/v1/{endpoint}", params=params, timeout=90,
                                 headers={"X-API-Key": key.strip()})
                status = r.status_code
                try:
                    payload = r.json()
                except ValueError:
                    payload = {"ok": False, "error": {"kind": "non_json", "reason": r.text[:300]}}
            except requests.RequestException as e:
                status, payload = 0, {"ok": False, "error": {"kind": "network", "reason": str(e)[:300]}}
        if payload.get("ok"):
            st.success(f"HTTP {status} · {payload.get('feature')}")
            show(endpoint, payload)
        else:
            err = payload.get("error") or {}
            st.error(f"HTTP {status} · {err.get('kind')}: {err.get('reason')}")
            if status in (401, 403):
                st.markdown(f"Check the key, or [create a new one]({KEY_PAGE}).")
        with st.expander("Response JSON", expanded=True):
            st.json(payload)

st.divider()
st.caption(f"[Prism News API on GitHub]({API_REPO}) · [User guide]({GUIDE}) · "
           f"[Free news datasets, 60 topics]({HUB}) · Base URL `{API_BASE}` · App code MIT · "
           "contact b2b@fliarbi.com")
