"""Streamlit demo UI for the multi-agent research pipeline.

Portfolio-facing app deployed on HuggingFace Spaces.  Provides a clean
interface for running the 3-agent LangGraph pipeline, displaying live
progress, and downloading the finished report as a PDF.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from graph.pipeline import pipeline
from output.pdf_export import generate_pdf
from output.report_schema import FinalReport

# ---------------------------------------------------------------------------
# Page config — must be the first Streamlit call
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Research Agent",
    layout="wide",
    page_icon="🔬",
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## AI Research Agent")
    st.markdown("Multi-agent pipeline · LangGraph · Claude API")

    st.divider()

    st.markdown("**How it works**")
    st.markdown(
        "- 🔍 **Researcher** — searches the web (Tavily) and academic papers (arXiv), "
        "scores relevance with Claude Haiku\n"
        "- 🧠 **Analyst** — extracts key findings from each source, deduplicates "
        "and filters noise\n"
        "- ✍️ **Writer** — generates a structured 5-section report with citations "
        "using Claude Sonnet"
    )

    st.divider()

    st.markdown("**Tech stack**")
    st.markdown(
        "- LangGraph\n"
        "- Claude Sonnet + Haiku\n"
        "- Tavily Search\n"
        "- arXiv API\n"
        "- ReportLab PDF"
    )

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

if "topic" not in st.session_state:
    st.session_state["topic"] = ""
if "last_result" not in st.session_state:
    st.session_state["last_result"] = None

# ---------------------------------------------------------------------------
# Main area — input
# ---------------------------------------------------------------------------

st.title("AI Research Agent")
st.caption("Enter a research topic and let the multi-agent pipeline do the work.")

topic: str = st.text_input(
    "Research topic",
    value=st.session_state["topic"],
    placeholder="e.g. LangGraph for production AI agents 2025",
    key="topic_input",
)

run_button = st.button("Generate Report", type="primary")

# Example topics expander
with st.expander("Example topics"):
    examples = [
        "Retrieval Augmented Generation for enterprise applications 2025",
        "LangGraph multi-agent systems in production",
        "Transformer architectures for time-series forecasting",
        "Open-source LLMs vs proprietary models: performance and cost 2025",
    ]
    cols = st.columns(2)
    for i, example in enumerate(examples):
        if cols[i % 2].button(example, key=f"example_{i}"):
            st.session_state["topic"] = example
            st.rerun()

# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

NODE_MESSAGES: dict[str, str] = {
    "researcher": "Agent 1 — Researcher: searching web and arXiv...",
    "analyst":    "Agent 2 — Analyst: extracting and filtering findings...",
    "writer":     "Agent 3 — Writer: generating report with Claude Sonnet...",
}

if run_button and topic:
    if len(topic.strip()) < 10:
        st.warning("Please enter a topic with at least 10 characters.")
        st.stop()

    try:
        with st.status("Running research pipeline...", expanded=True) as status:
            initial_state = {
                "topic": topic.strip(),
                "sources": [],
                "filtered_findings": [],
                "report_sections": [],
                "final_report": None,
                "token_usage": 0,
                "cost_usd": 0.0,
                "errors": [],
            }

            final_state: dict = initial_state.copy()

            for step in pipeline.stream(initial_state):
                for node_name, node_output in step.items():
                    message = NODE_MESSAGES.get(node_name, f"Running {node_name}...")
                    st.write(message)
                    # Merge each node's partial output into final_state
                    for key, value in node_output.items():
                        if isinstance(value, list) and isinstance(final_state.get(key), list):
                            final_state[key] = final_state[key] + value
                        else:
                            final_state[key] = value

            status.update(label="Report ready!", state="complete")
            st.session_state["last_result"] = final_state

    except Exception as exc:
        st.error(f"Pipeline failed: {exc}")
        st.stop()

# ---------------------------------------------------------------------------
# Results display
# ---------------------------------------------------------------------------

final_state = st.session_state.get("last_result")

if final_state:
    report = FinalReport.from_state(final_state)

    # Errors / warnings
    if final_state.get("errors"):
        with st.expander("Warnings", expanded=False):
            for err in final_state["errors"]:
                st.markdown(f":orange[{err}]")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Sources Found",      report.sources_count)
    col2.metric("Findings Extracted", report.findings_count)
    col3.metric("Sections Written",   len(report.sections))
    col4.metric("Estimated Cost",     f"${report.cost_usd:.4f}")

    st.markdown("---")

    # Report sections
    for i, section in enumerate(report.sections):
        with st.expander(section.heading, expanded=(i == 0)):
            st.markdown(section.content)

            if section.citations:
                st.subheader("Sources")
                for url in section.citations:
                    st.markdown(f"- [{url}]({url})")

    # PDF download
    st.divider()
    pdf_bytes: bytes = generate_pdf(report)
    st.download_button(
        label="Download PDF Report",
        data=pdf_bytes,
        file_name="research_report.pdf",
        mime="application/pdf",
    )
