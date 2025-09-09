
import streamlit as st
import plotly.express as px
import pandas as pd
from typing import Dict, Any

BRAND = {
    "primary":"#7C3AED",
    "ok":"#10B981",
    "warn":"#F59E0B",
    "bad":"#EF4444"
}

def header(logo_path:str, title:str, subtitle:str=""):
    c1,c2 = st.columns([0.2,0.8])
    c1.image(logo_path, width=90)
    with c2:
        st.markdown(f"### {title}")
        if subtitle:
            st.markdown(f"<span style='color:#94A3B8'>{subtitle}</span>", unsafe_allow_html=True)
    st.divider()

def metric_cards(metrics):
    cols = st.columns(len(metrics))
    for col, (label, (value, delta, color)) in zip(cols, metrics.items()):
        col.metric(label, value, delta=delta, help=None)
        col.markdown(f"<div style='height:4px;background:{color};border-radius:6px;margin-top:-8px'></div>", unsafe_allow_html=True)

def table(df: pd.DataFrame):
    st.dataframe(df, use_container_width=True, hide_index=True)

def line_chart(df: pd.DataFrame, x:str, y:str, color=None, title=""):
    fig = px.line(df, x=x, y=y, color=color, markers=True, title=title)
    st.plotly_chart(fig, use_container_width=True)
