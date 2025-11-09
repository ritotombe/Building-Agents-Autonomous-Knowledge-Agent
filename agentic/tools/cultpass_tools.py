from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session

from data.models import cultpass
from .db_paths import CULTPASS_DB


@dataclass
class ToolResult:
    ok: bool
    data: Any | None = None
    error: Optional[Dict[str, Any]] = None


def _open_session(db_path=CULTPASS_DB) -> Session:
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    cultpass.Base.metadata.create_all(engine)
    return Session(bind=engine)


def get_user_profile(external_user_id: str) -> ToolResult:
    with _open_session() as session:
        user = session.query(cultpass.User).filter_by(user_id=external_user_id).first()
        if not user:
            return ToolResult(ok=False, error={"code": "NOT_FOUND", "message": "User not found"})
        return ToolResult(ok=True, data={
            "user_id": user.user_id,
            "full_name": user.full_name,
            "email": user.email,
            "is_blocked": bool(user.is_blocked),
        })


def get_subscription_status(user_id: str, now: Optional[datetime] = None) -> ToolResult:
    now = now or datetime.utcnow()
    with _open_session() as session:
        sub = session.query(cultpass.Subscription).filter_by(user_id=user_id).first()
        if not sub:
            return ToolResult(ok=False, error={"code": "NO_SUB", "message": "Subscription not found"})
        # compute usage in current month
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        used = (
            session.query(cultpass.Reservation)
            .filter(
                cultpass.Reservation.user_id == user_id,
                cultpass.Reservation.created_at >= month_start,
                cultpass.Reservation.status == "reserved",
            )
            .count()
        )
        remaining = max(0, int(sub.monthly_quota) - used)
        return ToolResult(ok=True, data={
            "status": sub.status,
            "tier": sub.tier,
            "monthly_quota": int(sub.monthly_quota),
            "used_this_month": used,
            "remaining_quota": remaining,
        })


def list_reservations(user_id: str, upcoming_only: bool = True) -> ToolResult:
    with _open_session() as session:
        q = (
            session.query(cultpass.Reservation, cultpass.Experience)
            .join(cultpass.Experience, cultpass.Reservation.experience_id == cultpass.Experience.experience_id)
            .filter(cultpass.Reservation.user_id == user_id)
        )
        if upcoming_only:
            q = q.filter(cultpass.Experience.when >= datetime.utcnow())
        items = []
        for r, e in q.all():
            items.append({
                "reservation_id": r.reservation_id,
                "experience_id": e.experience_id,
                "title": e.title,
                "when": e.when.isoformat(),
                "status": r.status,
            })
        return ToolResult(ok=True, data={"reservations": items})


def reserve_experience(user_id: str, experience_id: str) -> ToolResult:
    with _open_session() as session:
        user = session.query(cultpass.User).filter_by(user_id=user_id).first()
        if not user:
            return ToolResult(ok=False, error={"code": "USER_NOT_FOUND", "message": "User not found"})
        if user.is_blocked:
            return ToolResult(ok=False, error={"code": "BLOCKED", "message": "User is blocked"})

        sub = session.query(cultpass.Subscription).filter_by(user_id=user_id).first()
        if not sub or sub.status != "active":
            return ToolResult(ok=False, error={"code": "INACTIVE_SUB", "message": "Subscription inactive"})

        status = get_subscription_status(user_id)
        if not status.ok or status.data["remaining_quota"] <= 0:
            return ToolResult(ok=False, error={"code": "NO_QUOTA", "message": "Monthly quota exhausted"})

        exp = session.query(cultpass.Experience).filter_by(experience_id=experience_id).first()
        if not exp:
            return ToolResult(ok=False, error={"code": "EXP_NOT_FOUND", "message": "Experience not found"})
        if exp.slots_available <= 0:
            return ToolResult(ok=False, error={"code": "NO_SLOTS", "message": "No slots available"})

        new_res = cultpass.Reservation(
            reservation_id=str(uuid.uuid4())[:6],
            user_id=user_id,
            experience_id=experience_id,
            status="reserved",
        )
        exp.slots_available = int(exp.slots_available) - 1
        session.add(new_res)
        session.commit()
        return ToolResult(ok=True, data={"reservation_id": new_res.reservation_id})


def cancel_reservation(reservation_id: str, user_id: str) -> ToolResult:
    with _open_session() as session:
        r = session.query(cultpass.Reservation).filter_by(reservation_id=reservation_id, user_id=user_id).first()
        if not r:
            return ToolResult(ok=False, error={"code": "NOT_FOUND", "message": "Reservation not found"})
        if r.status != "reserved":
            return ToolResult(ok=False, error={"code": "INVALID_STATE", "message": "Reservation not active"})
        r.status = "cancelled"
        # return slot
        exp = session.query(cultpass.Experience).filter_by(experience_id=r.experience_id).first()
        if exp:
            exp.slots_available = int(exp.slots_available) + 1
        session.commit()
        return ToolResult(ok=True, data={"reservation_id": r.reservation_id, "status": r.status})
