"""NEURO_PREDICT_SYS agent pipeline.

Three composable agents:
- LangGraph accuracy workflow: cross-checks a prediction against the real
  UCI cross-validation metrics (deterministic, no LLM required).
- OpenAI Agent SDK clinical reasoning: LLM-generated reasoning narrative,
  with a clearly-labelled deterministic fallback when no API key is set.
- CrewAI structuring: multi-agent report structuring, same fallback rule.

NEVER present fallback output as LLM output — every response carries an
explicit `mode` field ("llm" or "fallback_no_api_key").
"""

from .langgraph_accuracy import accuracy_check
from .openai_agent import clinical_reasoning
from .crewai_report import structured_report

__all__ = ["accuracy_check", "clinical_reasoning", "structured_report"]
