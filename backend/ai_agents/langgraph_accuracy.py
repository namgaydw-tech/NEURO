"""LangGraph accuracy workflow.

Cross-checks an AI prediction against the REAL cross-validation metrics
recorded by backend/ml/train_uci.py (uci_model_metadata.json). Pure
deterministic graph — no LLM, no API key, works offline.

Graph:
    load_metrics -> match_model -> judge_confidence -> compile_report
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

METADATA_PATH = Path(__file__).resolve().parents[1] / "ml" / "models" / "uci_model_metadata.json"

# Map application disease labels -> UCI dataset keys (empty = no real model yet)
DISEASE_TO_DATASET = {
    "epilepsy": "beed_epilepsy",
    "seizure": "beed_epilepsy",
    "parkinson's": "parkinsons",
    "parkinsons": "parkinsons",
    "parkinson disease": "parkinsons",
    "freezing of gait": "daphnet_gait",
    "alzheimer's": "",      # no real-data model yet — must stay honest
    "alzheimers": "",
    "als": "",
    "huntington's": "",
}


class AccuracyState(TypedDict, total=False):
    disease: str
    claimed_confidence: Optional[float]
    metrics: dict
    dataset_key: Optional[str]
    model_entry: Optional[dict]
    judgment: str
    expected_accuracy: Optional[float]
    report: dict


def _load_metrics(state: AccuracyState) -> AccuracyState:
    try:
        payload = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
        state["metrics"] = payload.get("datasets", {})
    except Exception:
        state["metrics"] = {}
    return state


def _match_model(state: AccuracyState) -> AccuracyState:
    key = DISEASE_TO_DATASET.get((state.get("disease") or "").strip().lower(), None)
    if key == "":
        key = None  # explicitly known to have no real model
    entry = state["metrics"].get(key, {}) if key else {}
    state["dataset_key"] = key if entry else None
    state["model_entry"] = entry or None
    return state


def _judge_confidence(state: AccuracyState) -> AccuracyState:
    entry = state.get("model_entry") or {}
    best = entry.get("best_model")
    model_metrics = (entry.get("models") or {}).get(best, {}) if best else {}
    expected = model_metrics.get("cv5_accuracy_mean")
    state["expected_accuracy"] = expected
    claimed = state.get("claimed_confidence")

    if expected is None:
        state["judgment"] = (
            "no_real_model: this condition has no model trained on real UCI data; "
            "any confidence shown comes from the synthetic demo model or a symptom "
            "fallback and must be labelled simulated."
        )
    elif claimed is None:
        state["judgment"] = "no_claimed_confidence: only the reference metric is reported."
    elif claimed > expected + 0.05:
        state["judgment"] = (
            f"over_confident: claimed {claimed:.0%} exceeds the real 5-fold CV "
            f"accuracy {expected:.0%} for the closest model by more than 5 points."
        )
    elif claimed < expected - 0.15:
        state["judgment"] = f"under_confident: claimed {claimed:.0%} vs CV {expected:.0%}."
    else:
        state["judgment"] = f"consistent: claimed {claimed:.0%} is within the expected band of CV {expected:.0%}."
    return state


def _compile_report(state: AccuracyState) -> AccuracyState:
    entry = state.get("model_entry") or {}
    state["report"] = {
        "mode": "langgraph_deterministic",
        "workflow": ["load_metrics", "match_model", "judge_confidence", "compile_report"],
        "disease": state.get("disease"),
        "claimed_confidence": state.get("claimed_confidence"),
        "dataset_key": state.get("dataset_key"),
        "dataset_url": entry.get("url"),
        "best_model": entry.get("best_model"),
        "expected_accuracy_cv5": state.get("expected_accuracy"),
        "judgment": state.get("judgment"),
        "source": "backend/ml/models/uci_model_metadata.json (real UCI 5-fold CV)",
        "disclaimer": (
            "Decision-support estimate only. UCI datasets are public research "
            "datasets, not clinical validation. Not for medical decision-making."
        ),
    }
    return state


def _build_graph():
    g = StateGraph(AccuracyState)
    g.add_node("load_metrics", _load_metrics)
    g.add_node("match_model", _match_model)
    g.add_node("judge_confidence", _judge_confidence)
    g.add_node("compile_report", _compile_report)
    g.add_edge(START, "load_metrics")
    g.add_edge("load_metrics", "match_model")
    g.add_edge("match_model", "judge_confidence")
    g.add_edge("judge_confidence", "compile_report")
    g.add_edge("compile_report", END)
    return g.compile()


_accuracy_app = None


def accuracy_check(disease: str, claimed_confidence: Optional[float] = None) -> dict[str, Any]:
    """Run the LangGraph accuracy workflow and return its report."""
    global _accuracy_app
    if _accuracy_app is None:
        _accuracy_app = _build_graph()
    final: AccuracyState = _accuracy_app.invoke(
        {"disease": disease, "claimed_confidence": claimed_confidence}
    )
    return final["report"]
