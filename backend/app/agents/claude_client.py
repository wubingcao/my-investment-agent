"""Thin wrapper around the Anthropic SDK with prompt caching + JSON extraction."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from anthropic import AsyncAnthropic
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from app.config import get_settings

log = logging.getLogger(__name__)


class ClaudeClient:
    def __init__(self):
        cfg = get_settings()
        if not cfg.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY missing. Populate backend/.env")
        self._client = AsyncAnthropic(api_key=cfg.anthropic_api_key)
        self.debate_model = cfg.claude_debate_model
        self.parse_model = cfg.claude_parse_model

    async def complete(
        self,
        system: str,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float | None = 0.6,
        cache_system: bool = True,
    ) -> str:
        model = model or self.debate_model
        sys_blocks = (
            [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
            if cache_system
            else [{"type": "text", "text": system}]
        )

        # Newer Opus/Sonnet models (Opus 4.5+) deprecated the `temperature` param.
        # Detect by model name and drop the kwarg for those.
        if _model_rejects_temperature(model):
            temperature = None

        create_kwargs: dict[str, Any] = dict(
            model=model,
            system=sys_blocks,
            messages=messages,
            max_tokens=max_tokens,
        )
        if temperature is not None:
            create_kwargs["temperature"] = temperature

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            reraise=True,
        ):
            with attempt:
                resp = await self._client.messages.create(**create_kwargs)
                text_parts = [b.text for b in resp.content if getattr(b, "type", "") == "text"]
                return "\n".join(text_parts)

    async def json_complete(
        self,
        system: str,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float | None = 0.3,
    ) -> dict[str, Any]:
        """Request a JSON response and parse it robustly."""
        raw = await self.complete(
            system=system + "\n\nRespond ONLY with a valid JSON object. No prose, no markdown fences.",
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return self.extract_json(raw)

    @staticmethod
    def extract_json(text: str) -> dict[str, Any]:
        if not text:
            return {}
        # strip markdown fences
        text = re.sub(r"^```(?:json)?\s*", "", text.strip())
        text = re.sub(r"\s*```$", "", text)
        try:
            return json.loads(text)
        except Exception:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass
        log.warning("Failed to parse JSON from model output: %s", text[:400])
        return {}


def _model_rejects_temperature(model: str) -> bool:
    """Opus 4.5+ dropped the `temperature` param."""
    if not model:
        return False
    m = model.lower()
    if m.startswith("claude-opus-4-"):
        try:
            minor = int(m.split("claude-opus-4-")[1].split("-")[0])
            return minor >= 5
        except (ValueError, IndexError):
            return True
    return False


_singleton: ClaudeClient | None = None


def get_claude() -> ClaudeClient:
    global _singleton
    if _singleton is None:
        _singleton = ClaudeClient()
    return _singleton
