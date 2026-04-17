"""arXiv academic paper search wrapper for the researcher agent.

Provides the same normalised result shape as tools/tavily_search.py
(title, url, content) so the researcher agent can merge results from
both sources without any special-casing.  No API key required — the
arXiv API is free and open.
"""

from __future__ import annotations

from typing import List


def search_arxiv(query: str, max_results: int = 5) -> List[dict]:
    """Search arXiv for academic papers matching *query*.

    Args:
        query:       The search query string.
        max_results: Maximum number of papers to return (default 5).

    Returns:
        A list of dicts, each with keys ``title``, ``url``, and ``content``.
        ``url`` is the arXiv abstract page link; ``content`` is the abstract
        truncated to 500 characters.  Returns an empty list if the search
        fails for any reason.
    """
    try:
        import arxiv

        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )

        results: List[dict] = []
        for paper in client.results(search):
            results.append(
                {
                    "title": paper.title,
                    "url": paper.entry_id,
                    "content": paper.summary[:500],
                }
            )
        return results

    except Exception as exc:  # noqa: BLE001
        print(f"[arxiv_search] search failed for query {query!r}: {exc}")
        return []


if __name__ == "__main__":
    TEST_QUERY = "retrieval augmented generation"

    print(f"Searching arXiv for: {TEST_QUERY!r}\n")
    results = search_arxiv(TEST_QUERY)

    print(f"Results returned : {len(results)}")
    if results:
        print(f"First result     : {results[0]['title']}")
        print(f"URL              : {results[0]['url']}")
