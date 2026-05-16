"""OpenAI-compatible chat client for Minimax + Kimi."""
import json
from enum import StrEnum
from typing import Any

import httpx

from intel_engine.settings import llm_config


class LLMProvider(StrEnum):
    minimax = "minimax"
    kimi = "kimi"


class LLMClient:
    def __init__(self, provider: LLMProvider, timeout: float = 60.0):
        cfg = llm_config(provider.value)
        self.base_url = cfg["base_url"].rstrip("/")
        self.api_key = cfg["api_key"]
        self.model = cfg["model"]
        self.timeout = timeout

    async def _chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    **kwargs,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def complete_text(self, system: str, user: str) -> str:
        return await self._chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )

    async def complete_json(
        self,
        system: str,
        user: str,
        max_retries: int = 1,
    ) -> dict[str, Any]:
        """Request a JSON response. Falls back to retry on parse failure."""
        prompt_with_json = (
            f"{system}\n\n"
            "You MUST respond with valid JSON only. No markdown fences, no prose."
        )
        last_err: Exception | None = None
        for _attempt in range(max_retries + 1):
            text = await self._chat(
                messages=[
                    {"role": "system", "content": prompt_with_json},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
            )
            try:
                # Tolerate accidental code fences
                stripped = text.strip()
                if stripped.startswith("```"):
                    parts = stripped.split("```", 2)
                    if len(parts) >= 3:
                        stripped = parts[1]
                        if stripped.startswith("json"):
                            stripped = stripped[4:]
                return json.loads(stripped)
            except json.JSONDecodeError as e:
                last_err = e
                continue
        raise ValueError(f"LLM returned non-JSON after retries: {last_err}")
