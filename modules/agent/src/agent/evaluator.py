import logging
import os

from agents import Agent, AgentOutputSchema, Runner

from agent.models import EvaluatorResult
from agent.prompts import EVALUATOR_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_agent = Agent(
    name="Evaluator",
    instructions=EVALUATOR_SYSTEM_PROMPT,
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    output_type=AgentOutputSchema(EvaluatorResult, strict_json_schema=False),
)


async def evaluate(
    worker_output: str,
    task_description: str,
    success_criteria: str,
) -> EvaluatorResult:
    """Evaluate worker output against success criteria.

    Args:
        worker_output: The output produced by the worker
        task_description: Original task description
        success_criteria: Criteria to evaluate against

    Returns:
        EvaluatorResult with pass/fail decision and feedback
    """
    logger.info("🔍 EVALUATOR: Starting evaluation")
    logger.info(f"   Criteria: {success_criteria[:80]}...")

    context = f"""Task Description: {task_description}

Success Criteria: {success_criteria}

Worker Output:
{worker_output}

Evaluate this output against the success criteria and provide your assessment."""

    result = await Runner.run(
        _agent,
        input=context,
    )

    eval_result = result.final_output
    status = "PASS" if eval_result.passed else "FAIL"
    logger.info(f"🔍 EVALUATOR: Result = {status} (score: {eval_result.score}/100)")

    return eval_result
