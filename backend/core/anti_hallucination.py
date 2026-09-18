"""
NEURO_PREDICT_SYS — Anti-Hallucination & Input Validation
Prevents the ML system from producing unreliable outputs and validates all inputs.
"""
import re
from typing import Any, Dict, List, Optional, Tuple
from .config import get_settings

settings = get_settings()


# ── Input Validators ──────────────────────────────────────────────

class InputValidator:
    """Validates and sanitizes all user inputs before they reach ML models."""

    @staticmethod
    def validate_symptoms(symptoms: List[str]) -> Tuple[List[str], List[str]]:
        """Validate symptoms against known list. Returns (valid, rejected)."""
        if not symptoms:
            return [], []
        valid = []
        rejected = []
        for s in symptoms:
            s_clean = s.strip().lower().replace(" ", "_").replace("-", "_")
            if s_clean in settings.ALLOWED_SYMPROMS:
                valid.append(s_clean)
            else:
                rejected.append(s)
        return valid, rejected

    @staticmethod
    def validate_clinical_data(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """Validate clinical data ranges. Returns (cleaned_data, warnings)."""
        warnings = []
        cleaned = {}

        RANGES = {
            "age": (0, 150),
            "cognitive_score": (0, 30),
            "mmse_score": (0, 30),
            "eeg_alpha_power": (0, 100),
            "eeg_beta_power": (0, 100),
            "eeg_delta_power": (0, 100),
            "eeg_theta_power": (0, 100),
            "mri_hippocampal_volume": (0, 10),
            "mri_ventricle_volume": (0, 200),
            "mri_cortical_thickness": (0, 5),
            "csf_abeta": (0, 2000),
            "csf_tau": (0, 2000),
            "csf_ptau": (0, 500),
            "gait_speed": (0, 3),
            "speech_clarity": (0, 100),
            "fdg_pet_uptake": (0, 5),
        }

        for key, value in data.items():
            if key in RANGES:
                low, high = RANGES[key]
                try:
                    v = float(value)
                    if v < low or v > high:
                        warnings.append(f"{key}={v} outside expected range [{low}, {high}]")
                        cleaned[key] = max(low, min(high, v))  # Clamp
                    else:
                        cleaned[key] = v
                except (ValueError, TypeError):
                    warnings.append(f"{key} has invalid numeric value")
            else:
                cleaned[key] = value

        return cleaned, warnings

    @staticmethod
    def validate_patient_id(patient_id: str) -> bool:
        """Validate patient ID format (UUID or MRN pattern)."""
        if not patient_id:
            return False
        # UUID format
        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        if re.match(uuid_pattern, patient_id, re.I):
            return True
        # MRN format
        mrn_pattern = r"^MRN-\d{4}-\d{3}$"
        if re.match(mrn_pattern, patient_id):
            return True
        return False

    @staticmethod
    def sanitize_text(text: str, max_length: int = 5000) -> str:
        """Sanitize free-text input (medical history, notes)."""
        if not text:
            return ""
        # Remove potential injection patterns
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.I | re.S)
        text = re.sub(r"javascript:", "", text, flags=re.I)
        text = re.sub(r"on\w+\s*=", "", text, flags=re.I)
        # Truncate
        return text[:max_length].strip()


# ── Hallucination Detector ────────────────────────────────────────

class HallucinationDetector:
    """
    Checks ML model outputs for signs of hallucination or unreliable results.
    Returns a confidence score and list of concerns.
    """

    # Diseases the model actually supports
    SUPPORTED_DISEASES = {
        "alzheimer's disease", "parkinson's disease", "als",
        "huntington's disease", "epilepsy", "multiple sclerosis",
        "migraine", "brain tumor",
    }

    @staticmethod
    def check_prediction(result: Dict) -> Dict:
        """Run hallucination checks on a prediction result."""
        concerns = []
        confidence_modifier = 0.0

        predictions = result.get("predictions", [])
        if not predictions:
            concerns.append("No predictions generated")
            return {"safe": False, "confidence_modifier": -0.5, "concerns": concerns}

        for pred in predictions:
            disease = pred.get("disease", "").lower()
            confidence = pred.get("confidence", 0)

            # Check 1: Is this a disease the model was trained on?
            if disease not in HallucinationDetector.SUPPORTED_DISEASES:
                concerns.append(f"Unknown disease '{pred.get('disease')}' — model not trained on this")
                confidence_modifier -= 0.3

            # Check 2: Suspiciously high confidence (>99%)
            if confidence > 0.99:
                concerns.append(f"Unusually high confidence ({confidence:.1%}) for {pred.get('disease')}")
                confidence_modifier -= 0.1

            # Check 3: Multiple high-confidence predictions (conflicting)
            high_conf = [p for p in predictions if p.get("confidence", 0) > 0.7]
            if len(high_conf) > 2:
                concerns.append(f"{len(high_conf)} diseases with >70% confidence — results may be conflicting")
                confidence_modifier -= 0.15

            # Check 4: Contributing factors missing
            factors = pred.get("contributing_factors", [])
            if confidence > 0.6 and len(factors) == 0:
                concerns.append("High confidence prediction with no contributing factors")
                confidence_modifier -= 0.05

        # Check 5: AI confidence vs actual prediction agreement
        ai_confidence = result.get("ai_confidence", 0)
        top_confidence = predictions[0].get("confidence", 0) if predictions else 0
        if ai_confidence > 0.9 and top_confidence < 0.5:
            concerns.append("Model reports high AI confidence but top prediction is weak")
            confidence_modifier -= 0.2

        # Check 6: Brain region consistency
        brain_regions = result.get("brain_regions", {})
        if brain_regions:
            impaired = [r for r, v in brain_regions.items() if v.get("status") not in ("normal",)]
            if len(impaired) == 0 and top_confidence > 0.7:
                concerns.append("High disease confidence but no brain region abnormalities detected")
                confidence_modifier -= 0.1

        safe = len(concerns) == 0 or (len(concerns) <= 1 and confidence_modifier > -0.2)

        return {
            "safe": safe,
            "confidence_modifier": round(max(confidence_modifier, -0.5), 2),
            "concerns": concerns,
            "recommendation": _get_recommendation(concerns, confidence_modifier),
        }

    @staticmethod
    def check_eeg_result(result: Dict) -> Dict:
        """Check EEG analysis for hallucination signs."""
        concerns = []

        signature = result.get("signature_match", {})
        if signature:
            total = sum(signature.values())
            if total > 100:
                concerns.append("Signature match percentages exceed 100% total")
            if any(v > 90 for v in signature.values()):
                concerns.append("Extremely high signature match — may be overfitting")

        quality = result.get("quality_score", 0)
        if quality < 0.5:
            concerns.append(f"Low data quality score ({quality:.0%}) — results may be unreliable")

        return {
            "safe": len(concerns) == 0,
            "concerns": concerns,
        }


def _get_recommendation(concerns: List[str], modifier: float) -> str:
    if not concerns:
        return "Results appear reliable. Proceed with clinical review."
    if modifier < -0.3:
        return "WARNING: Multiple reliability concerns detected. Recommend re-analysis with additional clinical data."
    if modifier < -0.15:
        return "CAUTION: Some concerns detected. Cross-reference with additional diagnostic tests."
    return "Minor concerns noted. Results should be reviewed by a specialist."


# ── Proxy Input Shield ────────────────────────────────────────────

class ProxyInputShield:
    """
    Detects and blocks prompt injection / proxy attacks on the ML pipeline.
    Checks for adversarial inputs designed to manipulate model outputs.
    """

    ATTACK_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"you\s+are\s+now\s+",
        r"act\s+as\s+if",
        r"pretend\s+you\s+are",
        r"system\s*:\s*",
        r"<\|im_start\|>",
        r"<\|im_end\|>",
        r"\[INST\]",
        r"\[/INST\]",
        r"###\s*(system|human|assistant)",
        r"ADMIN\s*:\s*",
        r"OVERRIDE\s*:",
    ]

    @staticmethod
    def scan(text: str) -> Dict:
        """Scan input text for injection patterns."""
        if not text:
            return {"safe": True, "attacks": []}

        attacks = []
        text_lower = text.lower()

        for pattern in ProxyInputShield.ATTACK_PATTERNS:
            if re.search(pattern, text_lower):
                attacks.append(f"Prompt injection pattern detected: {pattern[:30]}...")

        # Check for excessive length (DoS)
        if len(text) > settings.MAX_INPUT_LENGTH:
            attacks.append(f"Input exceeds max length ({len(text)} > {settings.MAX_INPUT_LENGTH})")

        # Check for binary/non-text content
        try:
            text.encode("utf-8")
        except UnicodeEncodeError:
            attacks.append("Non-UTF-8 content detected")

        return {
            "safe": len(attacks) == 0,
            "attacks": attacks,
            "blocked": len(attacks) > 0,
        }


# ── Singletons ────────────────────────────────────────────────────
validator = InputValidator()
hallucination_detector = HallucinationDetector()
proxy_shield = ProxyInputShield()
