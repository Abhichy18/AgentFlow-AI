import time
from typing import Any

from langchain_openai import ChatOpenAI

from core.config import settings


class ModelFailoverError(RuntimeError):
    def __init__(self, message: str, attempt_log: list[dict[str, Any]]):
        super().__init__(message)
        self.attempt_log = attempt_log


def _model_chain() -> list[str]:
    fallbacks = [
        m.strip()
        for m in settings.openrouter_fallback_models.split(",")
        if m.strip()
    ]
    chain = [settings.openrouter_model, *fallbacks]

    # Preserve order while removing duplicates.
    unique: list[str] = []
    for model in chain:
        if model not in unique:
            unique.append(model)
    return unique


def get_llm(model: str | None = None) -> ChatOpenAI:
    if not settings.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY is missing. Add it to .env.")

    return ChatOpenAI(
        model=model or settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        temperature=0.2,
    )


def invoke_with_failover(prompt: str) -> tuple[str, str, list[dict[str, Any]]]:
    last_exc: Exception | None = None
    retries = max(settings.openrouter_retries_per_model, 1)
    base_backoff = max(settings.openrouter_retry_backoff_seconds, 0.0)
    attempt_log: list[dict[str, Any]] = []

    for model in _model_chain():
        for attempt in range(1, retries + 1):
            start = time.perf_counter()
            try:
                llm = get_llm(model=model)
                response = llm.invoke(prompt)
                content = response.content if isinstance(response.content, str) else ""
                if content.strip():
                    latency_ms = int((time.perf_counter() - start) * 1000)
                    attempt_log.append(
                        {
                            "model": model,
                            "attempt": attempt,
                            "status": "success",
                            "latency_ms": latency_ms,
                            "error": "",
                        }
                    )
                    return content, model, attempt_log
                raise ValueError(f"Empty response from model: {model}")
            except Exception as exc:
                last_exc = exc
                latency_ms = int((time.perf_counter() - start) * 1000)
                attempt_log.append(
                    {
                        "model": model,
                        "attempt": attempt,
                        "status": "failed",
                        "latency_ms": latency_ms,
                        "error": str(exc),
                    }
                )
                if attempt < retries and base_backoff > 0:
                    # Exponential backoff per model before giving up this model.
                    sleep_seconds = base_backoff * (2 ** (attempt - 1))
                    time.sleep(sleep_seconds)

    if last_exc is not None:
        raise ModelFailoverError(
            f"All model invocations failed: {last_exc}",
            attempt_log,
        ) from last_exc
    raise ModelFailoverError("All model invocations failed.", attempt_log)
