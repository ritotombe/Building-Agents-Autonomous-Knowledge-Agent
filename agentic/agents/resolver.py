from typing import Dict, Any

from agentic.tools.kb_tool import knowledge_search
from agentic.tools.vocareum_llm import complete

SYSTEM = (
    "You are a support answerer. Given a user query and candidate knowledge snippets, "
    "compose a concise, accurate answer. If confidence is low, say 'ESCALATE' only."
)


def resolve(account_id: str, query: str, min_confidence: float = 0.55) -> Dict[str, Any]:
    res = knowledge_search(account_id=account_id, query=query, top_k=3, min_confidence=min_confidence)
    if not res.ok:
        return {"ok": False, "reason": "search_failed"}
    data = res.data
    snippets = "\n\n".join([f"- {r['title']}: {r['snippet']} (score={r['score']})" for r in data["results"]])

    try:
        llm = complete(SYSTEM, f"Query: {query}\n\nSnippets:\n{snippets}\n\nBest score: {data['best_score']}")
        if llm.get("ok"):
            content = llm.get("content", "").strip()
            if not data["meets_threshold"] or content.upper() == "ESCALATE":
                return {"ok": False, "reason": "low_confidence", "best_score": data["best_score"], "results": data["results"]}
            return {"ok": True, "answer": content, "citations": data["results"], "best_score": data["best_score"]}
        return {"ok": False, "reason": "llm_failed"}
    except Exception:
        return {"ok": False, "reason": "llm_exception"}
