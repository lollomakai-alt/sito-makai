"""Server-side maintenance switch for public online bookings."""

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, StrictBool

from admin_auth import require_admin, require_browser_action
from database import db


class MaintenanceActive(Exception):
    pass


class MaintenanceChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    active: StrictBool


router = APIRouter(prefix="/api/admin", tags=["admin"])


def maintenance_active(connection):
    row = connection.execute(
        "SELECT active FROM private.site_maintenance WHERE id = true"
    ).fetchone()
    if not row or type(row.get("active")) is not bool:
        raise RuntimeError("Stato manutenzione non disponibile")
    return row["active"]


def ensure_online_open(connection):
    if maintenance_active(connection):
        raise MaintenanceActive()


def public_status():
    with db() as connection:
        return {"active": maintenance_active(connection)}


@router.get("/site-maintenance")
def admin_status(request: Request):
    require_admin(request, allowed_roles=("admin",))
    try:
        with db() as connection:
            active = maintenance_active(connection)
            history = connection.execute(
                "SELECT id, active, actor_id, created_at "
                "FROM private.site_maintenance_history ORDER BY id DESC LIMIT 50"
            ).fetchall()
        return {"active": active, "history": history}
    except Exception:
        raise HTTPException(status_code=503, detail="Stato manutenzione non disponibile.") from None


@router.post("/site-maintenance")
def change_status(body: MaintenanceChange, request: Request):
    require_browser_action(request)
    account = require_admin(request, allowed_roles=("admin",))
    try:
        with db(write=True) as connection:
            previous = maintenance_active(connection)
            if previous != body.active:
                connection.execute(
                    "UPDATE private.site_maintenance SET active = %s, updated_at = now(), "
                    "updated_by = %s WHERE id = true",
                    (body.active, account["username"]),
                )
                connection.execute(
                    "INSERT INTO private.site_maintenance_history (active, actor_id) "
                    "VALUES (%s, %s)",
                    (body.active, account["username"]),
                )
        return {"active": body.active}
    except Exception:
        raise HTTPException(status_code=503, detail="Cambio manutenzione non confermato.") from None
