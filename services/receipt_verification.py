"""
Jobper Services — Receipt Verification with OpenAI Vision
Verifies payment receipts using AI to prevent fraud.
"""
from __future__ import annotations

import base64
import hashlib
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import NamedTuple

from config import Config
from core.cache import cache
from core.database import UnitOfWork, Payment

logger = logging.getLogger(__name__)


# =============================================================================
# VERIFICATION RESULT
# =============================================================================

class VerificationResult(NamedTuple):
    """Result of receipt verification."""
    is_valid: bool
    confidence: float  # 0.0 to 1.0
    extracted_amount: int | None
    extracted_reference: str | None
    extracted_date: str | None
    extracted_destination: str | None
    issues: list[str]
    requires_manual_review: bool
    raw_analysis: dict


# =============================================================================
# REFERENCE CODE GENERATION
# =============================================================================

def generate_payment_reference(user_id: int, plan: str, amount: int) -> str:
    """
    Generate a unique, verifiable reference code for payment.
    Format: JOB-{user_id}-{plan_code}-{amount_hash}-{timestamp_hash}
    Example: JOB-123-CAZ-A5B2-7X9K
    """
    plan_codes = {
        "cazador": "CAZ",
        "competidor": "COM",
        "dominador": "DOM",
    }
    plan_code = plan_codes.get(plan, "XXX")

    # Create deterministic but hard-to-guess hash
    timestamp = int(datetime.utcnow().timestamp())
    raw = f"{user_id}-{plan}-{amount}-{timestamp}-{Config.JWT_SECRET[:8]}"
    hash_bytes = hashlib.sha256(raw.encode()).digest()

    # Take 4 chars for amount hash, 4 for timestamp hash
    amount_hash = base64.b32encode(hash_bytes[:3]).decode()[:4].upper()
    time_hash = base64.b32encode(hash_bytes[3:6]).decode()[:4].upper()

    return f"JOB-{user_id}-{plan_code}-{amount_hash}-{time_hash}"


def parse_reference(reference: str) -> dict | None:
    """
    Parse a payment reference to extract components.
    Returns None if invalid format.
    """
    pattern = r"^JOB-(\d+)-(CAZ|COM|DOM)-([A-Z0-9]{4})-([A-Z0-9]{4})$"
    match = re.match(pattern, reference)
    if not match:
        return None

    plan_map = {"CAZ": "cazador", "COM": "competidor", "DOM": "dominador"}
    return {
        "user_id": int(match.group(1)),
        "plan": plan_map.get(match.group(2), "unknown"),
        "amount_hash": match.group(3),
        "time_hash": match.group(4),
    }


# =============================================================================
# DUPLICATE DETECTION
# =============================================================================

def compute_image_hash(image_bytes: bytes) -> str:
    """Compute a perceptual hash of the image for duplicate detection."""
    # Simple SHA256 hash of image content
    # In production, could use perceptual hashing (pHash) for similar images
    return hashlib.sha256(image_bytes).hexdigest()


def check_duplicate_receipt(image_hash: str, user_id: int) -> dict | None:
    """
    Check if this receipt has been used before.
    Returns the previous payment info if duplicate, None if new.
    """
    with UnitOfWork() as uow:
        # Check in database for same hash
        existing = (
            uow.session.query(Payment)
            .filter(
                Payment.comprobante_hash == image_hash,
                Payment.status == "approved",
            )
            .first()
        )
        if existing:
            return {
                "payment_id": existing.id,
                "user_id": existing.user_id,
                "created_at": existing.created_at.isoformat() if existing.created_at else None,
                "same_user": existing.user_id == user_id,
            }
    return None


# =============================================================================
# OPENAI VISION VERIFICATION
# =============================================================================

def verify_receipt_with_ai(
    image_path: str | Path,
    expected_amount: int,
    expected_reference: str,
    expected_destination: str,
) -> VerificationResult:
    """
    Verify a payment receipt using OpenAI Vision API.

    Args:
        image_path: Path to the receipt image
        expected_amount: Expected payment amount in COP
        expected_reference: Expected reference code (e.g., JOB-123-CAZ-A5B2-7X9K)
        expected_destination: Expected destination (Nequi number or Bancolombia account)

    Returns:
        VerificationResult with validation details
    """
    import openai

    # Read and encode image
    image_path = Path(image_path)
    if not image_path.exists():
        return VerificationResult(
            is_valid=False,
            confidence=0.0,
            extracted_amount=None,
            extracted_reference=None,
            extracted_date=None,
            extracted_destination=None,
            issues=["Imagen no encontrada"],
            requires_manual_review=False,
            raw_analysis={},
        )

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    # Determine image type
    if image_path.suffix.lower() in [".jpg", ".jpeg"]:
        media_type = "image/jpeg"
    elif image_path.suffix.lower() == ".png":
        media_type = "image/png"
    elif image_path.suffix.lower() == ".webp":
        media_type = "image/webp"
    else:
        media_type = "image/jpeg"

    # Format expected amount for display
    expected_amount_display = f"${expected_amount:,.0f}".replace(",", ".")

    # Get current date for time validation
    from datetime import datetime
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Build the prompt
    prompt = f"""Analiza esta imagen de un comprobante de pago colombiano.

FECHA ACTUAL: {today}

DATOS ESPERADOS:
- Monto: {expected_amount_display} COP (o {expected_amount} sin formato)
- Referencia: {expected_reference}
- Destino: {expected_destination}

EXTRAE Y VERIFICA (SÉ MUY ESTRICTO):
1. ¿Es un comprobante de pago REAL de Nequi, Bancolombia, Daviplata u otro banco colombiano?
2. ¿El monto EXACTO coincide con {expected_amount_display}?
3. ¿La referencia "{expected_reference}" aparece EXACTAMENTE en el comprobante?
4. ¿El destino (número Nequi o cuenta) coincide con "{expected_destination}"?
5. ¿La fecha es de HOY o AYER? (máximo 24 horas de antigüedad)
6. ¿El comprobante parece AUTÉNTICO? (busca signos de edición, Photoshop, inconsistencias)

SEÑALES DE FRAUDE:
- Tipografía inconsistente o diferente al estilo de Nequi/Bancolombia
- Bordes irregulares o pixelados alrededor de texto
- Fechas muy antiguas (más de 24h)
- Referencia que no coincide exactamente
- Monto diferente al esperado
- Foto de una foto o screenshot de screenshot

RESPONDE EN ESTE FORMATO JSON EXACTO:
{{
    "is_payment_receipt": true/false,
    "bank_or_app": "Nequi/Bancolombia/Daviplata/Otro/No identificado",
    "extracted_amount": número o null,
    "amount_matches": true/false,
    "extracted_reference": "texto encontrado" o null,
    "reference_matches": true/false,
    "extracted_destination": "número o cuenta encontrada" o null,
    "destination_matches": true/false,
    "transaction_date": "YYYY-MM-DD HH:MM" o null,
    "date_is_recent": true/false (true SOLO si es de las últimas 24 horas),
    "appears_authentic": true/false,
    "fraud_indicators": ["lista de señales sospechosas si las hay"],
    "confidence": 0.0 a 1.0,
    "issues": ["lista de problemas encontrados"],
    "notes": "observaciones adicionales"
}}

SÉ MUY ESTRICTO. Es mejor rechazar un pago legítimo que aprobar uno falso.
Si tienes CUALQUIER duda, indica confianza menor a 0.9.
"""

    try:
        client = openai.OpenAI()

        response = client.chat.completions.create(
            model="gpt-4o",  # Vision model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_base64}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            ],
            max_tokens=1000,
            temperature=0.1,  # Low temperature for consistent analysis
        )

        # Parse response
        content = response.choices[0].message.content

        # Extract JSON from response
        import json

        # Try to find JSON in the response
        json_match = re.search(r'\{[\s\S]*\}', content)
        if not json_match:
            logger.warning(f"No JSON found in OpenAI response: {content[:200]}")
            return VerificationResult(
                is_valid=False,
                confidence=0.0,
                extracted_amount=None,
                extracted_reference=None,
                extracted_date=None,
                extracted_destination=None,
                issues=["No se pudo analizar la imagen"],
                requires_manual_review=True,
                raw_analysis={"raw_response": content},
            )

        analysis = json.loads(json_match.group())

        # Determine validity
        issues = analysis.get("issues", [])

        # Critical checks
        if not analysis.get("is_payment_receipt", False):
            issues.append("No es un comprobante de pago")

        if not analysis.get("amount_matches", False):
            extracted = analysis.get("extracted_amount")
            if extracted:
                issues.append(f"Monto incorrecto: esperado {expected_amount_display}, encontrado ${extracted:,.0f}".replace(",", "."))
            else:
                issues.append("No se pudo leer el monto")

        if not analysis.get("reference_matches", False):
            extracted_ref = analysis.get("extracted_reference")
            if extracted_ref:
                issues.append(f"Referencia no coincide: esperado '{expected_reference}'")
            else:
                issues.append("No se encontró la referencia en el comprobante")

        if not analysis.get("destination_matches", False):
            issues.append("El destino del pago no coincide")

        if not analysis.get("appears_authentic", True):
            issues.append("El comprobante parece modificado o no auténtico")

        if not analysis.get("date_is_recent", True):
            issues.append("La fecha del comprobante no es reciente")

        # Determine if valid
        confidence = analysis.get("confidence", 0.0)

        # STRICT: Require 85%+ confidence AND all checks passing
        is_valid = (
            analysis.get("is_payment_receipt", False) and
            analysis.get("amount_matches", False) and
            analysis.get("reference_matches", False) and
            analysis.get("destination_matches", False) and  # Added: must match destination
            analysis.get("appears_authentic", True) and
            analysis.get("date_is_recent", True) and  # Added: must be recent
            confidence >= 0.85  # Raised from 0.7
        )

        # Require manual review if borderline (40-85% confidence)
        requires_manual_review = (
            not is_valid and
            confidence >= 0.4 and
            analysis.get("is_payment_receipt", False)
        )

        return VerificationResult(
            is_valid=is_valid,
            confidence=confidence,
            extracted_amount=analysis.get("extracted_amount"),
            extracted_reference=analysis.get("extracted_reference"),
            extracted_date=analysis.get("transaction_date"),
            extracted_destination=analysis.get("extracted_destination"),
            issues=issues,
            requires_manual_review=requires_manual_review,
            raw_analysis=analysis,
        )

    except openai.APIError as e:
        logger.error(f"OpenAI API error during receipt verification: {e}")
        return VerificationResult(
            is_valid=False,
            confidence=0.0,
            extracted_amount=None,
            extracted_reference=None,
            extracted_date=None,
            extracted_destination=None,
            issues=["Error al analizar la imagen con IA"],
            requires_manual_review=True,
            raw_analysis={"error": str(e)},
        )
    except Exception as e:
        logger.error(f"Unexpected error during receipt verification: {e}")
        return VerificationResult(
            is_valid=False,
            confidence=0.0,
            extracted_amount=None,
            extracted_reference=None,
            extracted_date=None,
            extracted_destination=None,
            issues=["Error inesperado al verificar el comprobante"],
            requires_manual_review=True,
            raw_analysis={"error": str(e)},
        )


# =============================================================================
# MAIN VERIFICATION FUNCTION
# =============================================================================

def verify_payment_receipt(
    user_id: int,
    payment_id: int,
    image_path: str | Path,
) -> dict:
    """
    Full verification pipeline for a payment receipt.

    Returns:
        {
            "valid": bool,
            "auto_approved": bool,
            "requires_review": bool,
            "issues": [...],
            "verification": {...},
        }
    """
    image_path = Path(image_path)

    # 1. Get payment details
    with UnitOfWork() as uow:
        payment = uow.payments.get(payment_id)
        if not payment:
            return {"valid": False, "issues": ["Pago no encontrado"], "auto_approved": False}
        if payment.user_id != user_id:
            return {"valid": False, "issues": ["Pago no pertenece a este usuario"], "auto_approved": False}
        if payment.status != "pending":
            return {"valid": False, "issues": ["Este pago ya fue procesado"], "auto_approved": False}

        expected_amount = payment.amount
        expected_reference = payment.wompi_ref  # We use this field for reference
        plan = payment.metadata_json.get("plan")

    # 2. Check for duplicate receipt
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    image_hash = compute_image_hash(image_bytes)

    duplicate = check_duplicate_receipt(image_hash, user_id)
    if duplicate:
        if duplicate["same_user"]:
            return {
                "valid": False,
                "auto_approved": False,
                "requires_review": False,
                "issues": ["Ya usaste este comprobante anteriormente"],
                "verification": {"duplicate": True, "previous_payment": duplicate["payment_id"]},
            }
        else:
            # Different user used this receipt - fraud attempt
            logger.warning(f"FRAUD ALERT: Receipt reuse detected! User {user_id} tried to use receipt from user {duplicate['user_id']}")
            return {
                "valid": False,
                "auto_approved": False,
                "requires_review": True,
                "issues": ["Este comprobante ya fue utilizado por otra cuenta"],
                "verification": {"fraud_suspected": True},
            }

    # 3. Determine expected destination
    # Check which payment method they're likely using based on reference
    if Config.NEQUI_NUMBER:
        expected_destination = Config.NEQUI_NUMBER
    elif Config.BANCOLOMBIA_ACCOUNT:
        expected_destination = Config.BANCOLOMBIA_ACCOUNT
    else:
        expected_destination = "cuenta de Jobper"

    # 4. Verify with AI
    verification = verify_receipt_with_ai(
        image_path=image_path,
        expected_amount=expected_amount,
        expected_reference=expected_reference,
        expected_destination=expected_destination,
    )

    # 5. Store hash for future duplicate detection
    if verification.is_valid or verification.requires_manual_review:
        with UnitOfWork() as uow:
            payment = uow.payments.get(payment_id)
            if payment:
                payment.comprobante_hash = image_hash
                payment.verification_result = {
                    "confidence": verification.confidence,
                    "issues": verification.issues,
                    "extracted_amount": verification.extracted_amount,
                    "extracted_reference": verification.extracted_reference,
                    "extracted_date": verification.extracted_date,
                }
                uow.commit()

    return {
        "valid": verification.is_valid,
        # STRICT: Only auto-approve with 95%+ confidence
        "auto_approved": verification.is_valid and verification.confidence >= 0.95,
        "requires_review": verification.requires_manual_review or (verification.is_valid and verification.confidence < 0.95),
        "issues": verification.issues,
        "verification": {
            "confidence": verification.confidence,
            "extracted_amount": verification.extracted_amount,
            "extracted_reference": verification.extracted_reference,
            "extracted_date": verification.extracted_date,
        },
    }
