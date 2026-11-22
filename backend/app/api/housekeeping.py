from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from psycopg import AsyncConnection

from ..db import get_db
from ..deps import require_permission
from ..notifications import notify_user
from ..schemas import (
    ConsumableWriteOff,
    HousekeepingTaskCreate,
    MaintenanceCreate,
    MaintenanceStatusUpdate,
    RoomStatusUpdate,
)
from ..utils import rows_to_dicts

router = APIRouter(prefix="/housekeeping", tags=["housekeeping"])


@router.get("/tasks")
async def tasks(
    status: str | None = None,
    floor: int | None = None,
    assignee_id: int | None = None,
    user: dict = Depends(require_permission("housekeeping:view")),
    conn: AsyncConnection = Depends(get_db),
):
    clauses: list[str] = []
    params: list = []
    if status:
        clauses.append("ht.status = %s")
        params.append(status)
    if floor is not None:
        clauses.append("r.floor = %s")
        params.append(floor)
    if assignee_id:
        clauses.append("ht.staff_id = %s")
        params.append(assignee_id)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    cur = await conn.execute(
        f"""
        SELECT ht.*, r.room_number, r.floor, rt.name AS room_type,
               rs.name AS room_status,
               u.full_name AS assignee_name
        FROM housekeeping_tasks ht
        JOIN rooms r ON r.room_id = ht.room_id
        JOIN room_types rt ON rt.room_type_id = r.room_type_id
        JOIN room_statuses rs ON rs.status_id = r.status_id
        LEFT JOIN users u ON u.user_id = ht.staff_id
        {where}
        ORDER BY
            CASE ht.status WHEN 'IN_PROGRESS' THEN 0 WHEN 'ASSIGNED' THEN 1 WHEN 'DONE' THEN 2 ELSE 3 END,
            ht.priority DESC,
            ht.assigned_at DESC
        """,
        tuple(params),
    )
    return rows_to_dicts(await cur.fetchall())


@router.post("/tasks")
async def create_task(
    payload: HousekeepingTaskCreate,
    request: Request,
    user: dict = Depends(require_permission("housekeeping:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        "SELECT fn_assign_housekeeping_task(%s::integer, %s::integer, %s::varchar, %s::varchar, %s::integer, %s::varchar) AS task_id",
        (
            payload.room_id,
            payload.staff_id,
            payload.task_type,
            payload.priority,
            user["user_id"],
            request.client.host if request.client else "",
        ),
    )
    task_id = (await cur.fetchone())["task_id"]
    if payload.staff_id:
        await notify_user(
            conn,
            payload.staff_id,
            "TASK_ASSIGNED",
            "Новое задание",
            f"Вам назначено задание #{task_id} в номере. Откройте доску хаускипинга.",
            "/app/housekeeping",
        )
    return {"task_id": task_id}


@router.post("/tasks/{task_id}/start")
async def start_task(
    task_id: int,
    request: Request,
    user: dict = Depends(require_permission("housekeeping:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        "CALL sp_start_housekeeping_task(%s::integer, %s::integer, %s::varchar)",
        (task_id, user["user_id"], request.client.host if request.client else ""),
    )
    return {"ok": True, "status": "IN_PROGRESS"}


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: int,
    request: Request,
    user: dict = Depends(require_permission("housekeeping:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        "CALL sp_complete_housekeeping_task(%s::integer, %s::integer, %s::varchar)",
        (task_id, user["user_id"], request.client.host if request.client else ""),
    )
    return {"ok": True, "status": "DONE"}


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: int,
    request: Request,
    user: dict = Depends(require_permission("housekeeping:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        "CALL sp_cancel_housekeeping_task(%s::integer, %s::integer, %s::varchar)",
        (task_id, user["user_id"], request.client.host if request.client else ""),
    )
    return {"ok": True, "status": "CANCELLED"}


@router.post("/tasks/{task_id}/consumables")
async def write_off_consumable(
    task_id: int,
    payload: ConsumableWriteOff,
    request: Request,
    user: dict = Depends(require_permission("consumables:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        "SELECT fn_write_off_consumable(%s::integer, %s::integer, %s::numeric, %s::integer, %s::varchar) AS usage_id",
        (
            task_id,
            payload.consumable_id,
            payload.quantity,
            user["user_id"],
            request.client.host if request.client else "",
        ),
    )
    return {"usage_id": (await cur.fetchone())["usage_id"]}


@router.get("/consumables")
async def consumables(
    user: dict = Depends(require_permission("consumables:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute("SELECT * FROM v_consumables_stock ORDER BY name")
    return rows_to_dicts(await cur.fetchall())


@router.get("/maintenance")
async def maintenance(
    status: str | None = None,
    user: dict = Depends(require_permission("maintenance:view")),
    conn: AsyncConnection = Depends(get_db),
):
    params: list = []
    status_filter = ""
    if status:
        status_filter = "WHERE mr.status = %s"
        params.append(status)
    cur = await conn.execute(
        f"""
        SELECT mr.*, r.room_number, r.floor,
               u.full_name AS assignee_name,
               ht.task_type
        FROM maintenance_requests mr
        JOIN rooms r ON r.room_id = mr.room_id
        LEFT JOIN users u ON u.user_id = mr.assigned_to
        LEFT JOIN housekeeping_tasks ht ON ht.task_id = mr.task_id
        {status_filter}
        ORDER BY
            CASE mr.priority WHEN 'URGENT' THEN 0 WHEN 'HIGH' THEN 1 WHEN 'NORMAL' THEN 2 ELSE 3 END,
            mr.created_at DESC
        """,
        tuple(params),
    )
    return rows_to_dicts(await cur.fetchall())


@router.post("/maintenance")
async def create_maintenance(
    payload: MaintenanceCreate,
    request: Request,
    user: dict = Depends(require_permission("maintenance:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        """
        SELECT fn_create_maintenance_request(
            %s::integer, %s::integer, %s::text, %s::varchar, %s::integer, %s::integer, %s::varchar
        ) AS request_id
        """,
        (
            payload.room_id,
            payload.task_id,
            payload.description,
            payload.priority,
            payload.assigned_to,
            user["user_id"],
            request.client.host if request.client else "",
        ),
    )
    return {"request_id": (await cur.fetchone())["request_id"]}


@router.patch("/maintenance/{request_id}/status")
async def update_maintenance_status(
    request_id: int,
    payload: MaintenanceStatusUpdate,
    request: Request,
    user: dict = Depends(require_permission("maintenance:manage")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        "CALL sp_update_maintenance_status(%s::integer, %s::varchar, %s::integer, %s::varchar)",
        (request_id, payload.status, user["user_id"], request.client.host if request.client else ""),
    )
    return {"ok": True, "status": payload.status}


@router.get("/rooms")
async def rooms(
    user: dict = Depends(require_permission("rooms:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        """
        SELECT r.room_id, r.room_number, r.floor, rt.name AS room_type,
               rs.name AS status, br.name AS block_reason
        FROM rooms r
        JOIN room_types rt ON rt.room_type_id = r.room_type_id
        JOIN room_statuses rs ON rs.status_id = r.status_id
        LEFT JOIN block_reasons br ON br.reason_id = r.block_reason_id
        ORDER BY r.room_number
        """
    )
    return rows_to_dicts(await cur.fetchall())


@router.post("/rooms/{room_id}/status")
async def update_room_status(
    room_id: int,
    payload: RoomStatusUpdate,
    request: Request,
    user: dict = Depends(require_permission("rooms:update_status")),
    conn: AsyncConnection = Depends(get_db),
):
    await conn.execute(
        "CALL sp_set_room_status(%s::integer, %s::varchar, %s::integer, %s::integer, %s::varchar)",
        (
            room_id,
            payload.status_name,
            payload.reason_id,
            user["user_id"],
            request.client.host if request.client else "",
        ),
    )
    return {"ok": True}


@router.get("/staff")
async def staff(
    user: dict = Depends(require_permission("housekeeping:view")),
    conn: AsyncConnection = Depends(get_db),
):
    cur = await conn.execute(
        """
        SELECT u.user_id, u.full_name, u.email, r.name AS role_name
        FROM users u
        JOIN roles r ON r.role_id = u.role_id
        WHERE u.role_id = 3 AND u.is_active
        ORDER BY u.full_name
        """
    )
    return rows_to_dicts(await cur.fetchall())
