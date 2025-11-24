# runner.py — OpenAI Agents SDK + WebSocket streaming
# Orchestrator-evaluator pattern with specialized workers.
# Maintains the same WebSocket protocol for frontend compatibility.

import json
import logging
import os
from typing import Dict, List

from dotenv import load_dotenv
from fastapi import WebSocket

from agent.orchestrator import Orchestrator

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
logger = logging.getLogger("app.runner")
load_dotenv(override=True)

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    logger.warning("OPENAI_API_KEY is missing. Agent will not function until configured.")

# -----------------------------------------------------------------------------
# In-memory conversation storage (keyed by user_uuid)
# -----------------------------------------------------------------------------
_conversations: Dict[str, List[Dict[str, str]]] = {}
_orchestrator: Orchestrator | None = None


def get_conversation(user_uuid: str) -> List[Dict[str, str]]:
    """Get or create conversation history for a user."""
    if user_uuid not in _conversations:
        _conversations[user_uuid] = []
    return _conversations[user_uuid]


def get_orchestrator() -> Orchestrator:
    """Get or create the orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


def _extract_user_input(data: str | List[Dict[str, str]]) -> str:
    """Extract user input from message data."""
    if not isinstance(data, list):
        return str(data)
    user_messages = [m for m in data if m.get("role") == "user"]
    if not user_messages:
        return ""
    return user_messages[-1]["content"]


# -----------------------------------------------------------------------------
# WebSocket entrypoint (called by server.py)
# -----------------------------------------------------------------------------
async def handle_chat(
    websocket: WebSocket, data: str | List[Dict[str, str]], user_uuid: str
):
    """
    Main entry point called by server.py.
    Routes through orchestrator-worker-evaluator pattern.

    Args:
        websocket: FastAPI WebSocket connection
        data: User message (string) or list of messages
        user_uuid: Conversation identifier for memory
    """
    if not API_KEY:
        logger.warning("handle_chat called without API_KEY configured")
        error_msg = "OPENAI_API_KEY is not configured. Please set it in your environment."
        await websocket.send_text(json.dumps({"on_chat_model_stream": error_msg}))
        await websocket.send_text(json.dumps({"on_chat_model_end": True}))
        return

    user_input = _extract_user_input(data)
    if not user_input:
        logger.warning("Empty user input, skipping")
        return

    logger.info(f"Processing message: {user_input[:50]}")

    orchestrator = get_orchestrator()
    conversation = get_conversation(user_uuid)
    conversation.append({"role": "user", "content": user_input})

    try:
        logger.info("Starting orchestrator processing")

        await websocket.send_text(
            json.dumps({"on_chat_model_stream": "Processing your request..."})
        )

        response = await orchestrator.process(user_input, conversation)

        await websocket.send_text(json.dumps({"on_chat_model_stream": "\n\n"}))
        await websocket.send_text(json.dumps({"on_chat_model_stream": response}))
        await websocket.send_text(json.dumps({"on_chat_model_end": True}))

        conversation.append({"role": "assistant", "content": response})
        logger.info("Orchestrator processing complete")

    except Exception as e:
        logger.exception(f"Orchestrator run failed: {e}")
        error_msg = "Sorry—there was an error generating the response."
        await websocket.send_text(
            json.dumps({"on_chat_model_stream": error_msg})
        )
        await websocket.send_text(json.dumps({"on_chat_model_end": True}))
        conversation.append({"role": "assistant", "content": error_msg})
