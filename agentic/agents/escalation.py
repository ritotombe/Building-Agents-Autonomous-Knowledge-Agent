from typing import Dict, Any, Optional

from agentic.tools.vocareum_llm import complete
from agentic.tools.udahub_tools import escalate_ticket, append_ticket_message
from agentic.tools.vocareum import escalate_to_vocareum

SYSTEM = (
    "You are an escalation assistant. Given the user message and context, "
    "produce a short clear reason for escalation. Respond with ONLY the reason sentence."
)


def escalate(ticket_id: str, user_message: str, context: Dict[str, Any], last_confidence: Optional[float] = None) -> Dict[str, Any]:
    try:
        llm = complete(SYSTEM, f"Message: {user_message}\nContext: {context}\nConfidence: {last_confidence}")
        reason = llm.get("content", "Escalation required.").strip() if llm.get("ok") else "Escalation required."
    except Exception:
        reason = "Escalation required due to low confidence or policy guardrail."

    append_ticket_message(ticket_id=ticket_id, role="system", content=f"Escalation requested: {reason}")
    res = escalate_ticket(ticket_id=ticket_id, reason=reason, last_confidence=last_confidence)
    v = escalate_to_vocareum(ticket_id=ticket_id, reason=reason, payload={"last_confidence": last_confidence, "context": context})
    return {"udahub": res.__dict__, "vocareum": v.__dict__, "reason": reason}
