from __future__ import annotations

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from psycopg import AsyncConnection
from psycopg.types.json import Jsonb

from ..db import get_db
from ..deps import require_permission
from ..schemas import ImportCommitRequest

router = APIRouter(prefix="/imports", tags=["imports"])

BANK_COLUMNS = {"date", "amount", "method", "booking_id", "folio_id", "external_ref"}
RATE_COLUMNS = {"room_type", "name", "season_start", "season_end", "price_per_night", "cancellation_terms"}
METHODS = {"CARD", "CASH", "BANK_TRANSFER", "ONLINE"}


def parse_date(value: str) -> str:
    value = (value or "").strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError("неверная дата")


def parse_amount(value: str) -> float:
    value = (value or "").strip().replace(" ", "").replace(",", ".")
    amount = float(value)
    if amount <= 0:
        raise ValueError("сумма должна быть больше нуля")
    return amount


def read_csv(upload: UploadFile, required: set[str]) -> list[dict[str, str]]:
    raw = upload.file.read()
    if isinstance(raw, bytes):
        text = raw.decode("utf-8-sig", errors="replace")
    else:
        text = raw
    if not text.strip():
        raise HTTPException(status_code=400, detail="Файл пуст")
    delimiter = ";" if ";" in text.splitlines()[0] else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="Не найдена строка заголовков")
    normalized = {name.strip() for name in reader.fieldnames}
    missing = required - normalized
    if missing:
        raise HTTPException(status_code=400, detail=f"Нет колонок: {', '.join(sorted(missing))}")
    return [{key.strip(): (value or "").strip() for key, value in row.items() if key} for row in reader]


@router.post("/bank-statement/preview")
async def bank_statement_preview(
    file: UploadFile = File(...),
    conn: AsyncConnection = Depends(get_db),
    user: dict = Depends(require_permission("imports:bank")),
):
    rows = read_csv(file, {"date", "amount", "method"})
    result = []
    valid = 0
    errors = 0
    for index, row in enumerate(rows, start=2):
        item = {"row": index, **row, "status": "ok", "error": None, "folio_id": None}
        try:
            item["date"] = parse_date(row["date"])
            item["amount"] = parse_amount(row["amount"])
            method = (row.get("method") or "").upper()
            if method not in METHODS:
                raise ValueError("недопустимый способ оплаты")
            item["method"] = method
            folio_id = None
            if row.get("folio_id"):
                folio_id = int(row["folio_id"])
            elif row.get("booking_id"):
                cur = await conn.execute(
                    """
                    SELECT folio_id FROM folios
                    WHERE booking_id = %s
                    ORDER BY folio_id DESC LIMIT 1
                    """,
                    (int(row["booking_id"]),),
                )
                folio = await cur.fetchone()
                if not folio:
                    raise ValueError("folio для брони не найден")
                folio_id = folio["folio_id"]
            else:
                raise ValueError("нужен booking_id или folio_id")
            cur = await conn.execute(
                "SELECT status FROM folios WHERE folio_id = %s",
                (folio_id,),
            )
            folio_row = await cur.fetchone()
            if not folio_row:
                raise ValueError("folio не найден")
            if folio_row["status"] != "OPEN":
                raise ValueError("folio закрыт")
            if row.get("external_ref"):
                cur = await conn.execute(
                    "SELECT 1 FROM payments WHERE external_ref = %s",
                    (row["external_ref"],),
                )
                if await cur.fetchone():
                    raise ValueError("платёж с таким external_ref уже существует")
            item["folio_id"] = folio_id
            valid += 1
        except (ValueError, TypeError) as exc:
            item["status"] = "error"
            item["error"] = str(exc)
            errors += 1
        result.append(item)
    return {"rows": result, "total": len(result), "valid": valid, "errors": errors}


@router.post("/bank-statement/commit")
async def bank_statement_commit(
    payload: ImportCommitRequest,
    conn: AsyncConnection = Depends(get_db),
    user: dict = Depends(require_permission("imports:bank")),
):
    valid_rows = [row for row in payload.rows if row.get("status") == "ok"]
    if not valid_rows:
        raise HTTPException(status_code=400, detail="Нет строк для загрузки")

    cur = await conn.execute(
        """
        INSERT INTO import_batches
            (import_type, filename, status, total_rows, success_rows, error_rows, created_by)
        VALUES ('BANK_STATEMENT', %s, 'PREVIEW', %s, %s, %s, %s)
        RETURNING import_id
        """,
        (payload.filename, len(payload.rows), len(valid_rows), len(payload.rows) - len(valid_rows), user["user_id"]),
    )
    import_id = (await cur.fetchone())["import_id"]

    for row in valid_rows:
        await conn.execute(
            """
            INSERT INTO payments (folio_id, amount, method, payment_type, external_ref)
            VALUES (%s, %s, %s, 'PAYMENT', %s)
            """,
            (
                int(row["folio_id"]),
                float(row["amount"]),
                row["method"],
                row.get("external_ref") or None,
            ),
        )

    await conn.execute(
        "UPDATE import_batches SET status = 'COMMITTED', committed_at = now() WHERE import_id = %s",
        (import_id,),
    )
    return {"ok": True, "import_id": import_id, "success_rows": len(valid_rows)}


@router.post("/rates/preview")
async def rates_preview(
    file: UploadFile = File(...),
    conn: AsyncConnection = Depends(get_db),
    user: dict = Depends(require_permission("imports:rates")),
):
    rows = read_csv(file, {"room_type", "name", "season_start", "season_end", "price_per_night"})
    result = []
    valid = 0
    errors = 0
    for index, row in enumerate(rows, start=2):
        item = {"row": index, **row, "status": "ok", "error": None, "room_type_id": None}
        try:
            cur = await conn.execute(
                "SELECT room_type_id FROM room_types WHERE lower(name) = lower(%s)",
                (row["room_type"],),
            )
            room_type = await cur.fetchone()
            if not room_type:
                raise ValueError("тип номера не найден")
            start = parse_date(row["season_start"])
            end = parse_date(row["season_end"])
            if end < start:
                raise ValueError("дата окончания раньше начала")
            price = parse_amount(row["price_per_night"])
            item.update(
                {
                    "room_type_id": room_type["room_type_id"],
                    "season_start": start,
                    "season_end": end,
                    "price_per_night": price,
                }
            )
            valid += 1
        except (ValueError, TypeError) as exc:
            item["status"] = "error"
            item["error"] = str(exc)
            errors += 1
        result.append(item)
    return {"rows": result, "total": len(result), "valid": valid, "errors": errors}


@router.post("/rates/commit")
async def rates_commit(
    payload: ImportCommitRequest,
    conn: AsyncConnection = Depends(get_db),
    user: dict = Depends(require_permission("imports:rates")),
):
    valid_rows = [row for row in payload.rows if row.get("status") == "ok"]
    if not valid_rows:
        raise HTTPException(status_code=400, detail="Нет строк для загрузки")

    cur = await conn.execute(
        """
        INSERT INTO import_batches
            (import_type, filename, status, total_rows, success_rows, error_rows, created_by)
        VALUES ('RATES', %s, 'PREVIEW', %s, %s, %s, %s)
        RETURNING import_id
        """,
        (payload.filename, len(payload.rows), len(valid_rows), len(payload.rows) - len(valid_rows), user["user_id"]),
    )
    import_id = (await cur.fetchone())["import_id"]

    for row in valid_rows:
        await conn.execute(
            """
            INSERT INTO rate_plans
                (room_type_id, name, season_start, season_end, price_per_night, cancellation_terms)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                int(row["room_type_id"]),
                row["name"],
                row["season_start"],
                row["season_end"],
                float(row["price_per_night"]),
                row.get("cancellation_terms") or None,
            ),
        )

    await conn.execute(
        "UPDATE import_batches SET status = 'COMMITTED', committed_at = now() WHERE import_id = %s",
        (import_id,),
    )
    return {"ok": True, "import_id": import_id, "success_rows": len(valid_rows)}
