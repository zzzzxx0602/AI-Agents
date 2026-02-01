from __future__ import annotations
import os
import requests

def generate_text_openai(system: str, user: str, model: str = "gpt-4o-mini") -> str:
    """OpenAI chat completion via openai-python v1.x.
    Requires OPENAI_API_KEY in environment.
    """
    from openai import OpenAI
    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content

def generate_text_ollama(system: str, user: str, base_url: str, model: str) -> str:
    """Ollama local inference (no paid API). Requires ollama running locally."""
    url = base_url.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": 0.3},
    }
    r = requests.post(url, json=payload, timeout=180)
    r.raise_for_status()
    data = r.json()
    return data["message"]["content"]

def generate_ai_memo(system: str, user: str, provider: str, model: str, ollama_base_url: str, ollama_model: str) -> tuple[str, str]:
    """Returns (memo_text, provider_used)."""
    provider = (provider or "openai").lower().strip()
    if provider == "openai":
        # If key missing, fall back to ollama (if available) or return a clear error memo.
        if not os.getenv("OPENAI_API_KEY"):
            try:
                memo = generate_text_ollama(system, user, base_url=ollama_base_url, model=ollama_model)
                return memo, f"ollama:{ollama_model}"
            except Exception:
                return (
                    "# AI Memo Generation Failed\n\n"
                    "No OPENAI_API_KEY was found, and Ollama was not reachable.\n\n"
                    "To generate the required AI memo, either:\n"
                    "- Set OPENAI_API_KEY, or\n"
                    "- Install and run Ollama locally, then set provider=ollama in src/config.py.\n",
                    "none",
                )
        memo = generate_text_openai(system, user, model=model)
        return memo, f"openai:{model}"

    if provider == "ollama":
        memo = generate_text_ollama(system, user, base_url=ollama_base_url, model=ollama_model)
        return memo, f"ollama:{ollama_model}"

    return (
        "# AI Memo Generation Failed\n\nUnsupported provider. Use 'openai' or 'ollama'.\n",
        "none",
    )
