"""LangGraph pipeline wiring the 3-agent research sequence."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from graph.state import ResearchState


def build_graph() -> StateGraph:
    """Construct and compile the research pipeline graph.

    Wires researcher → analyst → writer in a linear sequence and compiles
    the graph into a runnable LangGraph CompiledGraph.  Importing the
    agent modules is deferred to inside this function so that the graph
    definition module itself has no transitive dependency on heavy agent
    dependencies at import time (avoids circular-import issues when agent
    modules import from graph.state).

    Returns:
        A compiled LangGraph CompiledGraph ready to be invoked with an
        initial ResearchState dict containing at least the ``topic`` key.
    """
    # Deferred imports — keeps module-level imports clean and prevents
    # circular dependencies if agent modules ever import from graph.*
    from agents.analyst import analyst_node
    from agents.researcher import researcher_node
    from agents.writer import writer_node

    graph = StateGraph(ResearchState)

    graph.add_node("researcher", researcher_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("writer", writer_node)

    graph.set_entry_point("researcher")

    graph.add_edge("researcher", "analyst")
    graph.add_edge("analyst", "writer")
    graph.add_edge("writer", END)

    return graph.compile()


# Module-level compiled instance — import this for production use.
pipeline = build_graph()


if __name__ == "__main__":
    TEST_TOPIC = "Retrieval Augmented Generation for enterprise applications 2025"

    print(f"Running research pipeline for topic:\n  {TEST_TOPIC}\n")

    result: ResearchState = pipeline.invoke(
        {
            "topic": TEST_TOPIC,
            "sources": [],
            "filtered_findings": [],
            "report_sections": [],
            "final_report": None,
            "token_usage": 0,
            "cost_usd": 0.0,
            "errors": [],
        }
    )

    print(f"Sources found    : {len(result['sources'])}")
    print(f"Report sections  : {len(result['report_sections'])}")

    if result["errors"]:
        print(f"Errors           : {len(result['errors'])}")
        for err in result["errors"]:
            print(f"  - {err}")
