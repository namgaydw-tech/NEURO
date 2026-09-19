"""
NEURO_PREDICT_SYS Data Models
Pydantic models for request/response schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ── Enums ──────────────────────────────────────────────────────────

class UserRole(str, Enum):
    ADMIN = "admin"
    NEUROLOGIST = "neurologist"
    NEUROSURGEON = "neurosurgeon"
    RADIOLOGIST = "radiologist"
    PHARMACIST = "pharmacist"
    OT_COORDINATOR = "ot_coordinator"
    ANESTHESIOLOGIST = "anesthesiologist"
    LAB_PROFESSIONAL = "lab_professional"
    NURSE = "nurse"
    CLINICAL_STAFF = "clinical_staff"
    RESEARCHER = "researcher"
    DEMO = "demo"


class DiagnosisStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REVIEWED = "reviewed"


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ── Auth Models ────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role: UserRole = UserRole.NEUROLOGIST
    department: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    department: Optional[str] = None
    clearance_level: int = 1


# ── Patient Models ─────────────────────────────────────────────────

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    medical_record_number: Optional[str] = None
    insurance_id: Optional[str] = None
    emergency_contact: Optional[str] = None
    allergies: Optional[List[str]] = []
    current_medications: Optional[List[str]] = []


class PatientResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    date_of_birth: str
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    medical_record_number: Optional[str] = None
    created_at: Optional[str] = None


class PatientListResponse(BaseModel):
    patients: List[PatientResponse]
    total: int
    page: int = 1
    per_page: int = 20


# ── Diagnosis Models ──────────────────────────────────────────────

class DiagnosisCreate(BaseModel):
    patient_id: str
    disease_name: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    severity: SeverityLevel = SeverityLevel.MEDIUM
    symptoms: List[str] = []
    notes: Optional[str] = None
    ai_prediction_id: Optional[str] = None


class DiagnosisResponse(BaseModel):
    id: str
    patient_id: str
    disease_name: str
    confidence_score: float
    severity: str
    status: str
    symptoms: List[str] = []
    notes: Optional[str] = None
    diagnosed_by: Optional[str] = None
    created_at: Optional[str] = None


# ── AI Analysis Models ────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    patient_id: str
    eeg_data: Optional[List[float]] = None
    symptoms: List[str] = []
    medical_history: Optional[str] = None
    clinical_data: Optional[dict] = None


class PredictionResult(BaseModel):
    disease: str
    confidence: float
    risk_level: str
    contributing_factors: List[str] = []
    recommended_actions: List[str] = []


class AnalysisResponse(BaseModel):
    id: str
    patient_id: str
    predictions: List[PredictionResult]
    overall_risk: str
    scan_progress: float = 0.0
    ai_confidence: float = 0.0
    brain_regions: dict = {}
    created_at: Optional[str] = None


# ── EEG Models ─────────────────────────────────────────────────────

class EEGRecordingCreate(BaseModel):
    patient_id: str
    channel_data: dict  # {"alpha": [...], "beta": [...], "delta": [...]}
    duration_seconds: float
    sample_rate: int = 256
    notes: Optional[str] = None


class EEGRecordingResponse(BaseModel):
    id: str
    patient_id: str
    channel_data: dict
    duration_seconds: float
    sample_rate: int
    signature_match: Optional[dict] = None
    ai_insights: Optional[List[str]] = None
    created_at: Optional[str] = None


# ── Research Models ────────────────────────────────────────────────

class ResearchPaperCreate(BaseModel):
    title: str
    authors: List[str]
    abstract: str
    keywords: List[str] = []
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    category: Optional[str] = None


class ResearchPaperResponse(BaseModel):
    id: str
    title: str
    authors: List[str]
    abstract: str
    keywords: List[str] = []
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    category: Optional[str] = None
    citations: int = 0
    created_at: Optional[str] = None


# ── Medication / Pharmacy Models ──────────────────────────────────

class MedicationCreate(BaseModel):
    name: str
    generic_name: Optional[str] = None
    category: str
    dosage_form: str  # tablet, capsule, injection, etc.
    strength: str
    manufacturer: Optional[str] = None
    requires_prescription: bool = True
    side_effects: List[str] = []
    contraindications: List[str] = []


class MedicationResponse(BaseModel):
    id: str
    name: str
    generic_name: Optional[str] = None
    category: str
    dosage_form: str
    strength: str
    stock_quantity: int = 0
    requires_prescription: bool = True


class PrescriptionCreate(BaseModel):
    patient_id: str
    medication_id: str
    dosage: str
    frequency: str
    duration_days: int
    instructions: Optional[str] = None
    prescribed_by: Optional[str] = None


# ── Pharmacy Profile Models ──────────────────────────────────────

class PharmacyProfileCreate(BaseModel):
    pharmacy_name: str
    pharmacy_code: str
    license_number: str
    address: str
    phone: str
    email: str
    operating_hours: str
    pharmacist_in_charge: Optional[str] = None


class PharmacyProfileUpdate(BaseModel):
    pharmacy_name: Optional[str] = None
    pharmacy_code: Optional[str] = None
    license_number: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    operating_hours: Optional[str] = None
    pharmacist_in_charge: Optional[str] = None


class PharmacyProfileResponse(BaseModel):
    id: str
    pharmacy_name: str
    pharmacy_code: str
    license_number: str
    address: str
    phone: str
    email: str
    operating_hours: str
    pharmacist_in_charge: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    specialty: Optional[str] = None
    employee_id: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    requested_role: Optional[str] = None
    role_status: Optional[str] = None
    department: Optional[str] = None
    specialty: Optional[str] = None
    employee_id: Optional[str] = None
    clearance_level: int
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ── Dashboard / Stats Models ──────────────────────────────────────

class DashboardStats(BaseModel):
    total_patients: int = 0
    active_cases: int = 0
    completed_diagnoses: int = 0
    research_papers: int = 0
    ai_analyses_today: int = 0
    nodes_active: str = "0"
    global_sync_rate: str = "0%"
    uptime: str = "99.97%"
