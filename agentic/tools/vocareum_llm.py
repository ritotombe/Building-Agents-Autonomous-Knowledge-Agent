from __future__ import annotations

from typing import Any, Dict, Optional
import os
import httpx


def complete(system: str, user: str, model: Optional[str] = None) -> Dict[str, Any]:
    """Call OpenAI API directly to get a completion.

    Expected response shapes supported:
    - { "choices": [ { "message": { "content": "..." } } ] }
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"ok": False, "error": {"code": "NO_API_KEY", "message": "OPENAI_API_KEY not set"}}
    
    payload: Dict[str, Any] = {
        "model": model or "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        with httpx.Client(timeout=30.0, headers=headers) as client:
            resp = client.post("https://api.openai.com/v1/chat/completions", json=payload)
            
            if resp.status_code >= 200 and resp.status_code < 300:
                data = resp.json()
                content: Optional[str] = None
                
                # OpenAI chat completions format
                if isinstance(data.get("choices"), list) and data["choices"]:
                    try:
                        content = data["choices"][0].get("message", {}).get("content", "").strip()
                    except Exception:
                        pass
                
                if not content:
                    content = str(data)
                return {"ok": True, "content": content}
            else:
                return {"ok": False, "error": {"code": "HTTP_ERROR", "message": resp.text}}
                
    except Exception as e:
        return {"ok": False, "error": {"code": "EXCEPTION", "message": str(e)}}
