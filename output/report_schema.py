"""Final report schema for the multi-agent research pipeline.

Assembles the ReportSection objects produced by the writer agent into a
single validated model and provides rendering helpers for downstream
consumers (PDF export, Streamlit UI, Notion push).
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel

from graph.state import ReportSection


class FinalReport(BaseModel):
    """A fully assembled, validated research report ready for export.

    Constructed from a completed ResearchState dict via ``from_state()``.
    Carries metadata about the pipeline run (token usage, cost, source counts)
    alongside the structured section content produced by the writer agent.
    """

    topic: str
    sections: List[ReportSection]
    sources_count: int
    findings_count: int
    token_usage: int
    cost_usd: float
    generated_at: str  # ISO 8601 datetime string

    @classmethod
    def from_state(cls, state: dict) -> "FinalReport":
        """Build a FinalReport from a completed ResearchState dict.

        Args:
            state: A fully-executed ResearchState containing at minimum
                   ``topic``, ``report_sections``, ``sources``,
                   ``filtered_findings``, ``token_usage``, and ``cost_usd``.

        Returns:
            A validated FinalReport instance.
        """
        return cls(
            topic=state["topic"],
            sections=state["report_sections"],
            sources_count=len(state["sources"]),
            findings_count=len(state["filtered_findings"]),
            token_usage=state["token_usage"],
            cost_usd=state["cost_usd"],
            generated_at=datetime.utcnow().isoformat(),
        )

    def to_markdown(self) -> str:
        """Render the report as a markdown string.

        Produces a document with a top-level title, a blockquote metadata
        line, and one ``##`` subsection per ReportSection.

        Returns:
            A markdown-formatted string of the full report.
        """
        lines: List[str] = [
            f"# {self.topic}",
            "",
            (
                f"> Generated: {self.generated_at} | "
                f"Sources: {self.sources_count} | "
                f"Findings: {self.findings_count} | "
                f"Cost: ${self.cost_usd:.4f}"
            ),
        ]

        for section in self.sections:
            lines.append("")
            lines.append(f"## {section.heading}")
            lines.append("")
            lines.append(section.content)

        return "\n".join(lines)


if __name__ == "__main__":
    mock_report = FinalReport(
        topic="Retrieval Augmented Generation for Enterprise Applications 2025",
        sections=[
            ReportSection(
                heading="Executive Summary",
                content=(
                    "Retrieval-Augmented Generation (RAG) has emerged as the dominant "
                    "paradigm for grounding large language model outputs in verified "
                    "enterprise knowledge. Organisations adopting RAG report measurable "
                    "reductions in hallucination rates and improved compliance with "
                    "internal documentation standards. The technology is now considered "
                    "production-ready for knowledge management, customer support, and "
                    "regulatory reporting use cases."
                ),
                citations=[
                    "https://arxiv.org/abs/2312.10997",
                    "https://example.com/enterprise-rag-2025",
                ],
            ),
            ReportSection(
                heading="Key Findings",
                content=(
                    "Hybrid search combining dense vector retrieval with BM25 keyword "
                    "matching consistently outperforms either approach in isolation "
                    "across enterprise benchmarks. Domain-specific embedding models "
                    "fine-tuned on proprietary corpora deliver a 15-30% improvement "
                    "in retrieval precision compared to general-purpose models.\n\n"
                    "Reranking retrieved chunks prior to generation is now considered "
                    "a standard best practice, with cross-encoder rerankers offering "
                    "the best quality-latency trade-off for most enterprise workloads."
                ),
                citations=["https://arxiv.org/abs/2401.00368"],
            ),
        ],
        sources_count=13,
        findings_count=18,
        token_usage=4200,
        cost_usd=4200 * 0.000015,
        generated_at=datetime.utcnow().isoformat(),
    )

    print(mock_report.to_markdown())
