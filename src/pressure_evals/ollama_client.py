"""Thin wrapper around the Ollama Python client: reachability/model checks
and a single retrying chat call used by both generation and evaluation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import ollama
from tenacity import retry, stop_after_attempt, wait_exponential

DEFAULT_HOST = "http://localhost:11434"


class OllamaUnavailableError(RuntimeError):
    pass


@dataclass
class ChatResult:
    text: str
    latency_seconds: float
    thinking: str | None = None


# Model name prefixes known to support Ollama's `think` parameter. Passing
# think=True to a model that doesn't support it raises ResponseError, so this
# must be checked before setting the flag rather than always requesting it.
_THINKING_CAPABLE_PREFIXES = ("qwen3",)


def _supports_thinking(model: str) -> bool:
    return model.startswith(_THINKING_CAPABLE_PREFIXES)


def is_ollama_reachable(host: str = DEFAULT_HOST) -> bool:
    try:
        ollama.Client(host=host).list()
        return True
    except Exception:
        return False


def installed_models(host: str = DEFAULT_HOST) -> set[str]:
    resp = ollama.Client(host=host).list()
    return {m.model for m in resp.models}


def missing_models(required: list[str], host: str = DEFAULT_HOST) -> list[str]:
    installed = installed_models(host=host)
    return [m for m in required if m not in installed]


def install_instructions(missing: list[str]) -> str:
    lines = [f"ollama pull {m}" for m in missing]
    return "\n".join(lines)


def ensure_ready(required_models: list[str], host: str = DEFAULT_HOST) -> None:
    """Raise OllamaUnavailableError with an actionable message if anything
    needed for the experiment is missing, rather than failing deep inside a
    generation loop."""
    if not is_ollama_reachable(host=host):
        raise OllamaUnavailableError(
            f"Ollama is not reachable at {host}. Start it with the Ollama "
            "app or `ollama serve`, then retry."
        )
    missing = missing_models(required_models, host=host)
    if missing:
        raise OllamaUnavailableError(
            "Missing required Ollama models. Install them with:\n"
            + install_instructions(missing)
        )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def chat(
    model: str,
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float,
    top_p: float,
    max_tokens: int,
    format: str | dict | None = None,
    host: str = DEFAULT_HOST,
) -> ChatResult:
    """One chat call with explicit generation parameters. Retries transient
    connection/timeout errors up to 3 times with exponential backoff; does
    not retry on malformed output (that is evaluate.py's job, with a repair
    prompt rather than a blind retry).

    For reasoning-capable models (currently qwen3), think=True asks Ollama to
    separate chain-of-thought into `message.thinking`, so `message.content`
    holds only the final visible answer; the thinking text is preserved in
    the returned ChatResult rather than discarded. Passing think=True to a
    model that doesn't support it (gemma3, llama3.2) raises ResponseError, so
    the flag is only set when the model is known to support it.
    """
    client = ollama.Client(host=host)
    started = time.monotonic()
    chat_kwargs: dict = {}
    if _supports_thinking(model):
        chat_kwargs["think"] = True
    response = client.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": max_tokens,
        },
        format=format,
        **chat_kwargs,
    )
    latency = time.monotonic() - started
    return ChatResult(
        text=response.message.content or "",
        latency_seconds=latency,
        thinking=getattr(response.message, "thinking", None),
    )


def health_check_prompt(model: str, host: str = DEFAULT_HOST) -> ChatResult:
    # max_tokens is generous (not 50) because reasoning models such as qwen3
    # spend a variable, sometimes large, number of hidden tokens on
    # chain-of-thought before any visible content appears.
    return chat(
        model=model,
        system_prompt="You are a helpful assistant.",
        user_prompt="Say hello in one sentence.",
        temperature=0.0,
        top_p=1.0,
        max_tokens=2048,
        host=host,
    )
