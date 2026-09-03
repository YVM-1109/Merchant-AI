"""
AP2 Protocol — JWS Cryptography Layer

Provides deterministic JWS signing and verification using ES256
(Elliptic Curve P-256 with SHA-256). This is the cryptographic
trust boundary for AP2-style mandates.

Usage:
  - Buyer generates an ES256 key pair, keeps the private key.
  - Buyer's DID resolves to the public key (JWK or PEM).
  - CartMandate payloads are JWS-signed by the buyer's private key.
  - Guardian verifies the JWS against the buyer's public key (from the IntentMandate).
"""
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError


class AP2Crypto:
    """Handles JWS signing and verification for AP2 mandates."""

    ALGORITHM = "ES256"

    @staticmethod
    def generate_key_pair() -> tuple[str, str]:
        """Generate an ES256 key pair for a buyer.

        Returns (private_pem, public_pem) as strings.
        In production these would be stored in a secure enclave / KMS.
        """
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import serialization

        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        return private_pem, public_pem

    @staticmethod
    def sign_payload(payload: dict, private_key_pem: str) -> str:
        """Sign a payload dict as a compact JWS (ES256).

        Args:
            payload: The JSON-LD mandate document to sign.
            private_key_pem: PEM-encoded EC private key.

        Returns:
            Compact JWS string: header.payload.signature
        """
        token = jwt.encode(
            payload,
            private_key_pem,
            algorithm=AP2Crypto.ALGORITHM,
        )
        return token

    @staticmethod
    def verify_jws(jws_string: str, public_key_pem: str) -> dict:
        """Verify a JWS token and return the decoded payload.

        Args:
            jws_string: Compact JWS token.
            public_key_pem: PEM-encoded EC public key.

        Returns:
            Decoded payload dict.

        Raises:
            JWTError: If the signature is invalid or the token is malformed.
        """
        try:
            payload = jwt.decode(
                jws_string,
                public_key_pem,
                algorithms=[AP2Crypto.ALGORITHM],
            )
            return payload
        except JWTError as exc:
            raise JWTError(f"JWS verification failed: {exc}") from exc

    @staticmethod
    def get_key_id(public_key_pem: str) -> str:
        """Derive a short key ID from a public key (hash of the PEM)."""
        import hashlib
        return hashlib.sha256(public_key_pem.encode()).hexdigest()[:16]
