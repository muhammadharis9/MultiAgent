"""State definitions for the multi-agent research pipeline."""

import operator
from typing import Annotated, List, Optional

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class Source(BaseModel):
    """Represents a single research source discovered by the search agent.

    Populated initially by the searcher with metadata and a content snippet,
    then enriched by the analyst agent which fills in key_findings after
    evaluating relevance to the research topic.
    """

    title: str
    url: str
    snippet: str = Field(..., max_length=500, description="Up to 500 chars of source content")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score between 0.0 and 1.0")
    key_findings: List[str] = Field(default_factory=list, description="Filled in by analyst agent")


class ReportSection(BaseModel):
    """Represents one section of the final synthesized research report.

    Produced by the writer agent from filtered findings. Each section maps
    to a logical topic area and carries the URLs of sources that back its claims.
    """

    heading: str
    content: str
    citations: List[str] = Field(default_factory=list, description="List of source URLs cited in this section")


class ResearchState(TypedDict):
    """LangGraph shared state passed between all agents in the research pipeline.

    - topic: the original research question driving the pipeline
    - sources: accumulates across parallel search branches via operator.add
    - filtered_findings: distilled insights selected by the analyst agent
    - report_sections: structured sections assembled by the writer agent
    - final_report: fully rendered markdown report, set by the compiler agent
    - token_usage: running total of tokens consumed across all LLM calls
    - cost_usd: running total cost in USD across all LLM calls
    - errors: accumulates non-fatal error messages via operator.add so no
      branch silently swallows failures
    """

    topic: str
    sources: Annotated[List[Source], operator.add]
    filtered_findings: List[str]
    report_sections: List[ReportSection]
    final_report: Optional[str]
    token_usage: int
    cost_usd: float
    errors: Annotated[List[str], operator.add]
