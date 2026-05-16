"""LLM-as-judge — Kimi scores a draft against the rubric."""
from pathlib import Path

from eval.schemas import RubricScore
from intel_engine.llm.client import LLMClient, LLMProvider

_PROMPT_PATH = Path(__file__).parent / "judge_prompt.md"


def _clamp(value: object) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return 1
    return max(1, min(5, n))


async def judge_draft(
    *,
    ticket_id: str,
    customer_message: str,
    draft_reply: str,
    cited_excerpts: list[str],
    brand_voice_contract: str,
) -> RubricScore:
    """Score a single draft using Kimi."""
    system = _PROMPT_PATH.read_text()
    excerpts_block = "\n\n".join(cited_excerpts) if cited_excerpts else "(none)"
    user = (
        f"=== BRAND VOICE CONTRACT ===\n{brand_voice_contract}\n\n"
        f"=== CUSTOMER MESSAGE ===\n{customer_message}\n\n"
        f"=== DRAFT REPLY ===\n{draft_reply}\n\n"
        f"=== CITED KB EXCERPTS ===\n{excerpts_block}"
    )

    client = LLMClient(provider=LLMProvider.kimi)
    raw = await client.complete_json(system=system, user=user)

    return RubricScore(
        ticket_id=ticket_id,
        grounded=_clamp(raw.get("grounded")),
        brand_voice=_clamp(raw.get("brand_voice")),
        completeness=_clamp(raw.get("completeness")),
        no_hallucination=_clamp(raw.get("no_hallucination")),
        tone_fit=_clamp(raw.get("tone_fit")),
        notes=str(raw.get("notes") or "")[:300],
    )
