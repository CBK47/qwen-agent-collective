"""Shared DashScope/Qwen client for the collective.

All Python agents should call Qwen through this module. It centralizes
environment loading, model selection, retries, timeouts, diagnostics, and logging
while keeping the original convenience functions (`chat`, `embed`) intact.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv()

DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
DEFAULT_CHAT_MODEL = "qwen-plus"
DEFAULT_CODER_MODEL = "qwen3-coder-plus"
DEFAULT_VISION_MODEL = "qwen-vl-max"
DEFAULT_AUDIO_MODEL = "qwen3-omni-flash"
DEFAULT_EMBED_MODEL = "text-embedding-v3"

LOGGER = logging.getLogger("qwen_collective.dashscope")


class DashScopeError(RuntimeError):
    """Raised when a DashScope request cannot be completed."""


@dataclass(frozen=True)
class DashScopeConfig:
    """Runtime configuration for Qwen calls."""

    api_key: str | None
    base_url: str = DEFAULT_BASE_URL
    chat_model: str = DEFAULT_CHAT_MODEL
    coder_model: str = DEFAULT_CODER_MODEL
    vision_model: str = DEFAULT_VISION_MODEL
    audio_model: str = DEFAULT_AUDIO_MODEL
    embed_model: str = DEFAULT_EMBED_MODEL
    timeout_seconds: float = 30.0
    max_retries: int = 2
    backoff_base_seconds: float = 0.75
    temperature: float | None = None
    max_tokens: int | None = None

    @classmethod
    def from_env(cls) -> "DashScopeConfig":
        return cls(
            api_key=os.environ.get("DASHSCOPE_API_KEY"),
            base_url=os.environ.get("DASHSCOPE_BASE_URL", DEFAULT_BASE_URL),
            chat_model=os.environ.get("QWEN_CHAT_MODEL", DEFAULT_CHAT_MODEL),
            coder_model=os.environ.get("QWEN_CODER_MODEL", DEFAULT_CODER_MODEL),
            vision_model=os.environ.get("QWEN_VL_MODEL", DEFAULT_VISION_MODEL),
            audio_model=os.environ.get("QWEN_AUDIO_MODEL", DEFAULT_AUDIO_MODEL),
            embed_model=os.environ.get("QWEN_EMBED_MODEL", DEFAULT_EMBED_MODEL),
            timeout_seconds=float(os.environ.get("QWEN_TIMEOUT_SECONDS", "30")),
            max_retries=int(os.environ.get("QWEN_MAX_RETRIES", "2")),
            backoff_base_seconds=float(os.environ.get("QWEN_BACKOFF_BASE_SECONDS", "0.75")),
            temperature=_optional_float(os.environ.get("QWEN_TEMPERATURE")),
            max_tokens=_optional_int(os.environ.get("QWEN_MAX_TOKENS")),
        )

    def require_api_key(self) -> str:
        if self.api_key:
            return self.api_key
        raise DashScopeError(
            "DASHSCOPE_API_KEY is not configured. Set it in the environment or "
            "copy .env.example to .env and fill the key before making Qwen calls."
        )

    def model_map(self) -> dict[str, str]:
        return {
            "chat": self.chat_model,
            "coder": self.coder_model,
            "vision": self.vision_model,
            "audio": self.audio_model,
            "embed": self.embed_model,
        }

    def redacted(self) -> dict[str, Any]:
        configured = bool(self.api_key)
        return {
            "api_key_configured": configured,
            "api_key_prefix": f"{self.api_key[:5]}..." if self.api_key else None,
            "base_url": self.base_url,
            "models": self.model_map(),
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
        }


class _LazyOpenAIClient:
    """Backwards-compatible proxy for older code importing `client` directly."""

    def __init__(self, config_factory: Callable[[], DashScopeConfig] = DashScopeConfig.from_env):
        self._config_factory = config_factory
        self._client: OpenAI | None = None
        self._fingerprint: tuple[str | None, str] | None = None

    def get(self) -> OpenAI:
        config = self._config_factory()
        fingerprint = (config.api_key, config.base_url)
        if self._client is None or self._fingerprint != fingerprint:
            self._client = OpenAI(
                api_key=config.require_api_key(),
                base_url=config.base_url,
                timeout=config.timeout_seconds,
                max_retries=0,
            )
            self._fingerprint = fingerprint
        return self._client

    def __getattr__(self, name: str) -> Any:
        return getattr(self.get(), name)


class DashScopeClient:
    """Small OpenAI-compatible client for DashScope/Qwen models."""

    def __init__(self, config: DashScopeConfig | None = None, openai_client: OpenAI | None = None):
        self.config = config or DashScopeConfig.from_env()
        self._client = openai_client

    @property
    def raw(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                api_key=self.config.require_api_key(),
                base_url=self.config.base_url,
                timeout=self.config.timeout_seconds,
                max_retries=0,
            )
        return self._client

    def chat(
        self,
        prompt: str | None = None,
        *,
        messages: Sequence[Mapping[str, Any]] | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
        metadata: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> str:
        """Run one chat completion and return reply text."""
        request_messages = _normalize_messages(prompt, messages)
        response = self._with_retries(
            operation="chat",
            model=model or self.config.chat_model,
            metadata=metadata,
            call=lambda: self.raw.chat.completions.create(
                **_strip_none(
                    {
                        "model": model or self.config.chat_model,
                        "messages": request_messages,
                        "temperature": temperature
                        if temperature is not None
                        else self.config.temperature,
                        "max_tokens": max_tokens if max_tokens is not None else self.config.max_tokens,
                        "timeout": timeout or self.config.timeout_seconds,
                        **extra,
                    }
                )
            ),
        )
        content = response.choices[0].message.content
        return content or ""

    def chat_stream(
        self,
        prompt: str | None = None,
        *,
        messages: Sequence[Mapping[str, Any]] | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
        metadata: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> Iterator[str]:
        """Stream a chat completion as text chunks."""
        request_messages = _normalize_messages(prompt, messages)
        stream = self._with_retries(
            operation="chat_stream",
            model=model or self.config.chat_model,
            metadata=metadata,
            call=lambda: self.raw.chat.completions.create(
                **_strip_none(
                    {
                        "model": model or self.config.chat_model,
                        "messages": request_messages,
                        "temperature": temperature
                        if temperature is not None
                        else self.config.temperature,
                        "max_tokens": max_tokens if max_tokens is not None else self.config.max_tokens,
                        "timeout": timeout or self.config.timeout_seconds,
                        "stream": True,
                        **extra,
                    }
                )
            ),
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def embed(
        self,
        text: str | Sequence[str],
        *,
        model: str | None = None,
        timeout: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> list[float] | list[list[float]]:
        """Embed one string or a batch of strings."""
        response = self._with_retries(
            operation="embed",
            model=model or self.config.embed_model,
            metadata=metadata,
            call=lambda: self.raw.embeddings.create(
                model=model or self.config.embed_model,
                input=text,
                timeout=timeout or self.config.timeout_seconds,
            ),
        )
        vectors = [item.embedding for item in response.data]
        return vectors[0] if isinstance(text, str) else vectors

    def list_models(self) -> list[str]:
        """Return model IDs visible to the configured key."""
        response = self._with_retries(
            operation="models.list",
            model=None,
            metadata={"purpose": "diagnostic"},
            call=lambda: self.raw.models.list(timeout=self.config.timeout_seconds),
        )
        return [model.id for model in response.data]

    def diagnose(self, *, network: bool = True) -> dict[str, Any]:
        """Validate config and, optionally, live credentials."""
        report: dict[str, Any] = {
            "ok": False,
            "config": self.config.redacted(),
            "checks": [],
        }
        self._add_check(report, "api_key_present", bool(self.config.api_key), "Set DASHSCOPE_API_KEY.")
        self._add_check(
            report,
            "base_url_present",
            bool(self.config.base_url),
            "Set DASHSCOPE_BASE_URL or use the default compatible-mode endpoint.",
        )
        self._add_check(
            report,
            "models_configured",
            all(self.config.model_map().values()),
            "Set the QWEN_*_MODEL environment variables.",
        )
        if network and self.config.api_key:
            self._network_diagnostics(report)
        report["ok"] = all(check["ok"] for check in report["checks"])
        return report

    def _network_diagnostics(self, report: dict[str, Any]) -> None:
        try:
            models = self.list_models()
            self._add_check(report, "models_list", True, f"{len(models)} models visible.")
        except Exception as exc:
            self._add_check(report, "models_list", False, _friendly_error(exc))
        try:
            reply = self.chat(
                "Reply with one word: ok",
                temperature=0,
                max_tokens=8,
                metadata={"purpose": "diagnostic"},
            )
            self._add_check(report, "chat_completion", bool(reply.strip()), repr(reply.strip()[:40]))
        except Exception as exc:
            self._add_check(report, "chat_completion", False, _friendly_error(exc))
        try:
            vector = self.embed("diagnostic", metadata={"purpose": "diagnostic"})
            self._add_check(report, "embedding", bool(vector), f"dim {len(vector)}")
        except Exception as exc:
            self._add_check(report, "embedding", False, _friendly_error(exc))

    @staticmethod
    def _add_check(report: dict[str, Any], name: str, ok: bool, detail: str) -> None:
        report["checks"].append({"name": name, "ok": ok, "detail": detail})

    def _with_retries(
        self,
        *,
        operation: str,
        model: str | None,
        metadata: Mapping[str, Any] | None,
        call: Callable[[], Any],
    ) -> Any:
        request_id = str(metadata.get("request_id")) if metadata and metadata.get("request_id") else str(uuid.uuid4())
        started = time.monotonic()
        attempts = self.config.max_retries + 1
        for attempt in range(1, attempts + 1):
            try:
                result = call()
                self._log(
                    "info",
                    "dashscope_request_ok",
                    operation=operation,
                    model=model,
                    request_id=request_id,
                    attempt=attempt,
                    elapsed_ms=round((time.monotonic() - started) * 1000, 2),
                    metadata=metadata,
                )
                return result
            except Exception as exc:
                if attempt >= attempts:
                    self._log(
                        "error",
                        "dashscope_request_failed",
                        operation=operation,
                        model=model,
                        request_id=request_id,
                        attempt=attempt,
                        elapsed_ms=round((time.monotonic() - started) * 1000, 2),
                        error=_friendly_error(exc),
                        metadata=metadata,
                    )
                    raise DashScopeError(_friendly_error(exc)) from exc
                delay = self.config.backoff_base_seconds * (2 ** (attempt - 1))
                delay += random.uniform(0, self.config.backoff_base_seconds / 3)
                self._log(
                    "warning",
                    "dashscope_request_retry",
                    operation=operation,
                    model=model,
                    request_id=request_id,
                    attempt=attempt,
                    retry_in_seconds=round(delay, 2),
                    error=_friendly_error(exc),
                    metadata=metadata,
                )
                time.sleep(delay)
        raise AssertionError("unreachable retry loop state")

    @staticmethod
    def _log(level: str, event: str, **payload: Any) -> None:
        if not LOGGER.handlers and not logging.getLogger().handlers:
            logging.basicConfig(level=os.environ.get("LOG_LEVEL", "WARNING"))
        getattr(LOGGER, level)(json.dumps({"event": event, **payload}, default=str, sort_keys=True))


def _normalize_messages(
    prompt: str | None,
    messages: Sequence[Mapping[str, Any]] | None,
) -> list[Mapping[str, Any]]:
    if messages:
        return list(messages)
    if prompt is None:
        raise ValueError("Either prompt or messages is required.")
    return [{"role": "user", "content": prompt}]


def _strip_none(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _optional_float(value: str | None) -> float | None:
    return float(value) if value not in (None, "") else None


def _optional_int(value: str | None) -> int | None:
    return int(value) if value not in (None, "") else None


def _friendly_error(exc: Exception) -> str:
    text = str(exc).splitlines()[0]
    if "401" in text or "Unauthorized" in text:
        return "DashScope rejected the API key. Check DASHSCOPE_API_KEY and the selected region/base URL."
    if "404" in text and "model" in text.lower():
        return "DashScope could not find the configured model. Check the relevant QWEN_*_MODEL value."
    if "timeout" in text.lower():
        return "DashScope request timed out. Increase QWEN_TIMEOUT_SECONDS or retry later."
    return text[:300] or exc.__class__.__name__


DEFAULT_CONFIG = DashScopeConfig.from_env()
CHAT_MODEL = DEFAULT_CONFIG.chat_model
CODER_MODEL = DEFAULT_CONFIG.coder_model
VL_MODEL = DEFAULT_CONFIG.vision_model
AUDIO_MODEL = DEFAULT_CONFIG.audio_model
EMBED_MODEL = DEFAULT_CONFIG.embed_model
client = _LazyOpenAIClient()


def chat(prompt: str, model: str | None = None, **kwargs: Any) -> str:
    """Backwards-compatible one-shot chat helper."""
    return DashScopeClient().chat(prompt, model=model, **kwargs)


def chat_stream(prompt: str, model: str | None = None, **kwargs: Any) -> Iterator[str]:
    """Backwards-compatible streaming chat helper."""
    return DashScopeClient().chat_stream(prompt, model=model, **kwargs)


def embed(text: str | Sequence[str], model: str | None = None, **kwargs: Any) -> list[float] | list[list[float]]:
    """Backwards-compatible embedding helper."""
    return DashScopeClient().embed(text, model=model, **kwargs)


def diagnose(*, network: bool = True) -> dict[str, Any]:
    """Run configuration and credential diagnostics."""
    return DashScopeClient().diagnose(network=network)


def _print_human_report(report: Mapping[str, Any]) -> None:
    config = report["config"]
    print("DashScope/Qwen diagnostics")
    print(f"  base_url: {config['base_url']}")
    print(f"  api_key: {'configured' if config['api_key_configured'] else 'missing'}")
    for kind, model in config["models"].items():
        print(f"  model.{kind}: {model}")
    print("")
    for check in report["checks"]:
        status = "PASS" if check["ok"] else "FAIL"
        print(f"{status:4} {check['name']:<18} {check['detail']}")
    print("")
    print("OK" if report["ok"] else "FAILED")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DashScope/Qwen shared client utilities.")
    sub = parser.add_subparsers(dest="command")

    doctor = sub.add_parser("doctor", help="validate config and credentials")
    doctor.add_argument("--no-network", action="store_true", help="only check local environment values")
    doctor.add_argument("--json", action="store_true", help="print machine-readable JSON")

    chat_cmd = sub.add_parser("chat", help="send a one-shot chat prompt")
    chat_cmd.add_argument("prompt")
    chat_cmd.add_argument("--model")

    embed_cmd = sub.add_parser("embed", help="embed text and print vector dimension")
    embed_cmd.add_argument("text")
    embed_cmd.add_argument("--model")

    sub.add_parser("models", help="list model IDs visible to this key")

    args = parser.parse_args(list(argv) if argv is not None else None)
    command = args.command or "doctor"
    qwen = DashScopeClient()

    try:
        if command == "doctor":
            report = qwen.diagnose(network=not args.no_network)
            if args.json:
                print(json.dumps(report, indent=2, sort_keys=True))
            else:
                _print_human_report(report)
            return 0 if report["ok"] else 1
        if command == "chat":
            print(qwen.chat(args.prompt, model=args.model))
            return 0
        if command == "embed":
            vector = qwen.embed(args.text, model=args.model)
            print(f"dim {len(vector)}")
            return 0
        if command == "models":
            for model in qwen.list_models():
                print(model)
            return 0
    except DashScopeError as exc:
        print(f"DashScope error: {exc}", file=sys.stderr)
        return 2
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
