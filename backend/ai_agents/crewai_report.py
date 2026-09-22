"""CrewAI report-structuring agent.

Structures a prediction + reasoning into a consistent clinical-report
format. CrewAI requires an LLM key; without one, a deterministic template
produces the same section structure, labelled `mode: fallback_no_api_key`.
"""

from __future__ import annotations

import os
from typing import Any, Optional

SECTIONS = [
    "summary",
    "inputs_reviewed",
    "model_confidence",
    "accuracy_reference",
    "recommendations",
    "limitations",
]


def _fallback(report: dict) -> dict[str, Any]:
    reasoning = report.get("reasoning_steps") or []
    accuracy = report.get("accuracy") or {}
    conf = report.get("confidence")
    return {
        "mode": "fallback_no_api_key",
        "reason": "OPENAI_API_KEY not configured",
        "llm": None,
        "structure": "crewai_section_schema",
        "sections": {
            "summary": report.get("summary")
            or (reasoning[0] if reasoning else f"Candidate prediction: {report.get('disease') or 'undetermined'}."),
            "inputs_reviewed": report.get("signals") or [],
            "model_confidence": {
                "claimed": conf,
                "judgment": accuracy.get("judgment", "not cross-checked"),
            },
            "accuracy_reference": {
                "dataset": accuracy.get("dataset_key"),
                "best_model": accuracy.get("best_model"),
                "cv5_accuracy": accuracy.get("expected_accuracy_cv5"),
                "source": accuracy.get("source"),
            },
            "recommendations": report.get("recommendations")
            or [
                "Clinician review required before acting on this output.",
                "Cross-check with imaging/EEG where available.",
            ],
            "limitations": [
                accuracy.get("judgment") or "No accuracy cross-check available.",
                "Trained on public research datasets; not clinically validated.",
                "Decision-support only; not a diagnosis.",
            ],
        },
        "disclaimer": "Structured by deterministic template (no LLM configured).",
    }


def structured_report(report: dict) -> dict[str, Any]:
    """Structure a prediction + accuracy report into a stable schema."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key or api_key.lower() in {"change-me", "sk-placeholder"}:
        return _fallback(report)

    try:
        from crewai import Agent, Task, Crew
    except Exception as exc:  # pragma: no cover
        out = _fallback(report)
        out["reason"] = f"crewai unavailable: {exc.__class__.__name__}"
        return out

    analyst = Agent(
        role="Clinical Data Analyst",
        goal="Extract the decision-relevant facts from a prediction payload",
        backstory="You summarise ML decision-support outputs precisely and conservatively.",
        allow_delegation=False,
        verbose=False,
    )
    editor = Agent(
        role="Report Structurer",
        goal="Lay facts into the fixed sections of a clinical decision-support report",
        backstory="You produce consistent, auditable report structures.",
        allow_delegation=False,
        verbose=False,
    )
    facts = Task(
        description=f"Extract facts from: {report}",
        expected_output="Bullets: prediction, confidence, inputs, accuracy reference, caveats.",
        agent=analyst,
    )
    structured = Task(
        description=(
            "Produce sections: summary, inputs_reviewed, model_confidence, "
            "accuracy_reference, recommendations, limitations. "
            "Never claim clinical validation."
        ),
        expected_output="A report with exactly those six section headings.",
        agent=editor,
        context=[facts],
    )
    try:
        crew = Crew(agents=[analyst, editor], tasks=[facts, structured], verbose=False)
        result = crew.kickoff()
        text = str(result).strip()
    except Exception as exc:
        out = _fallback(report)
        out["reason"] = f"crew run failed: {exc.__class__.__name__}"
        return out

    return {
        "mode": "llm",
        "reason": "ok",
        "llm": "crewai",
        "structure": "crewai_section_schema",
        "raw": text,
        "sections": {"raw_text": text[:8000]},
        "disclaimer": "LLM-structured decision support; not a clinical diagnosis.",
    }
