from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WorkerType(str, Enum):
    SEARCH = "SEARCH"
    EMAIL = "EMAIL"
    GENERAL = "GENERAL"
    NONE = "NONE"


class OrchestratorDecision(BaseModel):
    """Structured output from the orchestrator agent."""

    worker_type: WorkerType = Field(description="The worker to route the request to")
    task_description: str = Field(description="Clear description of what the worker should accomplish")
    parameters: dict[str, Any] = Field(description="Relevant parameters extracted from user request")
    success_criteria: str = Field(description="Specific criteria for the evaluator to validate output")


class EvaluatorResult(BaseModel):
    """Structured output from the evaluator agent."""

    passed: bool = Field(description="Whether the output meets the success criteria")
    score: int = Field(ge=0, le=100, description="Numeric score from 0-100")
    feedback: str = Field(description="Detailed explanation of the evaluation")
    suggestions: str = Field(default="", description="Suggestions for improvement if failed")


class WorkerResult(BaseModel):
    """Result returned by a worker."""

    success: bool = Field(description="Whether the worker completed successfully")
    output: str = Field(description="The worker's output content")
    error: str | None = Field(default=None, description="Error message if failed")


class EmailParams(BaseModel):
    """Parameters for sending an email."""

    to: str = Field(description="Recipient email address")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body content")


class SearchParams(BaseModel):
    """Parameters for web search."""

    query: str = Field(description="Search query string")
    num_results: int = Field(default=5, description="Number of results to return")
