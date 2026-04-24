"""Reusable UI helper components for Streamlit frontend."""

from __future__ import annotations

import streamlit as st


def section_title(title: str, subtitle: str | None = None) -> None:
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)
