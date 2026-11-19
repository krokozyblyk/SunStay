from __future__ import annotations

import asyncio
import json
import statistics
import time

import httpx

BASE = "http://localhost:8000"


async def timed(client: httpx.AsyncClient, url: str, params: dict | None = None) -> tuple[float, int]:
    start = time.perf_counter()
    try:
        response = await client.get(url, params=params)
        return time.perf_counter() - start, response.status_code
    except Exception:
        return time.perf_counter() - start, 0


async def run_batch(url: str, params: dict | None, total: int, concurrency: int) -> dict:
    latencies: list[float] = []
    statuses: list[int] = []
    semaphore = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient(timeout=30.0) as client:
        async def worker() -> None:
            async with semaphore:
                elapsed, status = await timed(client, url, params)
                latencies.append(elapsed)
                statuses.append(status)

        started = time.perf_counter()
        await asyncio.gather(*(worker() for _ in range(total)))
        wall = time.perf_counter() - started

    latencies.sort()
    return {
        "url": url,
        "total": total,
        "concurrency": concurrency,
        "wall_seconds": round(wall, 3),
        "rps": round(total / wall, 2) if wall else 0,
        "avg_ms": round(statistics.mean(latencies) * 1000, 2) if latencies else 0,
        "p50_ms": round(latencies[int(len(latencies) * 0.50)] * 1000, 2) if latencies else 0,
        "p95_ms": round(latencies[int(len(latencies) * 0.95)] * 1000, 2) if latencies else 0,
        "p99_ms": round(latencies[int(len(latencies) * 0.99)] * 1000, 2) if latencies else 0,
        "errors": sum(1 for status in statuses if status != 200),
        "statuses": {str(status): statuses.count(status) for status in sorted(set(statuses))},
    }


async def main() -> None:
    results = [
        await run_batch(f"{BASE}/api/public/room-types", None, 200, 20),
        await run_batch(
            f"{BASE}/api/public/availability",
            {"checkin": "2026-12-20", "checkout": "2026-12-22", "guests": 2},
            100,
            10,
        ),
    ]
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
