"""Military-grade Cryptographic Agility with Post-Quantum support."""

import hashlib
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

try:
    import oqs
    OQS_AVAILABLE = True
except ImportError:
    OQS_AVAILABLE = False

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, ec, x25519, x448
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class PQCAlgorithm(Enum):
    """NIST PQC Standard algorithms."""
    # KEMs
    ML_KEM_512 = "ML-KEM-512"
    ML_KEM_768 = "ML-KEM-768"
    ML_KEM_1024 = "ML-KEM-1024"
    # Signatures
    ML_DSA_44 = "ML-DSA-44"
    ML_DSA_65 = "ML-DSA-65"
    ML_DSA_87 = "ML-DSA-87"
    SLH_DSA_SHA2_128S = "SLH-DSA-SHA2-128s"
    SLH_DSA_SHA2_192F = "SLH-DSA-SHA2-192f"
    SLH_DSA_SHA2_256S = "SLH-DSA-SHA2-256s"

    # Hybrid (Classical + PQ)
    X25519_ML_KEM_768 = "X25519MLKEM768"
    ECDH_P256_ML_KEM_768 = "ECDH_P256_ML_KEM_768"
    ED25519_ML_DSA_65 = "ED25519_ML_DSA_65"


@dataclass
class PQCKeyPair:
    algorithm: PQCAlgorithm
    public_key: bytes
    private_key: bytes
    metadata: dict = field(default_factory=dict)


@dataclass
class HybridKEMResult:
    classical_shared_secret: bytes
    pq_shared_secret: bytes
    combined_secret: bytes
    classical_public_key: bytes
    pq_public_key: bytes
    classical_ciphertext: bytes
    pq_ciphertext: bytes


class PQCKeyManager:
    """Post-Quantum Cryptography key management with hybrid support."""

    def __init__(self):
        self.keys: dict[str, PQCKeyPair] = {}

    def generate_keypair(self, algorithm: PQCAlgorithm, key_id: str = None) -> PQCKeyPair:
        if not OQS_AVAILABLE:
            raise RuntimeError("liboqs not available. Install liboqs and python-oqs.")

        oqs_alg = self._map_algorithm(algorithm)
        kem = oqs.KeyEncapsulation(oqs_alg)
        public_key = kem.generate_keypair()
        private_key = kem.export_secret_key()

        key_id = key_id or f"{algorithm.value}_{hashlib.sha256(public_key).hexdigest()[:8]}"
        keypair = PQCKeyPair(
            algorithm=algorithm,
            public_key=public_key,
            private_key=private_key,
            metadata={"algorithm": algorithm.value, "oqs_alg": oqs_alg}
        )
        self.keys[key_id] = keypair
        return self.keys[key_id]

    def _map_algorithm(self, alg: PQCAlgorithm) -> str:
        mapping = {
            PQCAlgorithm.ML_KEM_512: "Kyber512",
            PQCAlgorithm.ML_KEM_768: "Kyber768",
            PQCAlgorithm.ML_KEM_1024: "Kyber1024",
            PQCAlgorithm.ML_DSA_44: "Dilithium2",
            PQCAlgorithm.ML_DSA_65: "Dilithium3",
            PQCAlgorithm.ML_DSA_87: "Dilithium5",
            PQCAlgorithm.SLH_DSA_SHA2_128S: "SPHINCS+-SHA2-128s",
            PQCAlgorithm.SLH_DSA_SHA2_192F: "SPHINCS+-SHA2-192f",
            PQCAlgorithm.SLH_DSA_SHA2_256S: "SPHINCS+-SHA2-256s",
        }
        return mapping.get(alg, "Kyber768")

    def encapsulate(self, key_id: str) -> tuple[bytes, bytes]:
        if key_id not in self.keys:
            raise KeyError(f"Key {key_id} not found")
        keypair = self.keys[key_id]
        kem = oqs.KeyEncapsulation(self._map_algorithm(keypair.algorithm))
        kem.import_public_key(keypair.public_key)
        ciphertext, shared_secret = kem.encap_secret(keypair.public_key)
        return ciphertext, shared_secret

    def decapsulate(self, key_id: str, ciphertext: bytes) -> bytes:
        if key_id not in self.keys:
            raise KeyError(f"Key {key_id} not found")
        keypair = self.keys[key_id]
        kem = oqs.KeyEncapsulation(self._map_algorithm(keypair.algorithm))
        kem.import_private_key(keypair.private_key)
        return kem.decap_secret(ciphertext)


class HybridKeyManager:
    """Hybrid Classical + PQC key management for crypto agility."""

    def __init__(self):
        self.classical_keys: dict[str, any] = {}
        self.pqc_keys: dict[str, PQCKeyPair] = {}

    def generate_hybrid_keypair(self, classical_alg: str = "X25519",
                                pqc_alg: PQCAlgorithm = PQCAlgorithm.ML_KEM_768,
                                key_id: str = None) -> dict:
        key_id = key_id or f"hybrid_{classical_alg}_{pqc_alg.value}"

        # Classical key
        if classical_alg == "X25519":
            from cryptography.hazmat.primitives.asymmetric import x25519
            classical_private = x25519.X25519PrivateKey.generate()
            classical_public = classical_private.public_key()
            classical_pub_bytes = classical_public.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            classical_priv_bytes = classical_private.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            )
        elif classical_alg == "ECDH_P256":
            from cryptography.hazmat.primitives.asymmetric import ec
            classical_private = ec.generate_private_key(ec.SECP256R1())
            classical_public = classical_private.public_key()
            classical_pub_bytes = classical_public.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            classical_priv_bytes = classical_private.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            )
        else:
            raise ValueError(f"Unsupported classical algorithm: {classical_alg}")

        # PQC key
        pqc_key = PQCKeyManager().generate_keypair(pqc_alg, key_id + "_pqc")

        key_id = key_id or f"hybrid_{classical_alg}_{pqc_alg.value}"
        self.classical_keys[key_id] = {
            "public": classical_pub_bytes,
            "private": classical_priv_bytes,
            "algorithm": classical_alg
        }
        self.pqc_keys[key_id] = pqc_key

        return {
            "key_id": key_id,
            "classical_alg": classical_alg,
            "pqc_alg": pqc_alg.value,
            "classical_public": classical_pub_bytes,
            "pqc_public": pqc_key.public_key
        }

    def hybrid_kem_encapsulate(self, key_id: str, peer_classical_pub: bytes,
                               peer_pqc_pub: bytes) -> HybridKEMResult:
        if key_id not in self.classical_keys or key_id not in self.pqc_keys:
            raise KeyError(f"Hybrid key {key_id} not found")

        classical_priv = self.classical_keys[key_id]["private"]
        pqc_keypair = self.pqc_keys[key_id]

        # Classical KEM (X25519/ECDH)
        from cryptography.hazmat.primitives.asymmetric import x25519
        our_private = x25519.X25519PrivateKey.from_private_bytes(self.classical_keys[key_id]["private"])
        peer_public = x25519.X25519PublicKey.from_public_bytes(peer_classical_pub)
        classical_shared = our_private.exchange(peer_public)

        # PQC KEM
        pqc_keypair = self.pqc_keys[key_id]
        kem = oqs.KeyEncapsulation(self._map_algorithm(pqc_keypair.algorithm))
        kem.import_public_key(peer_pqc_pub)
        pq_ciphertext, pq_shared = kem.encap_secret(peer_pqc_pub)

        # Combine secrets using HKDF
        combined = classical_shared + pq_shared
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=64,
            salt=None,
            info=b"rtai-hybrid-kem-v1"
        )
        combined_secret = hkdf.derive(combined)

        return HybridKEMResult(
            classical_shared_secret=classical_shared,
            pq_shared_secret=pq_shared,
            combined_secret=combined_secret,
            classical_public_key=self.classical_keys[key_id]["public"],
            pq_public_key=self.pqc_keys[key_id].public_key,
            classical_ciphertext=b"",
            pq_ciphertext=b""
        )

    def _map_algorithm(self, alg: PQCAlgorithm) -> str:
        mapping = {
            PQCAlgorithm.ML_KEM_512: "Kyber512",
            PQCAlgorithm.ML_KEM_768: "Kyber768",
            PQCAlgorithm.ML_KEM_1024: "Kyber1024",
            PQCAlgorithm.ML_DSA_44: "Dilithium2",
            PQCAlgorithm.ML_DSA_65: "Dilithium3",
            PQCAlgorithm.ML_DSA_87: "Dilithium5",
        }
        return mapping.get(alg, "Kyber768")


class PostQuantumSigner:
    """Post-Quantum digital signatures with hybrid support."""

    def __init__(self):
        self.signers: dict[str, any] = {}

    def sign(self, key_id: str, message: bytes) -> bytes:
        if key_id not in self.signers:
            raise KeyError(f"Signer {key_id} not found")
        signer = self.signers[key_id]
        return signer.sign(message)

    def verify(self, key_id: str, message: bytes, signature: bytes) -> bool:
        if key_id not in self.signers:
            raise KeyError(f"Verifier {key_id} not found")
        verifier = self.signers[key_id]
        try:
            verifier.verify(signature, message)
            return True
        except Exception:
            return False


class CryptoAgilityManager:
    """Cryptographic agility manager for algorithm migration."""

    def __init__(self):
        self.algorithms: dict[str, dict] = {}
        self.active_algorithm: str = "hybrid_x25519_ml_kem_768"

    def register_algorithm(self, name: str, config: dict):
        self.algorithms[name] = config

    def get_active_suite(self) -> dict:
        return self.algorithms.get(self.active_algorithm, {})

    def migrate_to(self, algorithm: str) -> bool:
        if algorithm in self.algorithms:
            self.active_algorithm = algorithm
            return True
        return False

    def get_supported_algorithms(self) -> list[str]:
        return list(self.algorithms.keys())


# Convenience functions
def generate_pqc_keypair(algorithm: PQCAlgorithm = PQCAlgorithm.ML_KEM_768) -> PQCKeyPair:
    return PQCKeyManager().generate_keypair(algorithm)


def create_hybrid_keypair(classical: str = "X25519", pqc: PQCAlgorithm = PQCAlgorithm.ML_KEM_768) -> dict:
    return HybridKeyManager().generate_hybrid_keypair(classical, pqc)


def hybrid_encapsulate(key_id: str, peer_classical_pub: bytes, peer_pqc_pub: bytes) -> HybridKEMResult:
    return HybridKeyManager().hybrid_kem_encapsulate(key_id, peer_classical_pub, peer_pqc_pub)


# Export
__all__ = [
    "PQCAlgorithm",
    "PQCKeyPair",
    "HybridKEMResult",
    "PQCKeyManager",
    "HybridKeyManager",
    "PostQuantumSigner",
    "CryptoAgilityManager",
    "generate_pqc_keypair",
    "create_hybrid_keypair",
    "hybrid_encapsulate",
]