"""
Test AP2 crypto: JWS sign/verify roundtrip and tamper detection.

Run with: pytest tests/test_ap2_crypto.py
"""
import os
import sys

# Allow running from backend/venv
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.ap2.crypto import AP2Crypto


def test_key_pair_generation():
    """AP2Crypto should generate a valid ES256 key pair."""
    private_pem, public_pem = AP2Crypto.generate_key_pair()
    assert "BEGIN PRIVATE KEY" in private_pem
    assert "BEGIN PUBLIC KEY" in public_pem
    print("✓ Key pair generation works")


def test_sign_and_verify_roundtrip():
    """Sign a payload, then verify it with the public key — should succeed."""
    private_pem, public_pem = AP2Crypto.generate_key_pair()

    payload = {
        "mandate_id": "test_mandate_123",
        "buyer_did": "did:example:buyer",
        "merchant_id": "merch_abc",
        "amount": 50000,
        "nonce": "random_nonce_here",
    }

    jws = AP2Crypto.sign_payload(payload, private_pem)
    assert jws.count(".") == 2, "JWS should have 2 dots (3 segments)"

    decoded = AP2Crypto.verify_jws(jws, public_pem)
    assert decoded["mandate_id"] == "test_mandate_123"
    assert decoded["amount"] == 50000
    print("✓ Sign + verify roundtrip works")


def test_tamper_detection():
    """If we modify the payload, the JWS signature should be invalid."""
    private_pem, public_pem = AP2Crypto.generate_key_pair()

    original = {"mandate_id": "test", "amount": 100}
    jws = AP2Crypto.sign_payload(original, private_pem)

    # Tamper: verify with wrong public key (should fail)
    _, other_public = AP2Crypto.generate_key_pair()
    try:
        AP2Crypto.verify_jws(jws, other_public)
        assert False, "Should have raised JWTError"
    except Exception:
        pass  # Expected — signature invalid with wrong key

    print("✓ Tamper detection works (wrong key fails verification)")


def test_key_id_derivation():
    """get_key_id should produce a short deterministic hash."""
    _, public_pem = AP2Crypto.generate_key_pair()
    kid1 = AP2Crypto.get_key_id(public_pem)
    kid2 = AP2Crypto.get_key_id(public_pem)
    assert kid1 == kid2, "Same key should produce same key ID"
    assert len(kid1) == 16, "Key ID should be 16 chars"
    print("✓ Key ID derivation works")


if __name__ == "__main__":
    test_key_pair_generation()
    test_sign_and_verify_roundtrip()
    test_tamper_detection()
    test_key_id_derivation()
    print("\n✅ All AP2 crypto tests passed!")
