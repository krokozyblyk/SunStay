from __future__ import annotations

import csv
import io
from contextlib import asynccontextmanager
from datetime import date, timedelta
from typing import Any

import jwt
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

DATABASE_URL = __import__("os").getenv(
    "ANALYTICS_DATABASE_URL",
    "postgresql://sunstay_analytics:sunstay_analytics@localhost:5432/hotel",
)
JWT_SECRET = __import__("os").getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = __import__("os").getenv("JWT_ALGORITHM", "HS256")
CORS_ORIGINS = __import__("os").getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:8080,http://localhost"
).split(",")

pool: AsyncConnectionPool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = AsyncConnectionPool(
        conninfo=DATABASE_URL,
        min_size=1,
        max_size=5,
        open=False,
        kwargs={"row_factory": dict_row, "autocommit": True, "options": "-c search_path=public,extensions"},
    )
    await pool.open()
    await pool.wait()
    yield
    await pool.close()


app = FastAPI(
    title="SunStay Analytics",
    description="Микросервис статистики и отчётности гостиницы SunStay.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[item.strip() for item in CORS_ORIGINS if item.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_conn():
    assert pool is not None
    async with pool.connection() as conn:
        yield conn


async def require_reports(request: Request) -> dict[str, Any]:
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    try:
        payload = jwt.decode(
            header.split(" ", 1)[1],
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    if payload.get("role") not in ("MANAGER", "HOTEL_MANAGER", "DB_ADMIN"):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return payload


def json_rows(rows):
    result = []
    for row in rows:
        item = {}
        for key, value in row.items():
            if isinstance(value, (date,)):
                value = value.isoformat()
            else:
                try:
                    value = float(value) if value.__class__.__name__ == "Decimal" else value
                except Exception:
                    pass
            item[key] = value
        result.append(item)
    return result


def csv_export(rows: list[dict], filename: str) -> StreamingResponse:
    buffer = io.StringIO()
    buffer.write("\ufeff")
    if rows:
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    content = buffer.getvalue().encode("utf-8")
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def period(date_from: date | None, date_to: date | None) -> tuple[date, date]:
    end = date_to or date.today()
    start = date_from or (end - timedelta(days=30))
    if end < start:
        raise HTTPException(status_code=400, detail="Некорректный период")
    return start, end


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "analytics"}


@app.get("/api/reports/occupancy")
async def occupancy(
    date_from: date | None = None,
    date_to: date | None = None,
    room_type_id: int | None = None,
    format: str = "json",
    _: dict = Depends(require_reports),
    conn=Depends(get_conn),
):
    start, end = period(date_from, date_to)
    if room_type_id:
        cur = await conn.execute(
            """
            SELECT report_date, room_type_id, room_type, rooms_total AS rooms_available,
                   rooms_occupied, occupancy_pct
            FROM v_occupancy_by_type
            WHERE report_date BETWEEN %s AND %s AND room_type_id = %s
            ORDER BY report_date
            """,
            (start, end, room_type_id),
        )
    else:
        cur = await conn.execute(
            """
            SELECT report_date, rooms_occupied, rooms_available, occupancy_pct
            FROM v_occupancy_daily
            WHERE report_date BETWEEN %s AND %s
            ORDER BY report_date
            """,
            (start, end),
        )
    rows = json_rows(await cur.fetchall())
    if format == "csv":
        return csv_export(rows, "occupancy.csv")
    avg = round(sum(float(row["occupancy_pct"] or 0) for row in rows) / len(rows), 2) if rows else 0
    return {
        "series": rows,
        "summary": {
            "average_occupancy": avg,
            "room_nights_sold": sum(int(row["rooms_occupied"] or 0) for row in rows),
            "room_nights_available": sum(int(row["rooms_available"] or 0) for row in rows),
        },
    }


@app.get("/api/reports/adr-revpar")
async def adr_revpar(
    date_from: date | None = None,
    date_to: date | None = None,
    format: str = "json",
    _: dict = Depends(require_reports),
    conn=Depends(get_conn),
):
    start, end = period(date_from, date_to)
    cur = await conn.execute(
        """
        SELECT report_date, room_revenue, rooms_sold, rooms_available, adr, revpar
        FROM v_adr_revpar_daily
        WHERE report_date BETWEEN %s AND %s
        ORDER BY report_date
        """,
        (start, end),
    )
    rows = json_rows(await cur.fetchall())
    if format == "csv":
        return csv_export(rows, "adr-revpar.csv")
    revenue = sum(float(row["room_revenue"] or 0) for row in rows)
    sold = sum(int(row["rooms_sold"] or 0) for row in rows)
    available = sum(int(row["rooms_available"] or 0) for row in rows)
    return {
        "series": rows,
        "summary": {
            "room_revenue": round(revenue, 2),
            "adr": round(revenue / sold, 2) if sold else 0,
            "revpar": round(revenue / available, 2) if available else 0,
        },
    }


@app.get("/api/reports/cancellations")
async def cancellations(
    date_from: date | None = None,
    date_to: date | None = None,
    format: str = "json",
    _: dict = Depends(require_reports),
    conn=Depends(get_conn),
):
    start, end = period(date_from, date_to)
    cur = await conn.execute(
        "SELECT * FROM v_cancellations_monthly WHERE month BETWEEN %s AND %s ORDER BY month",
        (start, end),
    )
    months = json_rows(await cur.fetchall())
    cur = await conn.execute(
        "SELECT * FROM v_cancellation_reasons WHERE month BETWEEN %s AND %s ORDER BY month, bookings DESC",
        (start, end),
    )
    reasons = json_rows(await cur.fetchall())
    if format == "csv":
        return csv_export(months, "cancellations.csv")
    return {"months": months, "reasons": reasons}


@app.get("/api/reports/room-status")
async def room_status(
    format: str = "json",
    _: dict = Depends(require_reports),
    conn=Depends(get_conn),
):
    cur = await conn.execute("SELECT * FROM v_room_status_today ORDER BY status")
    rows = json_rows(await cur.fetchall())
    if format == "csv":
        return csv_export(rows, "room-status.csv")
    return {"items": rows}


@app.get("/api/reports/consumables")
async def consumables(
    format: str = "json",
    _: dict = Depends(require_reports),
    conn=Depends(get_conn),
):
    cur = await conn.execute("SELECT * FROM v_consumables_stock ORDER BY name")
    rows = json_rows(await cur.fetchall())
    if format == "csv":
        return csv_export(rows, "consumables.csv")
    return {"items": rows}


@app.get("/api/reports/revenue-by-service")
async def revenue_by_service(
    date_from: date | None = None,
    date_to: date | None = None,
    format: str = "json",
    _: dict = Depends(require_reports),
    conn=Depends(get_conn),
):
    start, end = period(date_from, date_to)
    cur = await conn.execute(
        "SELECT * FROM v_revenue_by_service WHERE month BETWEEN %s AND %s ORDER BY month, revenue DESC",
        (start, end),
    )
    rows = json_rows(await cur.fetchall())
    if format == "csv":
        return csv_export(rows, "revenue-by-service.csv")
    return {"items": rows}
