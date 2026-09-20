# NEURO_PREDICT_SYS — Dataset Folder

Real datasets for training the disease-prediction models. **This folder replaces the
synthetic `backend/ml/brainlat_dataset.csv` pipeline as the primary data source.**

## Contents

| Folder | UCI ID | Task | Rows | Target |
|--------|--------|------|------|--------|
| `uciraw/beed_eeg_epilepsy/` | [1134](https://archive.ics.uci.edu/dataset/1134) | Epilepsy classification from 16-channel EEG | 8,000 | `y`: 0=Healthy, 1=Generalized seizure, 2=Focal seizure, 3=Seizure events |
| `uciraw/eeg_eye_state/` | [264](https://archive.ics.uci.edu/dataset/264) | Eye state from 14-channel EEG | 14,980 | `eyeDetection` (0/1) |
| `uciraw/parkinsons/` | [174](https://archive.ics.uci.edu/dataset/174) | Parkinson's from voice measurements | 197 | `status` (1 = PD) |
| `uciraw/mice_protein/` | [342](https://archive.ics.uci.edu/dataset/342) | Down syndrome mouse memory (trisomy biomarkers) | 1,080 | `class` (c-CS-s, t-SC-s, ...) |

## Provenance

All four are downloaded verbatim from the UCI Machine Learning Repository
(https://archive.ics.uci.edu). No values were altered. Raw archives are kept in
`uciraw/*.zip` so every training run can be reproduced byte-for-byte.

Licenses (from UCI dataset pages):

- **BEED (1134)** — Creative Commons Attribution 4.0 International (CC BY 4.0),
  DOI `10.24432/C5K33B`. Citation: Najmusseher . & Nizar Banu P K (2024),
  *Feature Engineering for Epileptic Seizure Classification Using SeqBoostNet*,
  Int. J. of Computing and Digital Systems.
- **EEG Eye State (264)**, **Parkinsons (174)**, **Mice Protein (342)** — UCI lists
  no explicit license; used here for **research/educational purposes only**.

No model trained on these datasets may be used for clinical decision-making.

## Training

```bash
python backend/ml/train_uci.py
```

Produces metrics in `backend/ml/models/uci_model_metadata.json` and (where the
feature schema is compatible) refreshed artifacts under `backend/ml/models/`.

## Datasets wanted but not available on UCI

- **Epileptic Seizure Recognition** (Andrzejak et al. 2001, 11,500 × 178 EEG) —
  removed from the current UCI catalog (old id 388 no longer resolves). Obtain it
  from the Bonn University source or Kaggle and place the CSV here as
  `epileptic_seizure_recognition.csv` — `train_uci.py` will pick it up automatically.
- **BrainLat** (real EEG/MRI/cognitive multimodal cohort) — the synthetic
  `backend/ml/brainlat_dataset.csv` stands in for it. Replace with the real cohort
  from https://doi.org/10.1038/s41597-023-02806-8 when access is granted.

## Known dataset gaps (for future collection)

| Gap | Why it matters | Candidate source |
|-----|----------------|------------------|
| No multi-class disease cohort | Real data covers epilepsy/PD/eye-state, not AD/bvFTD/MS | BrainLat (application required) |
| No AD/bvFTD/MS real samples | README's 5-class claim rests on synthetic data | ADNI, BrainLat |
| Small Parkinson's cohort (197) | Voice features only, high overfit risk | Parkinsons Telemonitoring (UCI 189, 5,875 rows) |
| No raw EEG for 8-class seizure taxonomy | BEED is binary | TUH EEG Corpus (license required) |
