from typing import Dict

from agentic.tools.vocareum_llm import complete

DEFAULT_SYSTEM = (
    "You are a routing classifier for a support agent. "
    "Classify the user's message into one of: login, subscription, reservation, knowledge. "
    "Respond with ONLY the label."
)


def classify(text: str) -> Dict[str, str]:
    try:
        llm = complete(DEFAULT_SYSTEM, text)
        if llm.get("ok"):
            label = llm.get("content", "").strip().split()[0].lower()
            if label in {"login", "subscription", "reservation", "knowledge"}:
                return {"intent": label}
        return {"intent": "unknown"}
    except Exception:
        return {"intent": "unknown"}
