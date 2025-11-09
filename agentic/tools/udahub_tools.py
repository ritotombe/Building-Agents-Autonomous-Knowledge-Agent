from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from data.models import udahub
from .db_paths import UDAHUB_DB


@dataclass
class ToolResult:
    ok: bool
    data: Any | None = None
    error: Optional[Dict[str, Any]] = None


def _open_session(db_path=UDAHUB_DB) -> Session:
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    udahub.Base.metadata.create_all(engine)
    return Session(bind=engine)


def append_ticket_message(ticket_id: str, role: str, content: str) -> ToolResult:
    with _open_session() as session:
        m = udahub.TicketMessage(
            message_id=str(uuid.uuid4()),
            ticket_id=ticket_id,
            role=udahub.RoleEnum(role),
            content=content,
        )
        session.add(m)
        session.commit()
        return ToolResult(ok=True, data={"message_id": m.message_id})


def get_ticket_history(ticket_id: str) -> ToolResult:
    with _open_session() as session:
        msgs = (
            session.query(udahub.TicketMessage)
            .filter_by(ticket_id=ticket_id)
            .order_by(udahub.TicketMessage.created_at.asc())
            .all()
        )
        data = [
            {
                "message_id": m.message_id,
                "role": m.role.name,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in msgs
        ]
        return ToolResult(ok=True, data={"messages": data})


def escalate_ticket(ticket_id: str, reason: str, last_confidence: float | None = None) -> ToolResult:
    with _open_session() as session:
        meta = session.query(udahub.TicketMetadata).filter_by(ticket_id=ticket_id).first()
        if not meta:
            return ToolResult(ok=False, error={"code": "NOT_FOUND", "message": "Ticket metadata not found"})
        meta.status = "escalated"
        # optionally append a message describing the escalation
        m = udahub.TicketMessage(
            message_id=str(uuid.uuid4()),
            ticket_id=ticket_id,
            role=udahub.RoleEnum.system,
            content=f"Escalated: {reason}. Confidence={last_confidence}",
        )
        session.add(m)
        session.commit()
        return ToolResult(ok=True, data={"status": meta.status})
