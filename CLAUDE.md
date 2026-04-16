# Multi-Agent Research & Report Generator

## Project overview
A 3-agent AI pipeline that takes any research topic, searches the web
and academic sources, reasons over the findings, and produces a
structured report. Deployed as a live Streamlit demo.

## My background (for context)
- I am a Physics MSc student (Erasmus Mundus) with ML/AI internship experience
- Comfortable with Python, FastAPI, LangChain, FAISS, Docker
- This is a portfolio project for Upwork in the AI agent / RAG domain
- I have a Claude Plus subscription — use claude-sonnet-4-6 for the
  writer agent and claude-haiku-4-5-20251001 for cheaper research/analysis steps

## Architecture — 3 agents in sequence
1. Researcher agent  → searches Tavily (web) + arXiv (papers), scores relevance
2. Analyst agent     → extracts key findings, deduplicates, filters noise
3. Writer agent      → produces 5-section structured report with citations

State flows through all agents via a LangGraph StateGraph.

## Tech stack
- Agent orchestration: LangGraph + LangChain
- LLMs: claude-sonnet-4-6 (writer), claude-haiku-4-5-20251001 (researcher/analyst)
- Search: Tavily API (web), arXiv API (academic papers)
- Backend: FastAPI + Pydantic
- Frontend/demo: Streamlit
- PDF export: ReportLab
- Package manager: uv
- Deployment: HuggingFace Spaces (Streamlit)

## File responsibilities
- graph/state.py       → LangGraph state schema (ResearchState, Source, ReportSection)
- graph/pipeline.py    → StateGraph definition connecting the 3 agents
- agents/researcher.py → Agent 1: web + arXiv search, relevance scoring
- agents/analyst.py    → Agent 2: finding extraction + deduplication
- agents/writer.py     → Agent 3: structured report generation
- tools/tavily_search.py  → Tavily web search wrapper
- tools/arxiv_search.py   → arXiv API wrapper
- tools/notion_push.py    → Notion export (optional)
- output/report_schema.py → Pydantic models for report structure
- output/pdf_export.py    → ReportLab PDF generator
- app/streamlit_app.py    → Live demo UI with agent trace

## Coding conventions
- All functions must have type hints
- Use Pydantic models for all data structures passed between agents
- All agent nodes must return a dict matching ResearchState fields
- Use python-dotenv to load .env — never hardcode API keys
- Every agent function must handle errors gracefully and append to state["errors"]
- Keep agent files focused — one agent per file, no mixing logic

## Environment variables required
ANTHROPIC_API_KEY=       # Claude API — from your Plus subscription
TAVILY_API_KEY=          # From tavily.com — free tier is enough
NOTION_TOKEN=            # Optional — only needed for Notion export

## Key design decisions
- LangGraph over raw LangChain for agent orchestration — cleaner state management
- claude-haiku for researcher/analyst steps to keep cost under $0.05/report
- claude-sonnet-4-6 only for the writer step — highest quality prose
- Streamlit st.status() for live agent trace — this is the key demo differentiator
- arXiv integration targets research/scientific clients — unique vs competitors
- Cost tracking (tokens + USD) displayed per run — transparency feature

## Current build phase
Phase 1 — Setup & foundations
Next task: write graph/state.py

## Commands
# Install deps
uv add langchain langgraph langchain-anthropic langchain-community
uv add tavily-python streamlit fastapi uvicorn pydantic python-dotenv
uv add reportlab arxiv duckduckgo-search

# Run Streamlit demo
uv run streamlit run app/streamlit_app.py

# Run FastAPI (optional)
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest tests/