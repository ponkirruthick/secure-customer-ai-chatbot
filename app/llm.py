import httpx
from app.config import settings
def chat(messages: list[dict], tools: list[dict] | None = None) -> dict:
    payload = {"model":settings.ollama_chat_model,"messages":messages,"stream":False}
    if tools: payload["tools"] = tools
    try:
        r = httpx.post(f"{settings.ollama_url}/api/chat", json=payload, timeout=settings.llm_timeout_seconds)
        r.raise_for_status()
        return r.json().get("message", {})
    except Exception as exc:
        raise RuntimeError("LLM unavailable or timed out; check Ollama and model configuration") from exc
