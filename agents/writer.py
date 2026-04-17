"""Writer agent — Agent 3 of the multi-agent research pipeline.

Takes the deduplicated findings produced by the analyst and writes a
structured 5-section research report using Claude Sonnet, the highest-quality
model in the pipeline.  Each section is generated independently so failures
are isolated and partial reports are still useful.
"""

from __future__ import annotations

import json
from typing import List, Tuple

from langchain_ollama import ChatOllama

from graph.state import ReportSection, Source

REPORT_SECTIONS: List[Tuple[str, str]] = [
    ("Executive Summary",    "Write a 3-sentence executive summary"),
    ("Background & Context", "Write background and context"),
    ("Key Findings",         "Summarise the most important findings in detail"),
    ("Analysis",             "Analyse implications and what the findings mean"),
    ("Conclusion",           "Write a conclusion with recommended next steps"),
]

_SECTION_PROMPT = """\
You are writing a section of a professional research report.

Research topic: {topic}

Section: {heading}
Instruction: {instruction}

Key findings to draw on:
{findings_block}

Write 2-3 clear, well-structured paragraphs for this section.
Your audience is a professional researcher or consultant who values precision,
evidence-based reasoning, and actionable insight.
Do not add a heading — the heading is handled separately.
Do not use markdown bullet points — write in flowing prose."""


def generate_section(
    llm: ChatOllama,
    heading: str,
    instruction: str,
    topic: str,
    findings: List[str],
    citations: List[str],
) -> ReportSection:
    """Generate a single report section via LLM.

    Builds a focused prompt from the heading, instruction, topic, and the
    full findings list, then wraps the LLM response in a ReportSection.

    Args:
        llm:         Configured ChatAnthropic instance (Sonnet).
        heading:     Section heading string (e.g. "Executive Summary").
        instruction: Specific writing instruction for this section.
        topic:       The original research topic.
        findings:    Flat list of deduplicated findings from the analyst.
        citations:   List of source URLs to attach to this section.

    Returns:
        A ReportSection with heading, prose content, and citations.
        Returns a placeholder section if generation fails.
    """
    try:
        findings_block = "\n".join(f"- {f}" for f in findings)
        prompt = _SECTION_PROMPT.format(
            topic=topic,
            heading=heading,
            instruction=instruction,
            findings_block=findings_block,
        )
        response = llm.invoke(prompt)
        return ReportSection(
            heading=heading,
            content=response.content.strip(),
            citations=citations,
        )
    except Exception:  # noqa: BLE001
        return ReportSection(
            heading=heading,
            content="(generation failed)",
            citations=[],
        )


def writer_node(state: dict) -> dict:
    """LangGraph node that writes a 5-section research report from findings.

    Iterates over REPORT_SECTIONS, generating each independently so a single
    section failure does not abort the entire report.  Tracks token usage and
    estimated cost for the run.

    Args:
        state: The current ResearchState dict.  Must contain
               ``"filtered_findings"``, ``"sources"``, and ``"topic"``.

    Returns:
        A partial ResearchState dict with ``"report_sections"``,
        ``"token_usage"``, ``"cost_usd"``, and ``"errors"`` keys.
    """
    llm = ChatOllama(model="qwen2.5:1.5b", temperature=0.3)

    try:
        findings: List[str] = state["filtered_findings"]
        sources: List[Source] = state["sources"]
        topic: str = state["topic"]

        if not findings:
            return {
                "report_sections": [],
                "token_usage": 0,
                "cost_usd": 0.0,
                "errors": ["writer: no findings to write from — analyst may have failed"],
            }

        citations: List[str] = [s.url for s in sources if s.url][:10]

        sections: List[ReportSection] = []
        total_tokens: int = 0

        for heading, instruction in REPORT_SECTIONS:
            response_obj = None
            try:
                findings_block = "\n".join(f"- {f}" for f in findings)
                prompt = _SECTION_PROMPT.format(
                    topic=topic,
                    heading=heading,
                    instruction=instruction,
                    findings_block=findings_block,
                )
                response_obj = llm.invoke(prompt)
                output_tokens = (
                    response_obj.usage_metadata.get("output_tokens", 0)
                    if response_obj.usage_metadata
                    else 0
                )
                total_tokens += output_tokens
                sections.append(
                    ReportSection(
                        heading=heading,
                        content=response_obj.content.strip(),
                        citations=citations,
                    )
                )
            except Exception:  # noqa: BLE001
                sections.append(
                    ReportSection(
                        heading=heading,
                        content="(generation failed)",
                        citations=[],
                    )
                )

        cost_usd: float = total_tokens * 0.000015

        return {
            "report_sections": sections,
            "token_usage": total_tokens,
            "cost_usd": cost_usd,
            "errors": [],
        }

    except Exception as exc:  # noqa: BLE001
        return {
            "report_sections": [],
            "token_usage": 0,
            "cost_usd": 0.0,
            "errors": [f"writer: unexpected error — {exc}"],
        }


if __name__ == "__main__":
    mock_findings = [
        "LangGraph models multi-agent workflows as directed graphs with shared typed state.",
        "RAG significantly reduces hallucination rates by grounding LLM responses in retrieved documents.",
        "Hybrid search combining dense embeddings with BM25 outperforms either method alone.",
        "Reranking retrieved chunks before generation further improves output quality.",
        "Enterprise RAG deployments benefit most from domain-specific fine-tuned embedding models.",
    ]
    mock_sources = [
        Source(
            title="LangGraph Documentation",
            url="https://langchain-ai.github.io/langgraph/",
            snippet="LangGraph is a library for building stateful, multi-actor applications with LLMs.",
            relevance_score=0.95,
        ),
        Source(
            title="RAG Survey 2025",
            url="https://arxiv.org/abs/2312.10997",
            snippet="A comprehensive survey of retrieval-augmented generation techniques and benchmarks.",
            relevance_score=0.88,
        ),
    ]

    TEST_TOPIC = "LangGraph agentic AI pipelines 2025"

    print(f"Running writer agent for topic:\n  {TEST_TOPIC}\n")

    result = writer_node(
        {
            "topic": TEST_TOPIC,
            "filtered_findings": mock_findings,
            "sources": mock_sources,
        }
    )

    sections: List[ReportSection] = result["report_sections"]
    errors: List[str] = result["errors"]

    print(f"Sections generated : {len(sections)}")
    print(f"Token usage        : {result['token_usage']}")
    print(f"Estimated cost     : ${result['cost_usd']:.4f}\n")

    for section in sections:
        word_count = len(section.content.split())
        print(f"  {section.heading:<25} {word_count} words")

    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"  - {err}")
