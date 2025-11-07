# SPDX-License-Identifier: NOASSERTION
# Copyright (c) 2025 Shahin

"""Simple Engine for task queuing and concurrent execution.

This module handles parallel execution of multiple Agents. Goal: Simple policy, error handling, and concurrency limitation.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, List, Optional, Tuple

from .agent_core import create_agent

logger = logging.getLogger(__name__)


class TaskEngine:
    """Manage task queue and execute them concurrently with configurable limitation.

    Parameters:
    - concurrency: Number of concurrent executions (execution quantum); default 3
    """

    def __init__(self, *, concurrency: int = 3) -> None:
        self.queue: List[Tuple[str, str]] = []
        self._concurrency = max(1, int(concurrency))

    def add_task(self, task: str, mode: str = "browser") -> None:
        """Add a new task to the queue.

        task: Task text for Agent
        mode: 'browser' or 'code'
        """
        self.queue.append((task, mode))

    async def run_all(self) -> List[Optional[str]]:
        """Execute all tasks and return a list of results (or None in case of error)."""

        # Semaphore to limit the number of concurrent executions
        sem = asyncio.Semaphore(self._concurrency)

        async def _wrapped_run(task: str, mode: str) -> Optional[str]:
            async with sem:
                return await self.run_task(task, mode)

        coros = [_wrapped_run(t, m) for t, m in self.queue]
        # return_exceptions=False -> we catch and handle exceptions
        results = await asyncio.gather(*coros)
        return results

    async def run_task(self, task: str, mode: str) -> Optional[str]:
        """Execute a single task and return the final result (or None in case of error).

        This function handles and logs exceptions.
        """
        logger.info("🚀 Running: %s", task)
        agent = create_agent(task, mode)
        try:
            history: Any = await agent.run()
            # Some Agents might return a different type of history; we try
            # to access the final_result method first, and if not available, return a string representation of history.
            try:
                result = history.final_result()
            except Exception:
                result = str(history)

            logger.info("✅ Done: %s", task)
            return result
        except Exception as exc:
            logger.exception("❌ Failed: %s", task)
            return None