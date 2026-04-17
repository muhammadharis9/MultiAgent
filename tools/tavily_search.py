"""Tavily web-search wrapper for the researcher agent.

Provides a thin, error-safe interface over TavilySearchResults so the
rest of the pipeline never has to deal with API or network exceptions
directly.  Results are normalised to a consistent dict shape regardless
of what Tavily returns.
"""

from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv

load_dotenv()


def search_web(query: str, max_results: int = 8) -> List[dict]:
    """Search the web via Tavily and return a normalised list of results.

    Args:
        query:       The search query string.
        max_results: Maximum number of results to return (default 8).

    Returns:
        A list of dicts, each with keys ``title``, ``url``, and ``content``.
        Returns an empty list if the search fails for any reason.

    Raises:
        ValueError: If ``TAVILY_API_KEY`` is not set in the environment.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError(
            "TAVILY_API_KEY is not set. "
            "Add it to your .env file or export it as an environment variable. "
            "Get a free key at https://tavily.com."
        )

    try:
        from langchain_community.tools.tavily_search import TavilySearchResults

        tool = TavilySearchResults(
            max_results=max_results,
            tavily_api_key=api_key,
        )
        raw: List[dict] = tool.invoke(query)

        results: List[dict] = []
        for item in raw:
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                }
            )
        return results

    except Exception as exc:  # noqa: BLE001
        print(f"[tavily_search] search failed for query {query!r}: {exc}")
        return []


if __name__ == "__main__":
    TEST_QUERY = "LangGraph multi-agent systems"

    print(f"Searching Tavily for: {TEST_QUERY!r}\n")
    results = search_web(TEST_QUERY)

    print(f"Results returned : {len(results)}")
    if results:
        print(f"First result     : {results[0]['title']}")
        print(f"URL              : {results[0]['url']}")
