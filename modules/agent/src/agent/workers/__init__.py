from typing import Any

from agent.models import WorkerResult, WorkerType
from agent.workers import email_worker, general_worker, search_worker

_workers = {
    WorkerType.SEARCH: search_worker.execute,
    WorkerType.EMAIL: email_worker.execute,
    WorkerType.GENERAL: general_worker.execute,
}


async def execute_worker(
    worker_type: WorkerType,
    task_description: str,
    parameters: dict[str, Any],
    feedback: str | None = None,
) -> WorkerResult:
    """Execute the appropriate worker based on type."""
    worker_fn = _workers.get(worker_type)
    if not worker_fn:
        return WorkerResult(
            success=False,
            output="",
            error=f"Worker {worker_type} not available",
        )

    return await worker_fn(task_description, parameters, feedback)


__all__ = ["execute_worker", "WorkerType"]
