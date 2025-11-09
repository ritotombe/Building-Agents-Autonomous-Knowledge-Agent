from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import math
import re

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


def _score(text: str, query: str) -> float:
    # simple token overlap score [0,1]
    if not text or not query:
        return 0.0
    tokens = set(re.findall(r"[a-zA-Z0-9]+", text.lower()))
    qtokens = set(re.findall(r"[a-zA-Z0-9]+", query.lower()))
    if not qtokens:
        return 0.0
    inter = len(tokens & qtokens)
    return inter / float(len(qtokens))


def knowledge_search(account_id: str, query: str, top_k: int = 3, min_confidence: float = 0.5) -> ToolResult:
    with _open_session() as session:
        rows = (
            session.query(udahub.Knowledge)
            .filter(udahub.Knowledge.account_id == account_id)
            .all()
        )
        scored: List[Dict[str, Any]] = []
        for r in rows:
            score = max(_score(r.title, query), _score(r.content, query))
            if score > 0:
                snippet = (r.content[:200] + "...") if r.content and len(r.content) > 200 else r.content
                scored.append({
                    "article_id": r.article_id,
                    "title": r.title,
                    "snippet": snippet,
                    "score": round(score, 3),
                })
        scored.sort(key=lambda x: x["score"], reverse=True)
        results = scored[:top_k]
        best = results[0]["score"] if results else 0.0
        return ToolResult(ok=True, data={
            "results": results,
            "best_score": best,
            "meets_threshold": best >= float(min_confidence),
        })
