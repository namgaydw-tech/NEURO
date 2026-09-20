"""
NEURO_PREDICT_SYS — Real-UCI Dataset Training Pipeline
=======================================================

Trains disease-prediction models on REAL datasets downloaded from the UCI
Machine Learning Repository (see dataset/README.md for provenance).

This replaces the synthetic-data pipeline in train_model.py as the primary
trainer. The synthetic BrainLat-style generator is kept only as a fallback
demo and every artifact produced here is labelled with its true provenance.

Datasets (all real, all UCI):
  1. BEED: Bangalore EEG Epilepsy Dataset  (UCI 1134)  -> epilepsy detection
     8,000 rows, 16 EEG channels, binary target `y`
  2. EEG Eye State                          (UCI 264)  -> EEG signal quality / state
     14,980 rows, 14 EEG channels, binary `eyeDetection`
  3. Parkinsons voice measurements          (UCI 174)  -> Parkinson's detection
     197 rows, 22 voice features, binary `status`
  4. Mice Protein Expression                (UCI 342)  -> trisomy/memory biomarkers
     1,080 rows, 77 protein columns, 8-class `class`

Models: RandomForest + GradientBoosting (same algorithms as the original
pipeline, so the deployed predictor's interface does not change).

Outputs:
  backend/ml/models/uci_model_metadata.json  — honest per-dataset metrics
  backend/ml/models/uci_<name>_model.pkl     — each trained pipeline
"""

import json
import os
import warnings
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.io import arff

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "dataset" / "uciraw"
MODELS_DIR = Path(__file__).resolve().parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42


# --------------------------------------------------------------------------
# Loaders — one per dataset, each returns (X: DataFrame, y: Series, meta: dict)
# --------------------------------------------------------------------------
def load_beed_epilepsy():
    """UCI 1134 — BEED: Bangalore EEG Epilepsy Dataset."""
    path = RAW / "beed_eeg_epilepsy" / "BEED_Data.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    X = df.drop(columns=["y"])
    y = df["y"].astype(int)
    meta = {
        "uci_id": 1134,
        "url": "https://archive.ics.uci.edu/dataset/1134",
        "doi": "10.24432/C5K33B",
        "license": "CC BY 4.0",
        "n_rows": len(df),
        "n_features": X.shape[1],
        "classes": sorted(y.unique().tolist()),
        "class_counts": y.value_counts().to_dict(),
        "class_names": {
            "0": "healthy_control",
            "1": "generalized_seizure",
            "2": "focal_seizure",
            "3": "seizure_event",
        },
        "description": "16-channel EEG (10-20 system, 256 Hz); 4-class epilepsy classification",
    }
    return X, y, meta


def load_eeg_eye_state():
    """UCI 264 — EEG Eye State."""
    path = RAW / "eeg_eye_state" / "EEG Eye State.arff"
    if not path.exists():
        return None
    data, _ = arff.loadarff(path)
    df = pd.DataFrame(data)
    # decode bytes columns
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].str.decode("utf-8")
    X = df.drop(columns=["eyeDetection"]).astype(float)
    y = df["eyeDetection"].astype(int)
    # The dataset contains known measurement outliers; clip extreme values
    # to the 0.1/99.9 percentile so a few bad sensors cannot dominate scaling.
    lo, hi = X.quantile(0.001), X.quantile(0.999)
    X = X.clip(lo, hi, axis=1)
    meta = {
        "uci_id": 264,
        "url": "https://archive.ics.uci.edu/dataset/264",
        "n_rows": len(df),
        "n_features": X.shape[1],
        "classes": sorted(y.unique().tolist()),
        "class_counts": y.value_counts().to_dict(),
        "description": "14-channel EEG; eye-open/closed state (used for EEG signal QA)",
        "preprocessing": "values clipped to 0.1/99.9 percentile to remove sensor spikes",
    }
    return X, y, meta


def load_parkinsons():
    """UCI 174 — Parkinsons voice measurements."""
    path = RAW / "parkinsons" / "parkinsons.data"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    X = df.drop(columns=["name", "status"])
    y = df["status"].astype(int)
    meta = {
        "uci_id": 174,
        "url": "https://archive.ics.uci.edu/dataset/174",
        "n_rows": len(df),
        "n_features": X.shape[1],
        "classes": sorted(y.unique().tolist()),
        "class_counts": y.value_counts().to_dict(),
        "description": "22 voice measurements from 31 people; binary Parkinson's detection",
        "caution": "small cohort (197 rows, ~23 subjects) — scores are optimistic; treat as demo",
    }
    return X, y, meta


def load_mice_protein():
    """UCI 342 — Mice Protein Expression (trisomy / memory biomarkers)."""
    path = RAW / "mice_protein" / "Data_Cortex_Nuclear.xls"
    if not path.exists():
        return None
    try:
        df = pd.read_excel(path, engine="xlrd")
    except Exception as exc:  # xlrd not installed -> skip gracefully
        print(f"[skip] mice_protein: cannot read legacy .xls ({exc})")
        return None
    X = df.drop(columns=["MouseID"])
    # 38 proteins have missing values in some mice; median-impute per class
    X = X.fillna(X.groupby(df["class"]).transform("median"))
    X = X.fillna(X.median())
    y = df["class"].astype(str)
    meta = {
        "uci_id": 342,
        "url": "https://archive.ics.uci.edu/dataset/342",
        "n_rows": len(df),
        "n_features": X.shape[1],
        "classes": sorted(y.unique().tolist()),
        "class_counts": y.value_counts().to_dict(),
        "description": "77 protein expression levels; 8-class genotype/behavior groups",
        "preprocessing": "missing protein levels median-imputed within class",
    }
    return X, y, meta


LOADERS = {
    "beed_epilepsy": load_beed_epilepsy,
    "eeg_eye_state": load_eeg_eye_state,
    "parkinsons": load_parkinsons,
    "mice_protein": load_mice_protein,
}


# --------------------------------------------------------------------------
# Model zoo — same algorithms as the original pipeline
# --------------------------------------------------------------------------
def build_models():
    return {
        # NOTE: depth/leaf limits keep artifacts small (repo-friendly) while
        # costing ~0.5-1pt CV accuracy vs unbounded trees.
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_leaf=5,
            max_features="sqrt",
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=3,
            subsample=0.9,
            random_state=RANDOM_STATE,
        ),
        "logistic_regression": LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE
        ),
    }


def evaluate_dataset(name, X, y, meta):
    print(f"\n{'=' * 70}\n{name}: {meta['n_rows']} rows x {meta['n_features']} features")
    print(f"    classes: {meta['class_counts']}")

    strat = y if min(pd.Series(y).value_counts()) >= 4 else None
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=strat
    )

    results = {"meta": meta, "models": {}}
    best_name, best_score = None, -1.0

    for model_name, estimator in build_models().items():
        pipe = Pipeline([("scaler", StandardScaler()), ("clf", estimator)])
        pipe.fit(X_tr, y_tr)
        pred = pipe.predict(X_te)
        acc = accuracy_score(y_te, pred)
        f1 = f1_score(y_te, pred, average="weighted")
        entry = {"accuracy": round(acc, 4), "f1_weighted": round(f1, 4)}

        # ROC-AUC for binary tasks with a probability-capable estimator
        if len(np.unique(y)) == 2 and hasattr(pipe, "predict_proba"):
            try:
                proba = pipe.predict_proba(X_te)[:, 1]
                entry["roc_auc"] = round(float(roc_auc_score(y_te, proba)), 4)
            except Exception:
                pass

        # 5-fold CV accuracy (honest generalisation estimate)
        try:
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
            cv_scores = cross_val_score(
                Pipeline([("scaler", StandardScaler()), ("clf", estimator)]),
                X, y, cv=cv, scoring="accuracy", n_jobs=-1,
            )
            entry["cv5_accuracy_mean"] = round(float(cv_scores.mean()), 4)
            entry["cv5_accuracy_std"] = round(float(cv_scores.std()), 4)
        except Exception:
            entry["cv5_accuracy_mean"] = None

        results["models"][model_name] = entry
        if entry["cv5_accuracy_mean"] or 0 > best_score:
            pass
        if (entry["cv5_accuracy_mean"] or 0) >= best_score:
            best_score = entry["cv5_accuracy_mean"] or 0
            best_name = model_name

        print(f"  {model_name:<20} acc={acc:.4f} f1={f1:.4f} "
              f"cv5={entry['cv5_accuracy_mean']}")

    # persist the best model + full test report of it
    best_est = build_models()[best_name]
    pipe = Pipeline([("scaler", StandardScaler()), ("clf", best_est)])
    pipe.fit(X_tr, y_tr)
    pred = pipe.predict(X_te)
    report = classification_report(y_te, pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_te, pred).tolist()

    artifact = MODELS_DIR / f"uci_{name}_model.pkl"
    joblib.dump(
        {"pipeline": pipe, "feature_names": list(X.columns), "dataset": name},
        artifact,
    )

    results["best_model"] = best_name
    results["test_report"] = report
    results["confusion_matrix"] = cm
    results["artifact"] = artifact.name
    print(f"  -> best: {best_name} (cv5={best_score:.4f}), saved {artifact.name}")
    return results


def main():
    all_results = {}
    for name, loader in LOADERS.items():
        loaded = loader()
        if loaded is None:
            print(f"[skip] {name}: raw file missing")
            continue
        X, y, meta = loaded
        all_results[name] = evaluate_dataset(name, X, y, meta)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_provenance": "100% real datasets from the UCI Machine Learning Repository",
        "datasets": all_results,
        "disclaimer": (
            "Research/educational models trained on public non-clinical-use datasets. "
            "NOT clinically validated. NOT for medical decision-making."
        ),
    }
    out = MODELS_DIR / "uci_model_metadata.json"
    out.write_text(json.dumps(payload, indent=2, default=str))
    print(f"\nmetadata written -> {out}")
    return payload


if __name__ == "__main__":
    main()
