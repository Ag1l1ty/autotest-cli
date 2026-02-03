"""Async utilities for concurrent operations."""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine, TypeVar

T = TypeVar("T")


async def gather_with_limit(
    coros: list[Coroutine[Any, Any, T]],
    limit: int = 5,
) -> list[T]:
    """Run coroutines concurrently with a concurrency limit."""
    semaphore = asyncio.Semaphore(limit)
    
    async def limited(coro: Coroutine[Any, Any, T]) -> T:
        async with semaphore:
            return await coro

    return await asyncio.gather(*(limited(c) for c in coros))


async def run_in_executor(func: Callable[..., T], *args: Any) -> T:
    """Run a synchronous function in a thread executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)
