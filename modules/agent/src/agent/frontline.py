import json
import logging
import os

from agents import Agent, Runner

from agent.prompts.frontline import FRONTLINE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_agent = Agent(
    name="Frontline",
    instructions=FRONTLINE_SYSTEM_PROMPT,
    model=os.getenv("OPENAI_MODEL", "gpt-5-chat-latest"),
)


async def process(
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
        _agent,
        input=context,
    )

    response_text = result.final_output.strip()

    if not response_text.startswith("```"):
        return _parse_decision(response_text, result.final_output)

    response_text = response_text.split("```")[1]
    if response_text.startswith("json"):
        response_text = response_text[4:]

    return _parse_decision(response_text, result.final_output)


def _parse_decision(response_text: str, fallback: str) -> tuple[bool, str]:
    """Parse the frontline decision from response text."""
    try:
        decision = json.loads(response_text)
    except json.JSONDecodeError:
        logger.warning("⚠️  FRONTLINE: Failed to parse response, handling as direct")
        return False, fallback

    if decision.get("route_to_orchestrator", False):
        reason = decision.get("reason", "Specialized task detected")
        logger.info(f"→ FRONTLINE: Routing to orchestrator ({reason})")
        return True, reason

    response = decision.get("response", "")
    logger.info("✓ FRONTLINE: Handled directly")
    return False, response
