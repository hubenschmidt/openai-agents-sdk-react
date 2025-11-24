import logging
import os
from typing import Any

from agents import Agent, Runner

from agent.models import WorkerResult
from agent.prompts.workers.general import GENERAL_WORKER_PROMPT

logger = logging.getLogger(__name__)

_agent = Agent(
    name="GeneralWorker",
    instructions=GENERAL_WORKER_PROMPT,
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
)


async def execute(
    task_description: str,
    parameters: dict[str, Any],
    feedback: str | None = None,
) -> WorkerResult:
    """Execute general conversational task."""
    logger.info("💬 GENERAL_WORKER: Starting execution")
    logger.info(f"   Task: {task_description[:80]}...")
    if feedback:
        logger.info("   With feedback from previous attempt")

    try:
        context = task_description
        if feedback:
            context = f"{task_description}\n\nPrevious feedback to address: {feedback}"

        result = await Runner.run(
            _agent,
            input=context,
        )

        logger.info("✓ GENERAL_WORKER: Execution complete")
        return WorkerResult(
            success=True,
            output=result.final_output,
        )

    except Exception as e:
        logger.error(f"❌ GENERAL_WORKER: Failed with error: {e}")
        return WorkerResult(
            success=False,
            output="",
            error=str(e),
        )
