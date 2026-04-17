"""Researcher agent — Agent 1 of the multi-agent research pipeline.

Searches the web (Tavily) and arXiv in parallel, then uses an LLM to score
each result's relevance to the research topic.  Only results scoring >= 0.5
are kept and forwarded to the analyst agent via the pipeline state.
"""

from __future__ import annotations

from typing import List

from langchain_ollama import ChatOllama

from graph.state import Source
from tools.arxiv_search import search_arxiv
from tools.tavily_search import search_web

_RELEVANCE_PROMPT = """\
You are a relevance-scoring assistant.

Research topic: {topic}

Source content:
{content}

On a scale from 0.0 to 1.0, how relevant is this content to the research topic?
Reply with ONLY a single decimal number between 0.0 and 1.0. No explanation, no units."""

def score_relevance(llm: ChatOllama, topic: str, content: str) -> float:
    """Ask the LLM to score how relevant *content* is to *topic*.

    The LLM is prompted to respond with a single decimal number in [0, 1].
    Any response that cannot be parsed as a float falls back to 0.5 so that
    borderline sources are kept rather than silently discarded.

    Args:
        llm:     Configured ChatAnthropic instance.
        topic:   The research topic string.
        content: The source snippet or abstract to score.

    Returns:
        A float in [0.0, 1.0].
    """
    try:
        prompt = _RELEVANCE_PROMPT.format(topic=topic, content=content[:500])
        response = llm.invoke(prompt)
        score = float(response.content.strip())
        return max(0.0, min(1.0, score))
    except Exception:  # noqa: BLE001
        return 0.5


def researcher_node(state: dict) -> dict:
    """LangGraph node that searches and scores sources for the given topic.

    Combines Tavily web results and arXiv academic results, scores each with
    the LLM, and returns only those with relevance >= 0.5 as ``Source`` objects.

    Args:
        state: The current ResearchState dict.  Must contain ``"topic"``.

    Returns:
        A partial ResearchState dict with ``"sources"`` and ``"errors"`` keys.
        Both lists are intended to be merged into the existing state via the
        ``operator.add`` reducer defined on those fields.
    """
    llm = ChatOllama(model="qwen2.5:1.5b", temperature=0)

    try:
        topic: str = state["topic"]
        errors: List[str] = []

        web_results = search_web(topic, max_results=8)
        arxiv_results = search_arxiv(topic, max_results=5)
        all_results = web_results + arxiv_results

        if not all_results:
            return {
                "sources": [],
                "errors": [f"researcher: no sources found for topic: {topic}"],
            }

        sources: List[Source] = []
        for result in all_results:
            score = score_relevance(llm, topic, result.get("content", ""))
            if score < 0.5:
                continue
            sources.append(
                Source(
                    title=result.get("title", ""),
                    url=result.get("url", ""),
                    snippet=result.get("content", "")[:500],
                    relevance_score=score,
                    key_findings=[],
                )
            )

        if not sources:
            errors.append(
                f"researcher: all {len(all_results)} results scored below 0.5 "
                f"for topic: {topic}"
            )

        return {"sources": sources, "errors": errors}

    except Exception as exc:  # noqa: BLE001
        return {
            "sources": [],
            "errors": [f"researcher: unexpected error — {exc}"],
        }


if __name__ == "__main__":
    TEST_TOPIC = "LangGraph agentic AI pipelines 2025"

    print(f"Running researcher agent for topic:\n  {TEST_TOPIC}\n")

    result = researcher_node({"topic": TEST_TOPIC})
    sources: List[Source] = result["sources"]
    errors: List[str] = result["errors"]

    print(f"Sources kept     : {len(sources)}")

    if sources:
        avg_score = sum(s.relevance_score for s in sources) / len(sources)
        print(f"Avg relevance    : {avg_score:.2f}")
        print(f"First source     : {sources[0].title}")

    if errors:
        print(f"\nWarnings:")
        for err in errors:
            print(f"  - {err}")
