from typing import Dict, Any

from agentic.tools.cultpass_tools import (
    get_user_profile,
    get_subscription_status,
    list_reservations,
    reserve_experience,
    cancel_reservation,
)
from agentic.tools.vocareum_llm import complete

SYSTEM = (
    "You are a tool selector for support operations. Given the user message and context, "
    "choose one action from: get_user_profile, get_subscription_status, list_reservations, reserve_experience, cancel_reservation. "
    "Respond ONLY as JSON with keys: action, args."
)


TOOL_MAP = {
    "get_user_profile": lambda a: get_user_profile(a["external_user_id"]).__dict__,
    "get_subscription_status": lambda a: get_subscription_status(a["user_id"]).__dict__,
    "list_reservations": lambda a: list_reservations(a["user_id"], a.get("upcoming_only", True)).__dict__,
    "reserve_experience": lambda a: reserve_experience(a["user_id"], a["experience_id"]).__dict__,
    "cancel_reservation": lambda a: cancel_reservation(a["reservation_id"], a["user_id"]).__dict__,
}


def operate(message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        prompt = (
            f"User message: {message}\n" 
            f"Context: {context}\n"
        )
        llm = complete(SYSTEM, prompt)
        if not llm.get("ok"):
            return {"ok": False, "error": {"code": "LLM_ERROR", "message": str(llm.get('error'))}}
        import json as _json
        parsed = _json.loads(llm.get("content", "{}"))
        action = parsed.get("action")
        args = parsed.get("args", {})
        if action not in TOOL_MAP:
            return {"ok": False, "error": {"code": "BAD_ACTION", "message": action}}
        merged = {**{k: v for k, v in context.items() if k in {"user_id", "experience_id", "reservation_id", "external_user_id"}}, **args}
        return TOOL_MAP[action](merged)
    except Exception as e:
        return {"ok": False, "error": {"code": "LLM_OR_TOOL_ERROR", "message": str(e)}}
