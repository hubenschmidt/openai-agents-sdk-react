import logging
import os
from typing import Any

from agents import Agent, AgentOutputSchema, Runner

from agent.evaluator import Evaluator
from agent.models import OrchestratorDecision, WorkerResult, WorkerType
from agent.prompts import ORCHESTRATOR_SYSTEM_PROMPT
from agent.workers import EmailWorker, GeneralWorker, SearchWorker

logger = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrator agent that routes requests to workers and manages evaluation loop."""

    MAX_RETRIES = 3

    def __init__(self):
        self.agent = Agent(
            name="Orchestrator",
            instructions=ORCHESTRATOR_SYSTEM_PROMPT,
            model=os.getenv("OPENAI_MODEL", "gpt-5-chat-latest"),
            output_type=AgentOutputSchema(OrchestratorDecision, strict_json_schema=False),
        )
        self.evaluator = Evaluator()
        self.workers = {
            WorkerType.SEARCH: SearchWorker(),
            WorkerType.EMAIL: EmailWorker(),
            WorkerType.GENERAL: GeneralWorker(),
        }

    async def process(
        self,
        user_input: str,
        conversation_history: list[dict[str, str]],
    ) -> str:
        """Process user input through orchestrator-worker-evaluator flow.

        Args:
            user_input: The user's message
            conversation_history: Previous conversation messages

        Returns:
            Final response to send to user
        """
        logger.info("=" * 50)
        logger.info("▶️  ORCHESTRATOR: Starting request processing")
        logger.info(f"   User input: {user_input[:100]}...")

        decision = await self._route(user_input, conversation_history)

        logger.info(f"→ ORCHESTRATOR: Routing to {decision.worker_type.value}")
        logger.info(f"   Task: {decision.task_description[:100]}...")
        logger.info(f"   Success criteria: {decision.success_criteria[:100]}...")

        if decision.worker_type == WorkerType.NONE:
            logger.warning("⚠️  ORCHESTRATOR: No suitable worker found")
            return f"I'm unable to help with that request. {decision.task_description}"

        worker = self.workers.get(decision.worker_type)
        if not worker:
            logger.error(f"❌ ORCHESTRATOR: Worker {decision.worker_type} not available")
            return f"Worker {decision.worker_type} is not available."

        feedback = None
        for attempt in range(self.MAX_RETRIES):
            logger.info(f"🔄 ORCHESTRATOR: Attempt {attempt + 1}/{self.MAX_RETRIES}")

            worker_result = await worker.execute(
                task_description=decision.task_description,
                parameters=decision.parameters,
                feedback=feedback,
            )

            if not worker_result.success:
                logger.error(f"❌ WORKER: Failed with error: {worker_result.error}")
                return f"Error: {worker_result.error}"

            logger.info(f"✓ WORKER: Completed successfully")

            eval_result = await self.evaluator.evaluate(
                worker_output=worker_result.output,
                task_description=decision.task_description,
                success_criteria=decision.success_criteria,
            )

            if eval_result.passed:
                logger.info(f"✅ EVALUATOR: Passed (score: {eval_result.score}/100)")
                logger.info("=" * 50)
                return worker_result.output

            logger.info(f"⚠️  EVALUATOR: Failed (score: {eval_result.score}/100)")
            logger.info(f"   Feedback: {eval_result.feedback[:100]}...")

            feedback = f"{eval_result.feedback}\n\nSuggestions: {eval_result.suggestions}"

            if attempt == self.MAX_RETRIES - 1:
                logger.warning(f"⚠️  ORCHESTRATOR: Max retries reached, returning partial result")
                logger.info("=" * 50)
                return f"{worker_result.output}\n\n[Note: Response may not fully meet quality criteria after {self.MAX_RETRIES} attempts. Evaluator feedback: {eval_result.feedback}]"

        return worker_result.output

    async def _route(
        self,
        user_input: str,
        conversation_history: list[dict[str, str]],
    ) -> OrchestratorDecision:
        """Route user input to appropriate worker."""
        history_context = ""
        if conversation_history:
            recent = conversation_history[-6:]
            history_context = "\n".join(
                [f"{m['role'].upper()}: {m['content']}" for m in recent]
            )

        context = f"""Conversation History:
{history_context}

Current User Request: {user_input}

Analyze this request and determine which worker should handle it."""

        result = await Runner.run(
            self.agent,
            input=context,
        )

        return result.final_output
