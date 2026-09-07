"""
NEURO_PREDICT_SYS Seed Data
Demo data for testing all modules.
"""
import uuid
import random
from datetime import datetime, timedelta
from database import get_db


def seed_all():
    """Seed all demo data into the database."""
    seed_patients()
    seed_diagnoses()
    seed_research_papers()
    seed_medications()
    seed_eeg_recordings()
    print("[SEED] All demo data seeded successfully")


def seed_patients():
    db = get_db()
    if db.count("patients") > 0:
        return

    patients = [
        {"first_name": "John", "last_name": "Mitchell", "date_of_birth": "1958-03-12", "gender": "male", "phone": "+1-555-0101", "email": "john.mitchell@email.com", "medical_record_number": "MRN-2024-001", "allergies": ["Penicillin"], "current_medications": ["Donepezil", "Memantine"]},
        {"first_name": "Maria", "last_name": "Garcia", "date_of_birth": "1971-07-22", "gender": "female", "phone": "+1-555-0102", "email": "maria.garcia@email.com", "medical_record_number": "MRN-2024-002", "allergies": [], "current_medications": ["Levodopa", "Carbidopa"]},
        {"first_name": "Robert", "last_name": "Thompson", "date_of_birth": "1965-11-08", "gender": "male", "phone": "+1-555-0103", "email": "robert.thompson@email.com", "medical_record_number": "MRN-2024-003", "allergies": ["Aspirin", "Ibuprofen"], "current_medications": ["Riluzole"]},
        {"first_name": "Aisha", "last_name": "Patel", "date_of_birth": "1988-01-30", "gender": "female", "phone": "+1-555-0104", "email": "aisha.patel@email.com", "medical_record_number": "MRN-2024-004", "allergies": [], "current_medications": ["Levetiracetam", "Lamotrigine"]},
        {"first_name": "David", "last_name": "Kim", "date_of_birth": "1975-05-17", "gender": "male", "phone": "+1-555-0105", "email": "david.kim@email.com", "medical_record_number": "MRN-2024-005", "allergies": ["Sulfa drugs"], "current_medications": ["Interferon beta"]},
        {"first_name": "Elena", "last_name": "Volkov", "date_of_birth": "1982-09-04", "gender": "female", "phone": "+1-555-0106", "email": "elena.volkov@email.com", "medical_record_number": "MRN-2024-006", "allergies": [], "current_medications": ["Sumatriptan"]},
        {"first_name": "William", "last_name": "Brown", "date_of_birth": "1948-12-15", "gender": "male", "phone": "+1-555-0107", "email": "william.brown@email.com", "medical_record_number": "MRN-2024-007", "allergies": ["Codeine"], "current_medications": ["Rivastigmine", "Memantine"]},
        {"first_name": "Sophie", "last_name": "Laurent", "date_of_birth": "1992-06-28", "gender": "female", "phone": "+1-555-0108", "email": "sophie.laurent@email.com", "medical_record_number": "MRN-2024-008", "allergies": [], "current_medications": []},
        {"first_name": "Ahmed", "last_name": "Hassan", "date_of_birth": "1960-08-19", "gender": "male", "phone": "+1-555-0109", "email": "ahmed.hassan@email.com", "medical_record_number": "MRN-2024-009", "allergies": ["Latex"], "current_medications": ["Temozolomide"]},
        {"first_name": "Lisa", "last_name": "Nguyen", "date_of_birth": "1985-04-11", "gender": "female", "phone": "+1-555-0110", "email": "lisa.nguyen@email.com", "medical_record_number": "MRN-2024-010", "allergies": [], "current_medications": ["Valproate"]},
    ]

    for p in patients:
        p["id"] = str(uuid.uuid4())
        db.insert("patients", p)

    print(f"[SEED] Inserted {len(patients)} demo patients")


def seed_diagnoses():
    db = get_db()
    if db.count("diagnoses") > 0:
        return

    patients = db.get_all("patients")
    if not patients:
        return

    diagnoses = [
        {"patient_idx": 0, "disease_name": "Alzheimer's Disease", "confidence_score": 0.942, "severity": "high", "symptoms": ["memory_loss", "confusion", "disorientation"], "status": "completed"},
        {"patient_idx": 1, "disease_name": "Parkinson's Disease", "confidence_score": 0.918, "severity": "high", "symptoms": ["tremor", "rigidity", "bradykinesia"], "status": "completed"},
        {"patient_idx": 2, "disease_name": "ALS", "confidence_score": 0.871, "severity": "critical", "symptoms": ["muscle_weakness", "fasciculations", "difficulty_speaking"], "status": "in_progress"},
        {"patient_idx": 3, "disease_name": "Epilepsy", "confidence_score": 0.965, "severity": "high", "symptoms": ["seizures", "temporary_confusion", "staring_spells"], "status": "completed"},
        {"patient_idx": 4, "disease_name": "Multiple Sclerosis", "confidence_score": 0.883, "severity": "medium", "symptoms": ["numbness", "vision_problems", "fatigue"], "status": "reviewed"},
        {"patient_idx": 5, "disease_name": "Migraine", "confidence_score": 0.931, "severity": "medium", "symptoms": ["headache", "nausea", "light_sensitivity"], "status": "completed"},
        {"patient_idx": 6, "disease_name": "Alzheimer's Disease", "confidence_score": 0.891, "severity": "high", "symptoms": ["memory_loss", "difficulty_with_tasks", "language_problems"], "status": "in_progress"},
        {"patient_idx": 7, "disease_name": "Epilepsy", "confidence_score": 0.782, "severity": "medium", "symptoms": ["seizures", "headache"], "status": "pending"},
        {"patient_idx": 8, "disease_name": "Brain Tumor", "confidence_score": 0.854, "severity": "critical", "symptoms": ["headache", "seizures", "personality_changes"], "status": "completed"},
        {"patient_idx": 9, "disease_name": "Epilepsy", "confidence_score": 0.812, "severity": "medium", "symptoms": ["seizures", "loss_of_consciousness"], "status": "in_progress"},
    ]

    for d in diagnoses:
        patient = patients[d["patient_idx"]]
        now = datetime.utcnow() - timedelta(days=random.randint(1, 30))
        db.insert("diagnoses", {
            "id": str(uuid.uuid4()),
            "patient_id": patient["id"],
            "disease_name": d["disease_name"],
            "confidence_score": d["confidence_score"],
            "severity": d["severity"],
            "status": d["status"],
            "symptoms": d["symptoms"],
            "notes": f"AI-assisted diagnosis for {d['disease_name']}",
            "diagnosed_by": "Dr. Sarah Chen",
            "created_at": now.isoformat(),
        })

    print(f"[SEED] Inserted {len(diagnoses)} demo diagnoses")


def seed_research_papers():
    db = get_db()
    if db.count("research_papers") > 0:
        return

    papers = [
        {
            "title": "Deep Learning Approaches for Early Alzheimer's Detection Using EEG Biomarkers",
            "authors": ["Chen, S.", "Wilson, J.", "Kumar, A."],
            "abstract": "This study presents a novel deep learning framework for early detection of Alzheimer's disease using EEG biomarkers. Our approach achieves 94.2% accuracy on a cohort of 2,500 patients, demonstrating significant improvement over traditional diagnostic methods.",
            "keywords": ["alzheimers", "eeg", "deep_learning", "early_detection"],
            "journal": "Neural Computation",
            "year": 2025,
            "doi": "10.1234/neur.2025.001",
            "category": "neurology",
            "citations": 47,
        },
        {
            "title": "Real-Time Parkinson's Disease Prediction Using Wearable Sensor Data and Transformer Models",
            "authors": ["Garcia, M.", "Thompson, R.", "Li, W."],
            "abstract": "We present a transformer-based model for real-time prediction of Parkinson's disease progression using wrist-worn accelerometers. The model predicts motor symptom severity with 89.3% accuracy across a 12-month validation period.",
            "keywords": ["parkinsons", "wearable_sensors", "transformer", "real_time"],
            "journal": "Movement Disorders",
            "year": 2025,
            "doi": "10.1234/md.2025.042",
            "category": "neurology",
            "citations": 31,
        },
        {
            "title": "Neural Correlates of Seizure Prediction: A Multi-Center EEG Study",
            "authors": ["Patel, A.", "Nguyen, L.", "Volkov, E."],
            "abstract": "This multi-center study analyzes EEG patterns preceding epileptic seizures across 8 clinical sites. We identify consistent pre-ictal signatures that enable seizure prediction 15-30 minutes before onset with 87.6% sensitivity.",
            "keywords": ["epilepsy", "seizure_prediction", "eeg", "multi_center"],
            "journal": "Epilepsia",
            "year": 2024,
            "doi": "10.1234/epi.2024.118",
            "category": "neurology",
            "citations": 62,
        },
        {
            "title": "AI-Driven Drug Interaction Prediction for Neurological Polypharmacy",
            "authors": ["Sharma, P.", "Brown, W.", "Kim, D."],
            "abstract": "We develop an AI system for predicting drug interactions in neurological patients on multiple medications. Validated against 15,000 prescription records, our model identifies 94% of adverse interactions with a false positive rate below 3%.",
            "keywords": ["drug_interactions", "polypharmacy", "ai", "pharmacology"],
            "journal": "Clinical Pharmacology & Therapeutics",
            "year": 2025,
            "doi": "10.1234/cpt.2025.089",
            "category": "pharmacology",
            "citations": 23,
        },
        {
            "title": "Surgical Planning Optimization for Deep Brain Stimulation Using 3D Neural Mapping",
            "authors": ["Thompson, M.", "Hassan, A.", "Laurent, S."],
            "abstract": "This paper presents an optimized surgical planning system for deep brain stimulation (DBS) electrode placement using AI-enhanced 3D neural mapping. Our approach reduces surgical time by 35% while improving targeting accuracy to sub-millimeter precision.",
            "keywords": ["deep_brain_stimulation", "surgical_planning", "3d_mapping", "neurosurgery"],
            "journal": "Stereotactic and Functional Neurosurgery",
            "year": 2025,
            "doi": "10.1234/sfn.2025.015",
            "category": "neurosurgery",
            "citations": 18,
        },
        {
            "title": "Machine Learning for Multiple Sclerosis Lesion Segmentation in MRI",
            "authors": ["Volkov, E.", "Mitchell, J.", "Garcia, M."],
            "abstract": "We propose a U-Net-based architecture for automated MS lesion segmentation in brain MRI scans. Achieving a Dice coefficient of 0.89 on multi-center data, our method significantly outperforms existing automated approaches.",
            "keywords": ["multiple_sclerosis", "mri", "lesion_segmentation", "deep_learning"],
            "journal": "NeuroImage: Clinical",
            "year": 2024,
            "doi": "10.1234/nic.2024.267",
            "category": "radiology",
            "citations": 39,
        },
    ]

    for paper in papers:
        paper["id"] = str(uuid.uuid4())
        db.insert("research_papers", paper)

    print(f"[SEED] Inserted {len(papers)} demo research papers")


def seed_medications():
    db = get_db()
    if db.count("medications") > 0:
        return

    medications = [
        {"name": "Donepezil", "generic_name": "Donepezil", "category": "Cholinesterase Inhibitor", "dosage_form": "tablet", "strength": "5mg/10mg", "manufacturer": "Pfizer", "stock_quantity": 500, "side_effects": ["nausea", "diarrhea", "insomnia"], "contraindications": ["liver_disease"]},
        {"name": "Levodopa/Carbidopa", "generic_name": "Levodopa", "category": "Dopamine Precursor", "dosage_form": "tablet", "strength": "25mg/100mg", "manufacturer": "Merck", "stock_quantity": 350, "side_effects": ["nausea", "dizziness", "dyskinesia"], "contraindications": ["narrow_angle_glaucoma"]},
        {"name": "Levetiracetam", "generic_name": "Levetiracetam", "category": "Anticonvulsant", "dosage_form": "tablet", "strength": "250mg/500mg", "manufacturer": "UCB Pharma", "stock_quantity": 800, "side_effects": ["drowsiness", "fatigue", "behavioral_changes"], "contraindications": []},
        {"name": "Riluzole", "generic_name": "Riluzole", "category": "Neuroprotective", "dosage_form": "tablet", "strength": "50mg", "manufacturer": "Sanofi", "stock_quantity": 200, "side_effects": ["nausea", "hepatotoxicity", "neutropenia"], "contraindications": ["severe_liver_disease"]},
        {"name": "Temozolomide", "generic_name": "Temozolomide", "category": "Alkylating Agent", "dosage_form": "capsule", "strength": "5mg/20mg/100mg", "manufacturer": "Merck", "stock_quantity": 150, "side_effects": ["myelosuppression", "nausea", "fatigue"], "contraindications": ["severe_bone_marrow_depression"]},
        {"name": "Lamotrigine", "generic_name": "Lamotrigine", "category": "Anticonvulsant", "dosage_form": "tablet", "strength": "25mg/100mg/200mg", "manufacturer": "GSK", "stock_quantity": 600, "side_effects": ["rash", "headache", "dizziness"], "contraindications": ["sjs_history"]},
        {"name": "Sumatriptan", "generic_name": "Sumatriptan", "category": "Triptan", "dosage_form": "tablet", "strength": "50mg/100mg", "manufacturer": "GlaxoSmithKline", "stock_quantity": 1000, "side_effects": ["tingling", "warmth_sensation", "dizziness"], "contraindications": ["cardiovascular_disease", "uncontrolled_hypertension"]},
        {"name": "Memantine", "generic_name": "Memantine", "category": "NMDA Receptor Antagonist", "dosage_form": "tablet", "strength": "5mg/10mg", "manufacturer": "Allergan", "stock_quantity": 450, "side_effects": ["headache", "confusion", "dizziness"], "contraindications": []},
        {"name": "Valproate", "generic_name": "Valproic Acid", "category": "Anticonvulsant", "dosage_form": "capsule", "strength": "250mg", "manufacturer": "AbbVie", "stock_quantity": 700, "side_effects": ["tremor", "weight_gain", "hair_loss"], "contraindications": ["liver_disease", "pregnancy"]},
        {"name": "Carbamazepine", "generic_name": "Carbamazepine", "category": "Anticonvulsant", "dosage_form": "tablet", "strength": "200mg", "manufacturer": "Novartis", "stock_quantity": 550, "side_effects": ["dizziness", "drowsiness", "rash"], "contraindications": ["bone_marrow_depression", "AV_block"]},
    ]

    for med in medications:
        med["id"] = str(uuid.uuid4())
        db.insert("medications", med)

    print(f"[SEED] Inserted {len(medications)} demo medications")


def seed_eeg_recordings():
    db = get_db()
    if db.count("eeg_recordings") > 0:
        return

    patients = db.get_all("patients")
    if not patients:
        return

    for patient in patients[:4]:
        t = np.linspace(0, 5, 1280)
        alpha = (10 * np.sin(2 * np.pi * 10 * t) + np.random.normal(0, 3, len(t))).tolist()
        beta = (5 * np.sin(2 * np.pi * 25 * t) + np.random.normal(0, 2, len(t))).tolist()
        delta = (15 * np.sin(2 * np.pi * 2 * t) + np.random.normal(0, 4, len(t))).tolist()

        db.insert("eeg_recordings", {
            "id": str(uuid.uuid4()),
            "patient_id": patient["id"],
            "channel_data": {"alpha": alpha[:100], "beta": beta[:100], "delta": delta[:100]},
            "duration_seconds": 5.0,
            "sample_rate": 256,
            "notes": f"Recording for {patient['first_name']} {patient['last_name']}",
        })

    print(f"[SEED] Inserted 4 demo EEG recordings")


import numpy as np
