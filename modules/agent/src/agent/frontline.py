import json
import logging
import os

from agents import Agent, Runner

from agent.prompts.frontline import FRONTLINE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class Frontline:
    """Fast frontline agent that handles chat directly or routes to orchestrator."""

    def __init__(self):
        self.agent = Agent(
            name="Frontline",
            instructions=FRONTLINE_SYSTEM_PROMPT,
            model=os.getenv("OPENAI_MODEL", "gpt-5-chat-latest"),
        )

    async def process(
        self,
        user_input: str,
        conversation_history: list[dict[str, str]],
    ) -> tuple[bool, str]:
        """Process user input and decide whether to handle directly or route.

        Args:
            user_input: The user's message
            conversation_history: Previous conversation messages

        Returns:
            Tuple of (should_route_to_orchestrator, response_or_reason)
        """
        logger.info("⚡ FRONTLINE: Processing request")
        logger.info(f"   Input: {user_input[:80]}...")

        history_context = ""
        if conversation_history:
            recent = conversation_history[-4:]
            history_context = "\n".join(
                [f"{m['role'].upper()}: {m['content']}" for m in recent]
            )

        context = f"""Recent conversation:
{history_context}

Current user message: {user_input}

Decide whether to handle this directly or route to the orchestrator."""

        result = await Runner.run(
            self.agent,
            input=context,
        )

        try:
            response_text = result.final_output.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]

            decision = json.loads(response_text)

            if decision.get("route_to_orchestrator", False):
                reason = decision.get("reason", "Specialized task detected")
                logger.info(f"→ FRONTLINE: Routing to orchestrator ({reason})")
                return True, reason
            else:
                response = decision.get("response", "")
                logger.info("✓ FRONTLINE: Handled directly")
                return False, response

        except json.JSONDecodeError:
            logger.warning("⚠️  FRONTLINE: Failed to parse response, handling as direct")
            return False, result.final_output
