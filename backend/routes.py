"""
NEURO_PREDICT_SYS API Routes
All REST API endpoints for the system.
"""
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from core.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_admin, seed_demo_accounts, require_role,
    require_permission, audit_logger, DEMO_ACCOUNTS, create_refresh_token,
    hash_token, generate_refresh_token
)
from core.database import get_db
from models import (
    UserCreate, UserLogin, TokenResponse,
    PatientCreate, PatientResponse, PatientListResponse,
    DiagnosisCreate, DiagnosisResponse,
    AnalysisRequest, AnalysisResponse,
    EEGRecordingCreate, EEGRecordingResponse,
    ResearchPaperCreate, ResearchPaperResponse,
    MedicationCreate, MedicationResponse,
    DashboardStats,
    PharmacyProfileCreate, PharmacyProfileUpdate, PharmacyProfileResponse,
    UserProfileUpdate, UserProfileResponse
)
from ml import predictor

router = APIRouter()


# ══════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ══════════════════════════════════════════════════════════════════

from fastapi import Request
from core.auth import require_rate_limit


@router.post("/auth/register", response_model=TokenResponse,
             dependencies=[Depends(require_rate_limit(5, 60, "register"))])
async def register(user: UserCreate, request: Request):
    db = get_db()
    # Check existing
    existing = [u for u in db.get_all("users") if u.get("email") == user.email]
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_data = {
        "id": str(uuid.uuid4()),
        "email": user.email,
        "password_hash": hash_password(user.password),
        "full_name": user.full_name,
        "role": user.role.value,
        "department": user.department,
        "clearance_level": 2,
        "is_active": True,
    }
    db.insert("users", user_data)
    audit_logger.log("user.registered", user_data["id"], "user", user_data["id"], request=request)

    access_token = create_access_token({"sub": user_data["id"], "role": user_data["role"]})
    refresh_token = create_refresh_token({"sub": user_data["id"], "role": user_data["role"]})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={k: v for k, v in user_data.items() if k != "password_hash"}
    )


@router.post("/auth/login", response_model=TokenResponse,
             dependencies=[Depends(require_rate_limit(10, 60, "login"))])
async def login(creds: UserLogin, request: Request):
    db = get_db()
    users = db.get_all("users")
    user = next((u for u in users if u.get("email") == creds.email), None)

    if not user or not verify_password(creds.password, user.get("password_hash", "")):
        audit_logger.log("login.failed", creds.email, "auth", result="failure", request=request)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": user["id"], "role": user["role"]})
    refresh_token = create_refresh_token({"sub": user["id"], "role": user["role"]})
    audit_logger.log("login.success", user["id"], "auth", result="success", request=request)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={k: v for k, v in user.items() if k != "password_hash"}
    )


@router.get("/auth/me")
async def get_me(user=Depends(get_current_user)):
    return {k: v for k, v in user.items() if k != "password_hash"}


@router.get("/auth/demo-accounts")
async def list_demo_accounts():
    """List available demo accounts for testing. Passwords excluded."""
    return [
        {"email": a["email"], "role": a["role"],
         "full_name": a["full_name"], "department": a["department"]}
        for a in DEMO_ACCOUNTS
    ]


# ══════════════════════════════════════════════════════════════════
# PATIENT ROUTES
# ══════════════════════════════════════════════════════════════════

@router.get("/patients", response_model=PatientListResponse)
async def list_patients(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    user=Depends(get_current_user)
):
    db = get_db()
    patients = db.get_all("patients")

    if search:
        search_lower = search.lower()
        patients = [
            p for p in patients
            if search_lower in p.get("first_name", "").lower()
            or search_lower in p.get("last_name", "").lower()
            or search_lower in p.get("medical_record_number", "").lower()
            or search_lower in p.get("email", "").lower()
        ]

    total = len(patients)
    start = (page - 1) * per_page
    end = start + per_page
    page_patients = patients[start:end]

    return PatientListResponse(
        patients=[PatientResponse(**p) for p in page_patients],
        total=total, page=page, per_page=per_page
    )


@router.get("/patients/{patient_id}")
async def get_patient(patient_id: str, user=Depends(get_current_user)):
    db = get_db()
    patient = db.get("patients", patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Include diagnoses
    diagnoses = [d for d in db.get_all("diagnoses") if d.get("patient_id") == patient_id]
    eeg_count = len([e for e in db.get_all("eeg_recordings") if e.get("patient_id") == patient_id])

    return {
        **patient,
        "diagnoses": diagnoses,
        "eeg_recordings_count": eeg_count,
    }


@router.post("/patients")
async def create_patient(patient: PatientCreate, user=Depends(require_role("admin", "neurologist", "surgeon"))):
    db = get_db()
    data = patient.model_dump()
    data["id"] = str(uuid.uuid4())
    data["created_at"] = datetime.utcnow().isoformat()
    db.insert("patients", data)
    return data


@router.put("/patients/{patient_id}")
async def update_patient(patient_id: str, patient: PatientCreate, user=Depends(require_role("admin", "neurologist", "surgeon"))):
    db = get_db()
    existing = db.get("patients", patient_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Patient not found")

    data = patient.model_dump()
    data["updated_at"] = datetime.utcnow().isoformat()
    db.update("patients", patient_id, data)
    return db.get("patients", patient_id)


@router.delete("/patients/{patient_id}")
async def delete_patient(patient_id: str, user=Depends(require_admin)):
    db = get_db()
    if not db.delete("patients", patient_id):
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"message": "Patient deleted"}


# ══════════════════════════════════════════════════════════════════
# DIAGNOSIS ROUTES
# ══════════════════════════════════════════════════════════════════

@router.get("/diagnoses")
async def list_diagnoses(
    patient_id: Optional[str] = None,
    status: Optional[str] = None,
    user=Depends(get_current_user)
):
    db = get_db()
    diagnoses = db.get_all("diagnoses")
    if patient_id:
        diagnoses = [d for d in diagnoses if d.get("patient_id") == patient_id]
    if status:
        diagnoses = [d for d in diagnoses if d.get("status") == status]
    return diagnoses


@router.get("/diagnoses/{diagnosis_id}")
async def get_diagnosis(diagnosis_id: str, user=Depends(get_current_user)):
    db = get_db()
    diagnosis = db.get("diagnoses", diagnosis_id)
    if not diagnosis:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    return diagnosis


@router.post("/diagnoses")
async def create_diagnosis(diag: DiagnosisCreate, user=Depends(require_role("admin", "neurologist", "surgeon"))):
    db = get_db()
    data = diag.model_dump()
    data["id"] = str(uuid.uuid4())
    data["status"] = "completed"
    data["diagnosed_by"] = user.get("full_name", "Unknown")
    db.insert("diagnoses", data)
    return data


class DiagnosisUpdate(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None
    notes: Optional[str] = None
    confidence_score: Optional[float] = Field(ge=0.0, le=1.0, default=None)


@router.put("/diagnoses/{diagnosis_id}")
async def update_diagnosis(diagnosis_id: str, update: DiagnosisUpdate,
                           user=Depends(require_role("admin", "neurologist", "surgeon"))):
    db = get_db()
    existing = db.get("diagnoses", diagnosis_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    # Only update fields that were explicitly set (whitelist)
    allowed_updates = update.model_dump(exclude_unset=True)
    if not allowed_updates:
        return existing
    db.update("diagnoses", diagnosis_id, allowed_updates)
    audit_logger.log("diagnosis.updated", user.get("id"), "diagnosis", diagnosis_id,
                     action="update", request=None)
    return db.get("diagnoses", diagnosis_id)


# ══════════════════════════════════════════════════════════════════
# AI ANALYSIS ROUTES
# ══════════════════════════════════════════════════════════════════

@router.post("/analysis/predict")
async def run_prediction(request: AnalysisRequest, user=Depends(require_role("admin", "neurologist", "researcher"))):
    """Run AI disease prediction for a patient."""
    db = get_db()

    # Run ML prediction (uses trained model if clinical_data provided)
    result = predictor.predict(
        symptoms=request.symptoms,
        eeg_data=request.eeg_data,
        medical_history=request.medical_history,
        clinical_data=request.clinical_data,
    )

    # Store analysis result
    analysis_data = {
        "id": str(uuid.uuid4()),
        "patient_id": request.patient_id,
        "predictions": result["predictions"],
        "overall_risk": result["overall_risk"],
        "ai_confidence": result["ai_confidence"],
        "brain_regions": result["brain_regions"],
        "scan_progress": result["scan_progress"],
        "run_by": user.get("full_name", "Unknown"),
    }
    db.insert("analyses", analysis_data)

    return analysis_data


@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str, user=Depends(get_current_user)):
    db = get_db()
    analysis = db.get("analyses", analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.get("/analysis/patient/{patient_id}")
async def get_patient_analyses(patient_id: str, user=Depends(get_current_user)):
    db = get_db()
    analyses = [a for a in db.get_all("analyses") if a.get("patient_id") == patient_id]
    return analyses


# ══════════════════════════════════════════════════════════════════
# AI AGENT PIPELINE — LangGraph accuracy + OpenAI Agent SDK reasoning
# + CrewAI report structuring
# ══════════════════════════════════════════════════════════════════

class AgentPipelineRequest(BaseModel):
    """Input to the three-agent decision-support pipeline."""
    disease: str = Field(..., max_length=120, description="Candidate prediction label")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Claimed model confidence 0..1")
    signals: List[str] = Field(default_factory=list, max_length=50, description="EEG/clinical signals used")
    medical_history: Optional[str] = Field(None, max_length=2000)
    recommendations: Optional[List[str]] = Field(None, max_length=20)
    summary: Optional[str] = Field(None, max_length=1000)


@router.post("/agents/pipeline", tags=["agents"])
async def run_agent_pipeline(
    request: AgentPipelineRequest,
    user=Depends(require_role("admin", "neurologist", "researcher")),
):
    """Run the 3-agent pipeline: LangGraph accuracy cross-check,
    OpenAI Agent SDK clinical reasoning, CrewAI report structuring.

    Every stage reports `mode` (`llm` or `fallback_no_api_key`) so
    heuristic output is never mistaken for LLM output.
    """
    from ai_agents import accuracy_check, clinical_reasoning, structured_report

    accuracy = accuracy_check(request.disease, request.confidence)
    reasoning = clinical_reasoning(
        request.disease,
        request.confidence,
        context={
            "signals": request.signals,
            "medical_history": request.medical_history,
        },
    )
    report = structured_report({
        "disease": request.disease,
        "confidence": request.confidence,
        "signals": request.signals,
        "accuracy": accuracy,
        "reasoning_steps": reasoning.get("reasoning_steps"),
        "summary": request.summary,
        "recommendations": request.recommendations,
    })
    audit_logger.log(
        "agents.pipeline.run", user.get("id"),
        resource_type="analysis", resource_id=request.disease[:120],
        result="success",
    )
    return {
        "accuracy": accuracy,
        "reasoning": reasoning,
        "report": report,
        "run_by": user.get("full_name", "Unknown"),
        "disclaimer": (
            "Research/decision-support pipeline. NOT a clinical diagnosis. "
            "Not clinically validated."
        ),
    }


# ══════════════════════════════════════════════════════════════════
# EEG ROUTES
# ══════════════════════════════════════════════════════════════════

@router.post("/eeg/record")
async def record_eeg(recording: EEGRecordingCreate, user=Depends(require_role("admin", "neurologist"))):
    db = get_db()

    # Analyze the EEG data
    analysis = predictor.analyze_eeg(recording.channel_data)

    data = recording.model_dump()
    data["id"] = str(uuid.uuid4())
    data["signature_match"] = analysis["signature_match"]
    data["ai_insights"] = analysis["ai_insights"]
    db.insert("eeg_recordings", data)

    return {**data, "quality_score": analysis["quality_score"],
            "artifacts_detected": analysis["artifacts_detected"]}


@router.get("/eeg/patient/{patient_id}")
async def get_patient_eeg(patient_id: str, user=Depends(get_current_user)):
    db = get_db()
    recordings = [e for e in db.get_all("eeg_recordings") if e.get("patient_id") == patient_id]
    return recordings


@router.get("/eeg/{recording_id}")
async def get_eeg_recording(recording_id: str, user=Depends(get_current_user)):
    db = get_db()
    recording = db.get("eeg_recordings", recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="EEG recording not found")
    return recording


# ══════════════════════════════════════════════════════════════════
# RESEARCH PAPER ROUTES
# ══════════════════════════════════════════════════════════════════

@router.get("/research")
async def list_research(
    search: Optional[str] = None,
    category: Optional[str] = None,
    user=Depends(get_current_user)
):
    db = get_db()
    papers = db.get_all("research_papers")

    if search:
        search_lower = search.lower()
        papers = [
            p for p in papers
            if search_lower in p.get("title", "").lower()
            or search_lower in " ".join(p.get("keywords", [])).lower()
            or search_lower in " ".join(p.get("authors", [])).lower()
        ]

    if category:
        papers = [p for p in papers if p.get("category") == category]

    return papers


@router.get("/research/{paper_id}")
async def get_research_paper(paper_id: str, user=Depends(get_current_user)):
    db = get_db()
    paper = db.get("research_papers", paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@router.post("/research")
async def create_research_paper(paper: ResearchPaperCreate, user=Depends(require_role("admin", "researcher"))):
    db = get_db()
    data = paper.model_dump()
    data["id"] = str(uuid.uuid4())
    data["citations"] = 0
    db.insert("research_papers", data)
    return data


# ══════════════════════════════════════════════════════════════════
# MEDICATION / PHARMACY ROUTES
# ══════════════════════════════════════════════════════════════════

@router.get("/medications")
async def list_medications(
    search: Optional[str] = None,
    category: Optional[str] = None,
    user=Depends(get_current_user)
):
    db = get_db()
    meds = db.get_all("medications")

    if search:
        search_lower = search.lower()
        meds = [
            m for m in meds
            if search_lower in m.get("name", "").lower()
            or search_lower in m.get("generic_name", "").lower()
        ]

    if category:
        meds = [m for m in meds if m.get("category") == category]

    return meds


@router.get("/medications/{med_id}")
async def get_medication(med_id: str, user=Depends(get_current_user)):
    db = get_db()
    med = db.get("medications", med_id)
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    return med


@router.post("/medications")
async def create_medication(med: MedicationCreate, user=Depends(require_admin)):
    db = get_db()
    data = med.model_dump()
    data["id"] = str(uuid.uuid4())
    db.insert("medications", data)
    return data


# ══════════════════════════════════════════════════════════════════
# DASHBOARD STATS
# ══════════════════════════════════════════════════════════════════

@router.get("/dashboard/stats")
async def get_dashboard_stats(user=Depends(get_current_user)):
    db = get_db()
    return DashboardStats(
        total_patients=db.count("patients"),
        active_cases=db.count("diagnoses", {"status": "in_progress"})
                    + db.count("diagnoses", {"status": "pending"}),
        completed_diagnoses=db.count("diagnoses", {"status": "completed"}),
        research_papers=db.count("research_papers"),
        ai_analyses_today=db.count("analyses"),
        nodes_active="5,247,893",
        global_sync_rate="99.4%",
        uptime="99.97%",
    )


@router.get("/dashboard/activity")
async def get_dashboard_activity(user=Depends(get_current_user)):
    db = get_db()
    recent_diagnoses = db.get_all("diagnoses")[-5:]
    recent_analyses = db.get_all("analyses")[-5:]
    return {
        "recent_diagnoses": recent_diagnoses,
        "recent_analyses": recent_analyses,
        "system_health": {
            "cpu_usage": 34,
            "memory_usage": 62,
            "gpu_usage": 78,
            "network_latency": 12,
        }
    }


# ══════════════════════════════════════════════════════════════════
# PHARMACY PROFILE ROUTES
# ══════════════════════════════════════════════════════════════════

@router.get("/pharmacy/profile")
async def get_pharmacy_profile(user=Depends(get_current_user)):
    """Get the pharmacy profile for the current user's pharmacy."""
    db = get_db()
    profiles = db.get_all("pharmacy_profiles")
    # Return the first profile (in production, filter by user/pharmacy)
    if profiles:
        return PharmacyProfileResponse(**profiles[0])
    return {"detail": "No pharmacy profile found"}


@router.post("/pharmacy/profile")
async def create_pharmacy_profile(
    profile: PharmacyProfileCreate,
    user=Depends(require_role("admin", "pharmacist"))
):
    """Create or update the pharmacy profile."""
    db = get_db()
    existing = db.get_all("pharmacy_profiles")
    
    if existing:
        # Update existing
        data = profile.model_dump()
        data["updated_at"] = datetime.utcnow().isoformat()
        db.update("pharmacy_profiles", existing[0]["id"], data)
        return PharmacyProfileResponse(**db.get("pharmacy_profiles", existing[0]["id"]))
    
    # Create new
    data = profile.model_dump()
    data["id"] = str(uuid.uuid4())
    data["created_at"] = datetime.utcnow().isoformat()
    data["updated_at"] = datetime.utcnow().isoformat()
    db.insert("pharmacy_profiles", data)
    return PharmacyProfileResponse(**data)


@router.put("/pharmacy/profile/{profile_id}")
async def update_pharmacy_profile(
    profile_id: str,
    profile: PharmacyProfileUpdate,
    user=Depends(require_role("admin", "pharmacist"))
):
    """Update a pharmacy profile."""
    db = get_db()
    existing = db.get("pharmacy_profiles", profile_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Pharmacy profile not found")
    
    data = profile.model_dump(exclude_unset=True)
    data["updated_at"] = datetime.utcnow().isoformat()
    db.update("pharmacy_profiles", profile_id, data)
    return PharmacyProfileResponse(**db.get("pharmacy_profiles", profile_id))


@router.get("/users/me/profile")
async def get_my_profile(user=Depends(get_current_user)):
    """Get the current user's full profile."""
    return {
        "id": user.get("id"),
        "email": user.get("email"),
        "full_name": user.get("full_name"),
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "role": user.get("role"),
        "requested_role": user.get("requested_role"),
        "role_status": user.get("role_status"),
        "department": user.get("department"),
        "specialty": user.get("specialty"),
        "employee_id": user.get("employee_id"),
        "clearance_level": user.get("clearance_level"),
        "phone": user.get("phone"),
        "bio": user.get("bio"),
        "avatar_url": user.get("avatar_url"),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
    }


@router.put("/users/me/profile")
async def update_my_profile(
    profile: UserProfileUpdate,
    user=Depends(get_current_user)
):
    """Update the current user's profile information."""
    db = get_db()
    user_id = user.get("id")
    
    existing = db.get("users", user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = profile.model_dump(exclude_unset=True)
    # Prevent mass assignment of privileged fields
    forbidden_fields = {"role", "clearance_level", "is_active", "id"}
    if user.get("role") != "admin":
        for field in forbidden_fields:
            update_data.pop(field, None)
    update_data["updated_at"] = datetime.utcnow().isoformat()
    db.update("users", user_id, update_data)
    
    updated_user = db.get("users", user_id)
    updated_user = db.get("users", user_id)
    return {
        "id": updated_user.get("id"),
        "email": updated_user.get("email"),
        "full_name": updated_user.get("full_name"),
        "first_name": updated_user.get("first_name"),
        "last_name": updated_user.get("last_name"),
        "role": updated_user.get("role"),
        "requested_role": updated_user.get("requested_role"),
        "role_status": updated_user.get("role_status"),
        "department": updated_user.get("department"),
        "specialty": updated_user.get("specialty"),
        "employee_id": updated_user.get("employee_id"),
        "clearance_level": updated_user.get("clearance_level"),
        "phone": updated_user.get("phone"),
        "bio": updated_user.get("bio"),
        "avatar_url": updated_user.get("avatar_url"),
        "created_at": updated_user.get("created_at"),
        "updated_at": updated_user.get("updated_at"),
    }


# ══════════════════════════════════════════════════════════════════
# ACCOUNT SECURITY ROUTES
# ══════════════════════════════════════════════════════════════════

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


@router.post("/users/me/change-password")
async def change_password(
    body: ChangePasswordRequest,
    user=Depends(get_current_user),
    request: Request = None,
):
    """Change the current user's password."""
    db = get_db()
    user_id = user.get("id")
    full_user = db.get("users", user_id)

    if not full_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify current password
    if not verify_password(body.current_password, full_user.get("password_hash", "")):
        audit_logger.log("password.change.failed", user_id, "auth",
                         result="invalid_current_password", request=request)
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # Hash and store new password
    new_hash = hash_password(body.new_password)
    db.update("users", user_id, {
        "password_hash": new_hash,
        "updated_at": datetime.utcnow().isoformat(),
    })

    audit_logger.log("password.changed", user_id, "auth", result="success", request=request)
    return {"message": "Password changed successfully"}


@router.get("/users/me/sessions")
async def get_my_sessions(user=Depends(get_current_user)):
    """List audit events (sessions) for the current user."""
    events = audit_logger.get_events(limit=50, actor_id=user.get("id"))
    # Filter to auth-related events
    auth_events = [e for e in events if e.get("event_type").startswith(("login.", "auth.", "password."))]
    return auth_events


@router.get("/users/me/audit-log")
async def get_my_audit_log(
    limit: int = Query(50, ge=1, le=200),
    user=Depends(get_current_user),
):
    """Get the current user's audit trail."""
    events = audit_logger.get_events(limit=limit, actor_id=user.get("id"))
    return events


@router.get("/admin/audit-log")
async def get_admin_audit_log(
    limit: int = Query(100, ge=1, le=500),
    event_type: Optional[str] = None,
    user=Depends(require_admin),
):
    """Admin: view all audit events."""
    events = audit_logger.get_events(limit=limit, event_type=event_type)
    return events


@router.get("/admin/users")
async def list_users(user=Depends(require_admin)):
    """Admin: list all users."""
    db = get_db()
    users = db.get_all("users")
    return [{k: v for k, v in u.items() if k != "password_hash"} for u in users]


# ══════════════════════════════════════════════════════════════════
# OT SCHEDULING ROUTES
# ══════════════════════════════════════════════════════════════════

class TheaterCreate(BaseModel):
    name: str
    location: str
    capacity: int
    equipment: List[str] = []
    status: str = "available"


class TheaterResponse(BaseModel):
    id: str
    name: str
    location: str
    capacity: int
    equipment: List[str] = []
    status: str
    created_at: Optional[str] = None


class TimeSlotCreate(BaseModel):
    theater_id: str
    date: str  # YYYY-MM-DD format
    start_time: str  # HH:MM format
    end_time: str  # HH:MM format
    slot_type: str = "scheduled"  # scheduled, available, blocked
    notes: Optional[str] = None


class TimeSlotResponse(BaseModel):
    id: str
    theater_id: str
    date: str
    start_time: str
    end_time: str
    slot_type: str
    booked_by: Optional[str] = None
    patient_name: Optional[str] = None
    procedure: Optional[str] = None
    status: str = "available"  # available, booked, blocked, completed
    notes: Optional[str] = None
    created_at: Optional[str] = None


class BookingUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None
    assistant_name: Optional[str] = None
    anesthesia_type: Optional[str] = None


class BookingCreate(BaseModel):
    slot_id: str
    patient_name: str
    patient_id: Optional[str] = None
    procedure: str
    surgeon_name: str
    assistant_name: Optional[str] = None
    anesthesia_type: str = "general"
    priority: str = "normal"  # normal, urgent, emergency
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    id: str
    slot_id: str
    patient_name: str
    patient_id: Optional[str] = None
    procedure: str
    surgeon_name: str
    assistant_name: Optional[str] = None
    anesthesia_type: str
    priority: str
    status: str = "confirmed"  # confirmed, in_progress, completed, cancelled
    notes: Optional[str] = None
    created_at: Optional[str] = None


@router.get("/ot/theaters")
async def list_theaters(user=Depends(get_current_user)):
    """List all operating theaters."""
    db = get_db()
    theaters = db.get_all("ot_theaters")
    return [TheaterResponse(**t) for t in theaters]


@router.post("/ot/theaters")
async def create_theater(
    theater: TheaterCreate,
    user=Depends(require_role("admin", "surgeon"))
):
    """Create a new operating theater."""
    db = get_db()
    data = theater.model_dump()
    data["id"] = str(uuid.uuid4())
    data["created_at"] = datetime.utcnow().isoformat()
    db.insert("ot_theaters", data)
    return TheaterResponse(**data)


@router.get("/ot/slots")
async def list_slots(
    date: Optional[str] = None,
    theater_id: Optional[str] = None,
    user=Depends(get_current_user)
):
    """List time slots, optionally filtered by date and theater."""
    db = get_db()
    slots = db.get_all("ot_slots")
    
    if date:
        slots = [s for s in slots if s.get("date") == date]
    if theater_id:
        slots = [s for s in slots if s.get("theater_id") == theater_id]
    
    return [TimeSlotResponse(**s) for s in slots]


@router.post("/ot/slots")
async def create_slot(
    slot: TimeSlotCreate,
    user=Depends(require_role("admin", "surgeon"))
):
    """Create a new time slot."""
    db = get_db()
    
    # Check for conflicts
    existing_slots = db.get_all("ot_slots")
    for existing in existing_slots:
        if (existing.get("theater_id") == slot.theater_id and 
            existing.get("date") == slot.date):
            # Check time overlap
            existing_start = existing.get("start_time", "00:00")
            existing_end = existing.get("end_time", "23:59")
            new_start = slot.start_time
            new_end = slot.end_time
            
            # Simple time overlap check (in production, use proper datetime parsing)
            if not (new_end <= existing_start or new_start >= existing_end):
                raise HTTPException(
                    status_code=409,
                    detail=f"Time slot conflicts with existing booking in theater"
                )
    
    data = slot.model_dump()
    data["id"] = str(uuid.uuid4())
    data["status"] = slot.slot_type
    data["created_at"] = datetime.utcnow().isoformat()
    db.insert("ot_slots", data)
    return TimeSlotResponse(**data)


@router.get("/ot/slots/{slot_id}")
async def get_slot(slot_id: str, user=Depends(get_current_user)):
    """Get a specific time slot."""
    db = get_db()
    slot = db.get("ot_slots", slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Time slot not found")
    return TimeSlotResponse(**slot)


class TimeSlotUpdate(BaseModel):
    status: Optional[str] = None
    slot_type: Optional[str] = None
    notes: Optional[str] = None


@router.put("/ot/slots/{slot_id}")
async def update_slot(
    slot_id: str,
    updates: TimeSlotUpdate,
    user=Depends(require_role("admin", "surgeon"))
):
    """Update a time slot."""
    db = get_db()
    existing = db.get("ot_slots", slot_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Time slot not found")
    allowed = updates.model_dump(exclude_unset=True)
    if not allowed:
        return TimeSlotResponse(**existing)
    db.update("ot_slots", slot_id, allowed)
    return TimeSlotResponse(**db.get("ot_slots", slot_id))


@router.post("/ot/bookings")
async def create_booking(
    booking: BookingCreate,
    user=Depends(require_role("admin", "surgeon"))
):
    """Create a new booking for a time slot."""
    db = get_db()
    
    # Check if slot exists and is available
    slot = db.get("ot_slots", booking.slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Time slot not found")
    
    if slot.get("status") != "available":
        raise HTTPException(
            status_code=409,
            detail="Time slot is no longer available"
        )
    
    # Create booking
    booking_data = booking.model_dump()
    booking_data["id"] = str(uuid.uuid4())
    booking_data["status"] = "confirmed"
    booking_data["created_at"] = datetime.utcnow().isoformat()
    db.insert("ot_bookings", booking_data)
    
    # Update slot status
    db.update("ot_slots", booking.slot_id, {
        "status": "booked",
        "booked_by": user.get("full_name"),
        "patient_name": booking.patient_name,
        "procedure": booking.procedure
    })
    
    return BookingResponse(**booking_data)


@router.get("/ot/bookings")
async def list_bookings(
    date: Optional[str] = None,
    theater_id: Optional[str] = None,
    status: Optional[str] = None,
    user=Depends(get_current_user)
):
    """List bookings with optional filters."""
    db = get_db()
    bookings = db.get_all("ot_bookings")
    slots = db.get_all("ot_slots")
    
    # Filter bookings
    if date:
        # Get slots for that date and find their bookings
        date_slots = [s for s in slots if s.get("date") == date]
        slot_ids = [s["id"] for s in date_slots]
        bookings = [b for b in bookings if b.get("slot_id") in slot_ids]
    
    if theater_id:
        # Get slots for that theater and find their bookings
        theater_slots = [s for s in slots if s.get("theater_id") == theater_id]
        slot_ids = [s["id"] for s in theater_slots]
        bookings = [b for b in bookings if b.get("slot_id") in slot_ids]
    
    if status:
        bookings = [b for b in bookings if b.get("status") == status]
    
    # Enrich with slot info
    result = []
    for booking in bookings:
        slot = next((s for s in slots if s["id"] == booking.get("slot_id")), None)
        enriched = {
            **booking,
            "slot_date": slot.get("date") if slot else None,
            "slot_start_time": slot.get("start_time") if slot else None,
            "slot_end_time": slot.get("end_time") if slot else None,
            "theater_id": slot.get("theater_id") if slot else None,
        }
        result.append(enriched)
    
    return result


@router.get("/ot/bookings/{booking_id}")
async def get_booking(booking_id: str, user=Depends(get_current_user)):
    """Get a specific booking."""
    db = get_db()
    booking = db.get("ot_bookings", booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    slot = db.get("ot_slots", booking.get("slot_id"))
    return {
        **booking,
        "slot_date": slot.get("date") if slot else None,
        "slot_start_time": slot.get("start_time") if slot else None,
        "slot_end_time": slot.get("end_time") if slot else None,
        "theater_id": slot.get("theater_id") if slot else None,
    }


@router.put("/ot/bookings/{booking_id}")
async def update_booking(
    booking_id: str,
    updates: BookingUpdate,
    user=Depends(require_role("admin", "surgeon"))
):
    """Update a booking."""
    db = get_db()
    existing = db.get("ot_bookings", booking_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Booking not found")
    allowed = updates.model_dump(exclude_unset=True)
    if not allowed:
        return {**existing}
    db.update("ot_bookings", booking_id, allowed)
    
    # If status changed to cancelled, free up the slot
    if allowed.get("status") == "cancelled":
        slot = db.get("ot_slots", existing.get("slot_id"))
        if slot:
            db.update("ot_slots", existing.get("slot_id"), {
                "status": "available",
                "booked_by": None,
                "patient_name": None,
                "procedure": None
            })
    audit_logger.log("booking.updated", user.get("id"), "ot_booking", booking_id,
                     action="update", request=None)
    return {**db.get("ot_bookings", booking_id)}


@router.delete("/ot/bookings/{booking_id}")
async def cancel_booking(booking_id: str, user=Depends(require_role("admin", "surgeon"))):
    """Cancel a booking."""
    db = get_db()
    booking = db.get("ot_bookings", booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Free up the slot
    slot = db.get("ot_slots", booking.get("slot_id"))
    if slot:
        db.update("ot_slots", booking.get("slot_id"), {
            "status": "available",
            "booked_by": None,
            "patient_name": None,
            "procedure": None
        })
    
    db.delete("ot_bookings", booking_id)
    return {"message": "Booking cancelled successfully"}


@router.get("/ot/daily-schedule")
async def get_daily_schedule(
    date: str,
    user=Depends(get_current_user)
):
    """Get the complete daily schedule for a given date."""
    db = get_db()
    
    # Get all slots for the date
    slots = db.get_all("ot_slots")
    day_slots = [s for s in slots if s.get("date") == date]
    
    # Get all bookings
    bookings = db.get_all("ot_bookings")
    
    # Get theaters
    theaters = db.get_all("ot_theaters")
    theater_map = {t["id"]: t for t in theaters}
    
    # Build schedule grouped by theater
    schedule = {}
    for slot in day_slots:
        theater_id = slot.get("theater_id")
        theater = theater_map.get(theater_id, {})
        
        # Find booking for this slot
        booking = next((b for b in bookings if b.get("slot_id") == slot["id"]), None)
        
        if theater_id not in schedule:
            schedule[theater_id] = {
                "theater": TheaterResponse(**theater) if theater else {},
                "slots": []
            }
        
        schedule[theater_id]["slots"].append({
            "slot": TimeSlotResponse(**slot),
            "booking": BookingResponse(**booking) if booking else None
        })
    
    return schedule
