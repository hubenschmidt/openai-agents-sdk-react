from abc import ABC, abstractmethod
from typing import Any

from agent.models import WorkerResult


class BaseWorker(ABC):
    """Abstract base class for all workers."""

    @abstractmethod
    async def execute(
        self,
        task_description: str,
        parameters: dict[str, Any],
        feedback: str | None = None,
    ) -> WorkerResult:
        """Execute the worker's task.

        Args:
            task_description: Description of what to accomplish
            parameters: Task-specific parameters
            feedback: Optional feedback from previous evaluation attempt

        Returns:
            WorkerResult with success status and output
        """
        pass
