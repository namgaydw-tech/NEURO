"""OpenAI Agent SDK clinical-reasoning agent.

Requires OPENAI_API_KEY to produce LLM output. When the key is absent the
function returns a deterministic, clearly-labelled fallback — the `mode`
field is always "llm" or "fallback_no_api_key" so callers can never
mistake heuristic text for model output.
"""

from __future__ import annotations

import os
from typing import Any, Optional

FALLBACK_DISCLAIMER = (
    "Simulated reasoning (no LLM configured). Decision-support only; "
    "not a clinical diagnosis."
)


def _fallback(reason: str, disease: str, confidence: Optional[float], context: dict) -> dict[str, Any]:
    conf = f"{confidence:.0%}" if confidence is not None else "unknown"
    signals = ", ".join(context.get("signals")[:6]) or "none provided"
    bullets = [
        f"Primary hypothesis: {disease or 'undetermined'} (reported confidence {conf}).",
        f"Input signals considered: {signals}.",
        "Consistency: cross-check against real UCI CV metrics is performed by the "
        "LangGraph accuracy node; consult its `judgment` field.",
        "Missing data: recommend clinician review of history, imaging and EEG "
        "before any conclusion is acted on.",
        "Next step: verify with a qualified neurologist; escalate if symptoms "
        "are progressive or acute.",
    ]
    return {
        "mode": "fallback_no_api_key",
        "reason": reason,
        "llm": None,
        "summary": " | ".join(bullets[:2]),
        "reasoning_steps": bullets,
        "disclaimer": FALLBACK_DISCLAIMER,
    }


def clinical_reasoning(
    disease: str,
    confidence: Optional[float] = None,
    context: Optional[dict] = None,
) -> dict[str, Any]:
    """Run the OpenAI Agent SDK reasoning agent (or its labelled fallback)."""
    context = context or {}
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key or api_key.lower() in {"change-me", "sk-placeholder"}:
        return _fallback("OPENAI_API_KEY not configured", disease, confidence, context)

    try:
        from agents import Agent, Runner  # openai-agents SDK
    except Exception as exc:  # pragma: no cover
        return _fallback(f"agents SDK unavailable: {exc.__class__.__name__}", disease, confidence, context)

    agent = Agent(
        name="clinical_reasoner",
        instructions=(
            "You are a neurology decision-support assistant. Given a candidate "
            "prediction and its context, produce: (1) a one-sentence summary, "
            "(2) numbered reasoning steps weighing supporting and conflicting "
            "evidence, (3) what additional data would increase confidence. "
            "Never present the output as a diagnosis. Never invent statistics. "
            "If the input is insufficient, say so plainly."
        ),
    )
    prompt = (
        f"Candidate prediction: {disease or 'undetermined'} "
        f"(reported confidence: {confidence if confidence is not None else 'unknown'}).\n"
        f"Context signals: {', '.join(context.get('signals', [])) or 'none'}\n"
        f"Medical history: {context.get('medical_history') or 'not provided'}"
    )
    try:
        result = Runner.run_sync(agent, prompt)
        text = (result.final_output or "").strip()
    except Exception as exc:
        return _fallback(f"LLM call failed: {exc.__class__.__name__}", disease, confidence, context)

    return {
        "mode": "llm",
        "reason": "ok",
        "llm": "openai-agents",
        "summary": text.split("\n", 1)[0][:400],
        "raw": text,
        "disclaimer": (
            "LLM-generated decision support. Not a clinical diagnosis; "
            "requires clinician review."
        ),
    }
