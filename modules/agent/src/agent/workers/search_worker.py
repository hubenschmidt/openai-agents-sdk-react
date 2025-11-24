import logging
import os
from typing import Any

from agents import Agent, Runner
from serpapi import GoogleSearch

from agent.models import WorkerResult
from agent.prompts import SEARCH_WORKER_PROMPT

logger = logging.getLogger(__name__)

_api_key = os.getenv("SERPAPI_KEY", "")

_agent = Agent(
    name="SearchWorker",
    instructions=SEARCH_WORKER_PROMPT,
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
)


def _search(query: str, num_results: int = 5) -> list[dict[str, str]]:
    """Execute search query via SerpAPI."""
    if not _api_key:
        return [{"error": "SERPAPI_KEY not configured"}]

    params = {
        "q": query,
        "api_key": _api_key,
        "num": num_results,
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    organic_results = results.get("organic_results", [])
    return [
        {
            "title": r.get("title", ""),
            "link": r.get("link", ""),
            "snippet": r.get("snippet", ""),
        }
        for r in organic_results[:num_results]
    ]


def _format_results(results: list[dict[str, str]]) -> str:
    """Format search results for agent context."""
    formatted = [
        f"{i}. {r['title']}\n   {r['link']}\n   {r['snippet']}"
        for i, r in enumerate(results, 1)
    ]
    return "\n\n".join(formatted)


async def execute(
    task_description: str,
    parameters: dict[str, Any],
    feedback: str | None = None,
) -> WorkerResult:
    """Execute web search task."""
    logger.info("🔎 SEARCH_WORKER: Starting execution")
    logger.info(f"   Task: {task_description[:80]}...")
    if feedback:
        logger.info("   With feedback from previous attempt")

    try:
        query = parameters.get("query", task_description)
        num_results = parameters.get("num_results", 5)

        logger.info(f"🔎 SEARCH_WORKER: Searching for '{query}' ({num_results} results)")
        search_results = _search(query, num_results)

        if search_results and "error" in search_results[0]:
            logger.error(f"❌ SEARCH_WORKER: Search API error: {search_results[0]['error']}")
            return WorkerResult(
                success=False,
                output="",
                error=search_results[0]["error"],
            )

        logger.info(f"✓ SEARCH_WORKER: Got {len(search_results)} results")

        feedback_section = f"Previous feedback to address: {feedback}" if feedback else ""
        context = f"""Task: {task_description}

Search Results:
{_format_results(search_results)}

{feedback_section}

Synthesize these results into a clear, informative response."""

        result = await Runner.run(
            _agent,
            input=context,
        )

        logger.info("✓ SEARCH_WORKER: Execution complete")
        return WorkerResult(
            success=True,
            output=result.final_output,
        )

    except Exception as e:
        logger.error(f"❌ SEARCH_WORKER: Failed with error: {e}")
        return WorkerResult(
            success=False,
            output="",
            error=str(e),
        )
