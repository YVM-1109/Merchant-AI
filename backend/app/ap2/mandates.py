"""
AP2 Protocol — Mandate Creation and Validation

Implements Intent Mandate creation (signed by buyer) and Cart Mandate
signatures, plus scope validation logic used by the Guardian Agent.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from app.ap2.crypto import AP2Crypto
from app.ap2.schemas import AP2MandateDocument, AP2CartMandateDocument, MandateScopeJSONLD
from app.models import IntentMandate, MandateScope, CartMandate, CartItem


def create_intent_mandate(
    buyer_did: str,
    agent_did: str,
    merchant_id: str,
    max_amount_per_txn: int,
    max_amount_daily: int,
    allowed_categories: list[str],
    merchant_dids: list[str],
    duration_hours: int = 24,
    buyer_private_key_pem: str = "",
) -> IntentMandate:
    """Create and sign an Intent Mandate.

    The mandate is JWS-signed by the buyer's private key, then stored
    as a Beanie Document. The JSON-LD document is serialized into the
    mandate fields.
    """
    now = datetime.utcnow()
    expires_at = now + timedelta(hours=duration_hours)

    # Extract public key from private key if provided
    buyer_public_key = ""
    if buyer_private_key_pem:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec

        private_key = serialization.load_pem_private_key(
            buyer_private_key_pem.encode(), password=None
        )
        public_key = private_key.public_key()
        buyer_public_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

    # Build the JSON-LD document
    ld_doc = AP2MandateDocument(
        mandate_id=f"int_{uuid4().hex[:12]}",
        buyer_did=buyer_did,
        agent_did=agent_did,
        merchant_id=merchant_id,
        scope=MandateScopeJSONLD(
            max_amount_per_txn=max_amount_per_txn,
            max_amount_daily=max_amount_daily,
            allowed_categories=allowed_categories,
            merchant_dids=merchant_dids,
            time_window_start=now.isoformat() + "Z",
            time_window_end=expires_at.isoformat() + "Z",
        ),
        buyer_public_key=buyer_public_key,
        created_at=now.isoformat() + "Z",
        expires_at=expires_at.isoformat() + "Z",
        nonce=uuid4().hex,
    )

    # Sign the payload
    payload_dict = ld_doc.model_dump()
    signature = AP2Crypto.sign_payload(payload_dict, buyer_private_key_pem) if buyer_private_key_pem else ""

    # Create the Beanie Document
    mandate = IntentMandate(
        mandate_id=ld_doc.mandate_id,
        buyer_did=buyer_did,
        agent_did=agent_did,
        merchant_id=merchant_id,
        scope=MandateScope(
            max_amount_per_txn=max_amount_per_txn,
            max_amount_daily=max_amount_daily,
            allowed_categories=allowed_categories,
            merchant_dids=merchant_dids,
            time_window_start=now,
            time_window_end=expires_at,
        ),
        buyer_public_key=buyer_public_key,
        mandate_signature=signature,
        created_at=now,
        expires_at=expires_at,
    )
    return mandate


def sign_cart_mandate(
    intent_mandate_id: str,
    merchant_id: str,
    cart_items: list[CartItem],
    total_amount: int,
    currency: str,
    buyer_private_key_pem: str,
) -> tuple[str, str]:
    """Create a Cart Mandate document and sign it with the buyer's key.

    Returns (cart_mandate_id, jws_signature).
    """
    now = datetime.utcnow()
    nonce = uuid4().hex

    ld_doc = AP2CartMandateDocument(
        mandate_id=f"cart_{uuid4().hex[:12]}",
        intent_mandate_id=intent_mandate_id,
        merchant_id=merchant_id,
        cart_items=[item.model_dump() for item in cart_items],
        total_amount=total_amount,
        currency=currency,
        nonce=nonce,
        created_at=now.isoformat() + "Z",
    )

    payload_dict = ld_doc.model_dump()
    signature = AP2Crypto.sign_payload(payload_dict, buyer_private_key_pem)

    return ld_doc.mandate_id, signature


def validate_intent_mandate(
    mandate: IntentMandate,
    buyer_public_key_pem: str,
) -> bool:
    """Verify the JWS signature on an Intent Mandate.

    Returns True if the signature is valid, False otherwise.
    """
    if not mandate.mandate_signature:
        return False

    try:
        AP2Crypto.verify_jws(mandate.mandate_signature, buyer_public_key_pem)
        return True
    except Exception:
        return False
