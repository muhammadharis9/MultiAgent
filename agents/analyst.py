"""Analyst agent — Agent 2 of the multi-agent research pipeline.

Reads Source objects collected by the researcher, extracts structured key
findings from each snippet via LLM, then deduplicates the combined finding
list before forwarding it to the writer agent.
"""

from __future__ import annotations

import json
from typing import List

from langchain_ollama import ChatOllama

from graph.state import Source

_EXTRACT_PROMPT = """\
You are a research analyst extracting key insights from source material.

Research topic: {topic}

Source snippet:
{snippet}

Extract exactly 3 key findings from this snippet that are relevant to the topic.
Return ONLY a valid JSON array of exactly 3 strings.
No markdown fences, no explanation, no extra text — just the raw JSON array.

Example of the exact format required:
["Finding one.", "Finding two.", "Finding three."]"""

_DEDUPLICATE_PROMPT = """\
You are a research analyst deduplicating a list of findings.

Below is a list of research findings that may contain near-duplicates or \
redundant points:
{findings_json}

Return a deduplicated list keeping the clearest and most informative version \
of each unique point. Remove near-duplicates but keep genuinely distinct findings.
Return ONLY a valid JSON array of strings.
No markdown fences, no explanation, no extra text — just the raw JSON array."""


def extract_findings(llm: ChatOllama, topic: str, source: Source) -> List[str]:
    """Extract exactly 3 key findings from a source snippet via LLM.

    Mutates ``source.key_findings`` in place so the enriched Source is
    available to downstream agents, and also returns the list for convenience.

    Args:
        llm:    Configured ChatAnthropic instance.
        topic:  The research topic guiding what counts as a relevant finding.
        source: The Source object whose snippet will be analysed.

    Returns:
        A list of finding strings (normally 3).  Falls back to a single-item
        list containing a truncated raw response if JSON parsing fails.
    """
    try:
        prompt = _EXTRACT_PROMPT.format(topic=topic, snippet=source.snippet)
        response = llm.invoke(prompt)
        findings: List[str] = json.loads(response.content.strip())
    except Exception:  # noqa: BLE001
        raw = getattr(response, "content", "") if "response" in dir() else ""
        findings = [raw.strip()[:200]] if raw.strip() else ["(extraction failed)"]

    source.key_findings = findings
    return findings


def deduplicate_findings(llm: ChatOllama, findings: List[str]) -> List[str]:
    """Remove near-duplicate findings from a combined list using the LLM.

    Skips the LLM call entirely when the list is short enough that
    deduplication would not be worthwhile (fewer than 5 items).

    Args:
        llm:      Configured ChatAnthropic instance.
        findings: Flat list of finding strings from all sources.

    Returns:
        A deduplicated list of findings.  Returns the original list unchanged
        if the input is short or if JSON parsing of the LLM response fails.
    """
    if len(findings) < 5:
        return findings

    try:
        prompt = _DEDUPLICATE_PROMPT.format(findings_json=json.dumps(findings))
        response = llm.invoke(prompt)
        return json.loads(response.content.strip())
    except Exception:  # noqa: BLE001
        return findings


def analyst_node(state: dict) -> dict:
    """LangGraph node that extracts and deduplicates findings from sources.

    Iterates over all Source objects in state, calls the LLM once per source
    to extract key findings, then deduplicates the combined pool before
    returning it as ``filtered_findings``.

    Args:
        state: The current ResearchState dict.  Must contain ``"sources"``
               and ``"topic"``.

    Returns:
        A partial ResearchState dict with ``"filtered_findings"`` and
        ``"errors"`` keys.
    """
    llm = ChatOllama(model="qwen2.5:1.5b", temperature=0)

    try:
        sources: List[Source] = state["sources"]
        topic: str = state["topic"]

        if not sources:
            return {
                "filtered_findings": [],
                "errors": ["analyst: no sources to analyse — researcher may have failed"],
            }

        all_findings: List[str] = []
        for source in sources:
            findings = extract_findings(llm, topic, source)
            all_findings.extend(findings)

        deduplicated = deduplicate_findings(llm, all_findings)

        return {"filtered_findings": deduplicated, "errors": []}

    except Exception as exc:  # noqa: BLE001
        return {
            "filtered_findings": [],
            "errors": [f"analyst: unexpected error — {exc}"],
        }


if __name__ == "__main__":
    mock_sources = [
        Source(
            title="LangGraph: Building Stateful Multi-Agent Systems",
            url="https://example.com/langgraph-intro",
            snippet=(
                "LangGraph enables developers to build stateful, multi-actor "
                "applications with LLMs. It models agent workflows as directed "
                "graphs where nodes represent computation steps and edges define "
                "control flow. State is shared across all nodes via a typed dict, "
                "making it easy to pass data between agents without global variables."
            ),
            relevance_score=0.92,
        ),
        Source(
            title="RAG Pipelines in Production: Lessons Learned",
            url="https://example.com/rag-production",
            snippet=(
                "Retrieval-Augmented Generation (RAG) improves LLM accuracy by "
                "grounding responses in retrieved documents. In production, the "
                "retrieval step is typically the bottleneck. Hybrid search combining "
                "dense embeddings with BM25 keyword search consistently outperforms "
                "either approach alone. Reranking retrieved chunks before generation "
                "reduces hallucination rates significantly."
            ),
            relevance_score=0.85,
        ),
    ]

    TEST_TOPIC = "LangGraph agentic AI pipelines 2025"

    print(f"Running analyst agent with {len(mock_sources)} mock sources\n")

    result = analyst_node({"topic": TEST_TOPIC, "sources": mock_sources})

    findings: List[str] = result["filtered_findings"]
    errors: List[str] = result["errors"]

    print(f"Findings extracted : {len(findings)}")
    for i, f in enumerate(findings, 1):
        print(f"  {i}. {f}")

    if errors:
        print("\nWarnings:")
        for err in errors:
            print(f"  - {err}")
