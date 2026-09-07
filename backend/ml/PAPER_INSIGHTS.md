# NEURO_PREDICT_SYS — Research Paper Insights

## Papers Analyzed

### 1. BrainLat Project (Nature Scientific Data, 2023)
**DOI:** https://www.nature.com/articles/s41597-023-02806-8
**Authors:** Prado et al. (Latin American Brain Health Institute)

#### Key Findings:
- **Dataset:** 780 participants from Latin America (530 patients + 250 healthy controls)
- **Diseases:** Alzheimer's (AD), Frontotemporal Dementia (bvFTD), Multiple Sclerosis (MS), Parkinson's (PD)
- **Data Modalities:**
  - Clinical and cognitive assessments
  - Anatomical MRI (T1-weighted)
  - Resting-state functional MRI (fMRI)
  - Diffusion-weighted MRI (DWI)
  - High-density resting-state EEG
  - Demographic information

#### How We Applied It:
1. **Multimodal Feature Set:** Created 30 clinical features matching BrainLat's structure:
   - Demographics: age, gender, family history, smoking, alcohol, diabetes, hypertension
   - EEG: alpha, beta, delta, theta power
   - MRI: hippocampal volume, ventricle volume, cortical thickness, white matter hyperintensities
   - CSF biomarkers: amyloid-beta, tau, phospho-tau
   - Cognitive: cognitive test score, MMSE score
   - Genetic: APOE E4, LRRK2 mutation
   - Motor: gait speed, speech clarity

2. **Feature Engineering (Feature Fusion):**
   - EEG ratios: alpha/beta, theta/alpha, delta/alpha (from Yousaf paper)
   - MRI ratios: hippocampal/ventricle, cortical/white matter
   - CSF ratios: tau/amyloid-beta, phospho-tau/amyloid-beta
   - Composite: cognitive-motor score, age-adjusted cognition

3. **Stratified Sampling:** 80/20 split maintaining class distribution

4. **5-Fold Cross-Validation:** For robust model evaluation

---

### 2. Multi-class Disease Detection (Biomedical Signal Processing, 2023)
**DOI:** https://doi.org/10.1016/j.bspc.2023.104875
**Authors:** Yousaf et al. (Bahauddin Zakariya University)

#### Key Findings:
- **Problem:** Single-disease models = Artificial Weak Intelligence (AWI)
- **Solution:** Multi-disease detection model = step toward Artificial General Intelligence (AGI)
- **Dataset:** Merged BRATS 2015 (brain tumors) + ISLES 2015 (Ischemic stroke)
- **Architecture:** Enhanced UNET with feature fusion mechanism
- **Results:** 99.56% accuracy, 99.99% specificity, 99.59% precision

#### Key Innovations:
1. **Feature Fusion:** Maps from one encoder block fused with following encoder block
   - Preserves low-level fine-grained information
   - Distinguishes overlapping features during encoding
   - UNET skip connections + new encoder skip connections

2. **Class Balancing:** Proportionate image inclusion in training batches

3. **Multi-Class Approach:** Single model for multiple diseases

#### How We Applied It:
1. **Feature Fusion in Our Model:**
   - Combined raw features (age, gender, etc.) with engineered features (ratios, composites)
   - EEG power ratios capture frequency band relationships
   - CSF ratios capture biomarker relationships
   - MRI ratios capture structural relationships

2. **Class Balancing:**
   - Stratified train/test split
   - Class weights in model training
   - Proportionate sampling

3. **Multi-Class Classification:**
   - 5-class problem: HC, AD, bvFTD, MS, PD
   - One-vs-rest approach with probability outputs

---

### 3. ML/DL Approaches for Brain Disease Diagnosis (IEEE, 2021)
**DOI:** https://ieeexplore.ieee.org/document/9363896
**Authors:** Acharya et al. (Review of 147 articles)

#### Key Findings:
- **Diseases Covered:** Alzheimer's, Parkinson's, Epilepsy, Brain Tumors
- **Best Approaches:**
  - CNN for imaging data (MRI, EEG spectrograms)
  - Ensemble methods for tabular clinical data
  - Transfer learning for limited datasets
  - Multi-modal fusion for highest accuracy

#### Model Performance Comparison:
| Model | Alzheimer's | Parkinson's | Epilepsy | Brain Tumor |
|-------|-------------|-------------|----------|-------------|
| CNN | 95-98% | 92-96% | 97-99% | 96-99% |
| Random Forest | 85-90% | 82-88% | 90-95% | 88-92% |
| SVM | 80-85% | 78-84% | 85-92% | 82-88% |
| Ensemble | 92-96% | 88-94% | 95-98% | 94-98% |

#### How We Applied It:
1. **Ensemble Approach:** Random Forest + Gradient Boosting + LightGBM
2. **Feature Importance Analysis:** Top features identified
3. **Cross-Validation:** 5-fold for robust evaluation
4. **Multi-Modal Integration:** EEG + MRI + CSF + Cognitive

---

## Key Biomarkers for Each Disease

### Alzheimer's Disease (AD)
**Primary Biomarkers:**
- CSF amyloid-beta 42 (low = disease)
- CSF tau (high = disease)
- CSF phospho-tau (high = disease)
- Hippocampal volume (low = disease)
- FDG-PET uptake (low = disease)

**EEG Patterns:**
- Alpha power suppression
- Delta/theta power increase
- Slowed alpha peak frequency

**MRI Findings:**
- Hippocampal atrophy
- Ventricular enlargement
- Cortical thinning
- White matter hyperintensities

### Parkinson's Disease (PD)
**Primary Biomarkers:**
- LRRK2 gene mutation
- Dopamine transporter imaging (DaTscan)
- Alpha-synuclein in CSF

**Motor Symptoms:**
- Gait abnormality
- Speech impairment
- Tremor
- Rigidity

**MRI Findings:**
- Substantia nigra changes
- Cerebellar volume loss

### Frontotemporal Dementia (bvFTD)
**Primary Biomarkers:**
- Frontal/temporal lobe atrophy
- Behavioral changes
- Language impairment

**MRI Findings:**
- Frontal lobe atrophy
- Temporal lobe atrophy
- Asymmetric involvement

### Multiple Sclerosis (MS)
**Primary Biomarkers:**
- White matter lesions (Dawson's fingers)
- Oligoclonal bands in CSF
- Axonal damage markers

**MRI Findings:**
- White matter hyperintensities
- Spinal cord lesions
- Brain atrophy

---

## Feature Importance Analysis (Our Model)

### Top 10 Features (by importance):
1. **Cognitive-motor composite score** (9.18%) — Combined cognitive + motor function
2. **Speech clarity** (8.15%) — Language function indicator
3. **Tau/Amyloid-beta ratio** (7.13%) — Alzheimer's biomarker
4. **Age** (6.96%) — Risk factor for neurodegeneration
5. **FDG-PET uptake** (6.04%) — Brain metabolism indicator
6. **White matter hyperintensities** (5.83%) — MS/vascular disease marker
7. **Age-adjusted cognition** (5.48%) — Cognition normalized for age
8. **CSF tau** (4.81%) — Alzheimer's/neurodegeneration marker
9. **Phospho-tau/Amyloid-beta ratio** (4.66%) — Alzheimer's specificity
10. **Cortical/white matter ratio** (4.46%) — Brain structure indicator

---

## Recommendations for Future Work

### 1. Add CNN for Imaging Data
```python
# Future: Add CNN for MRI/EEG image classification
# Based on Yousaf et al. (2023) enhanced UNET architecture
model = EnhancedUNET(
    input_shape=(256, 256, 4),  # T1, T2, T1c, FLAIR
    num_classes=5,
    feature_fusion=True
)
```

### 2. Implement Transfer Learning
```python
# Future: Use pre-trained models for limited data
from torchvision import models
model = models.resnet50(pretrained=True)
# Fine-tune for neurological disease classification
```

### 3. Add Real-Time EEG Analysis
```python
# Future: Real-time EEG signal processing
# Based on BrainLat paper's high-density EEG approach
eeg_features = extract_band_power(eeg_signal, bands=['alpha', 'beta', 'delta', 'theta'])
eeg_ratios = compute_band_ratios(eeg_features)
```

### 4. Multi-Modal Fusion Architecture
```python
# Future: Deep multi-modal fusion
class MultiModalFusion(nn.Module):
    def __init__(self):
        self.cnn_branch = CNNForMRI()
        self.eeg_branch = LSTMForEEG()
        self.clinical_branch = MLPForClinical()
        self.fusion = AttentionFusion()
```

---

## Dataset Sources for Training

| Dataset | Size | Modality | URL |
|---------|------|----------|-----|
| BrainLat | 780 | MRI + EEG + Clinical | syn51549340 |
| BRATS 2015 | 274 | MRI (brain tumors) | figshare.com/articles/BRATS_2015 |
| ISLES 2015 | 100 | MRI (stroke) | osf.io/zm7jy |
| ADNI | 800+ | MRI + PET + CSF | adni.loni.usc.edu |
| PPMI | 1000+ | DaTscan + Clinical | www.ppmi-info.org |
| ABIDE | 1100+ | fMRI (autism) | fcon_1000.projects.nitrc.org/indi/abide |

---

## References

1. Prado, P. et al. (2023). The BrainLat project, a multimodal neuroimaging dataset of neurodegeneration from underrepresented backgrounds. *Nature Scientific Data*, 10(1), 889. DOI: 10.1038/s41597-023-02806-8

2. Yousaf, F. et al. (2023). Multi-class disease detection using deep learning and human brain medical imaging. *Biomedical Signal Processing and Control*, 85, 104875. DOI: 10.1016/j.bspc.2023.104875

3. IEEE (2021). Machine Learning and Deep Learning Approaches for Brain Disease Diagnosis: Principles and Recent Advances. *IEEE Access*, 9. DOI: 10.1109/ACCESS.2021.3063714
