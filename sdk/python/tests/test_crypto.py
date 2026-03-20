"""
Tests for KCP Cryptographic Operations (crypto.py)
"""
import pytest
from kcp.crypto import (
    generate_keypair, sign_artifact, hash_content, verify_artifact,
    encrypt_content, decrypt_content, derive_content_key, is_encrypted,
)


class TestGenerateKeypair:
    def test_returns_two_byte_objects(self):
        priv, pub = generate_keypair()
        assert isinstance(priv, bytes)
        assert isinstance(pub, bytes)

    def test_private_key_32_bytes(self):
        priv, _ = generate_keypair()
        assert len(priv) == 32

    def test_public_key_32_bytes(self):
        _, pub = generate_keypair()
        assert len(pub) == 32

    def test_each_call_generates_unique_keys(self):
        priv1, pub1 = generate_keypair()
        priv2, pub2 = generate_keypair()
        assert priv1 != priv2
        assert pub1 != pub2


class TestHashContent:
    def test_returns_hex_string(self):
        h = hash_content(b"hello")
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 = 32 bytes = 64 hex chars

    def test_deterministic(self):
        assert hash_content(b"test") == hash_content(b"test")

    def test_different_content_different_hash(self):
        assert hash_content(b"foo") != hash_content(b"bar")

    def test_empty_bytes(self):
        h = hash_content(b"")
        assert len(h) == 64

    def test_known_value(self):
        # SHA-256 of empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert hash_content(b"") == expected


class TestSignAndVerify:
    def test_sign_returns_hex_string(self):
        priv, _ = generate_keypair()
        payload = {"title": "Test", "user_id": "alice", "tenant_id": "corp"}
        sig = sign_artifact(payload, priv)
        assert isinstance(sig, str)
        assert len(sig) == 128  # Ed25519 = 64 bytes = 128 hex chars

    def test_verify_valid_signature(self):
        priv, pub = generate_keypair()
        payload = {"title": "Test", "user_id": "alice", "tenant_id": "corp"}
        sig = sign_artifact(payload, priv)
        payload["signature"] = sig
        assert verify_artifact(payload, pub) is True

    def test_verify_invalid_signature(self):
        priv, pub = generate_keypair()
        payload = {"title": "Test", "user_id": "alice", "tenant_id": "corp"}
        payload["signature"] = "a" * 128  # fake sig
        assert verify_artifact(payload, pub) is False

    def test_verify_wrong_public_key(self):
        priv, _ = generate_keypair()
        _, wrong_pub = generate_keypair()
        payload = {"title": "Test", "user_id": "alice", "tenant_id": "corp"}
        sig = sign_artifact(payload, priv)
        payload["signature"] = sig
        assert verify_artifact(payload, wrong_pub) is False

    def test_verify_missing_signature(self):
        _, pub = generate_keypair()
        payload = {"title": "Test", "user_id": "alice", "tenant_id": "corp"}
        assert verify_artifact(payload, pub) is False

    def test_sign_ignores_existing_signature_field(self):
        priv, pub = generate_keypair()
        payload = {
            "title": "Test",
            "user_id": "alice",
            "tenant_id": "corp",
            "signature": "old-sig",
        }
        sig = sign_artifact(payload, priv)
        payload["signature"] = sig
        assert verify_artifact(payload, pub) is True

    def test_tampered_payload_fails_verification(self):
        priv, pub = generate_keypair()
        payload = {"title": "Original", "user_id": "alice", "tenant_id": "corp"}
        sig = sign_artifact(payload, priv)
        payload["signature"] = sig
        # Tamper after signing
        payload["title"] = "Tampered"
        assert verify_artifact(payload, pub) is False


# ─── AES-256-GCM Encryption ───────────────────────────────────

class TestEncryption:
    def test_encrypt_returns_bytes(self):
        priv, _ = generate_keypair()
        key = derive_content_key(priv, "test-id")
        result = encrypt_content(b"hello world", key)
        assert isinstance(result, bytes)

    def test_encrypted_starts_with_magic(self):
        priv, _ = generate_keypair()
        key = derive_content_key(priv, "test-id")
        result = encrypt_content(b"hello", key)
        assert result[:7] == b"KCPENC1"

    def test_is_encrypted_true_for_encrypted(self):
        priv, _ = generate_keypair()
        key = derive_content_key(priv, "test-id")
        blob = encrypt_content(b"hello", key)
        assert is_encrypted(blob) is True

    def test_is_encrypted_false_for_plaintext(self):
        assert is_encrypted(b"plain text content") is False
        assert is_encrypted(b"") is False

    def test_decrypt_returns_original_plaintext(self):
        priv, _ = generate_keypair()
        key = derive_content_key(priv, "artifact-123")
        plaintext = b"This is secret content"
        blob = encrypt_content(plaintext, key)
        result = decrypt_content(blob, key)
        assert result == plaintext

    def test_decrypt_unicode_content(self):
        priv, _ = generate_keypair()
        key = derive_content_key(priv, "artifact-unicode")
        plaintext = "Conteúdo com acentos: ção, ã, ê".encode("utf-8")
        blob = encrypt_content(plaintext, key)
        result = decrypt_content(blob, key)
        assert result.decode("utf-8") == "Conteúdo com acentos: ção, ã, ê"

    def test_different_artifact_ids_produce_different_keys(self):
        priv, _ = generate_keypair()
        key1 = derive_content_key(priv, "id-001")
        key2 = derive_content_key(priv, "id-002")
        assert key1 != key2

    def test_wrong_key_raises_on_decrypt(self):
        from cryptography.exceptions import InvalidTag
        priv, _ = generate_keypair()
        key_correct = derive_content_key(priv, "artifact-a")
        key_wrong   = derive_content_key(priv, "artifact-b")  # different artifact
        blob = encrypt_content(b"secret", key_correct)
        with pytest.raises((InvalidTag, Exception)):
            decrypt_content(blob, key_wrong)

    def test_decrypt_non_kcp_blob_raises(self):
        priv, _ = generate_keypair()
        key = derive_content_key(priv, "test")
        with pytest.raises(ValueError, match="KCPENC1"):
            decrypt_content(b"not encrypted content", key)

    def test_each_encryption_produces_unique_ciphertext(self):
        """Same plaintext + same key = different ciphertext (random nonce)."""
        priv, _ = generate_keypair()
        key = derive_content_key(priv, "artifact-x")
        blob1 = encrypt_content(b"same content", key)
        blob2 = encrypt_content(b"same content", key)
        assert blob1 != blob2  # different nonces

    def test_encrypted_blob_longer_than_plaintext(self):
        priv, _ = generate_keypair()
        key = derive_content_key(priv, "artifact-y")
        plaintext = b"hello"
        blob = encrypt_content(plaintext, key)
        # magic(7) + nonce(12) + ciphertext(5) + GCM tag(16) = 40 bytes
        assert len(blob) == 7 + 12 + len(plaintext) + 16

    def test_content_key_is_32_bytes(self):
        priv, _ = generate_keypair()
        key = derive_content_key(priv, "test")
        assert len(key) == 32


class TestEncryptionEndToEnd:
    def test_private_artifact_stored_encrypted(self, tmp_path):
        """Private artifact content in SQLite must be ciphertext."""
        import sqlite3
        from kcp.node import KCPNode

        node = KCPNode(
            user_id="alice@test.com",
            db_path=str(tmp_path / "kcp.db"),
            keys_dir=str(tmp_path / "keys"),
        )
        secret = b"This is top secret information"
        artifact = node.publish(
            "Secret Report",
            content=secret,
            format="text",
            visibility="private",
        )

        # Read raw blob from SQLite — must NOT be plaintext
        conn = sqlite3.connect(str(tmp_path / "kcp.db"))
        row = conn.execute(
            "SELECT content FROM kcp_content WHERE content_hash = ?",
            (artifact.content_hash,),
        ).fetchone()
        raw_blob = row[0]

        assert raw_blob != secret, "Private content must not be stored as plaintext"
        assert raw_blob[:7] == b"KCPENC1", "Private content must have encryption magic"

    def test_private_artifact_get_content_returns_plaintext(self, tmp_path):
        """get_content() must transparently decrypt private artifacts."""
        from kcp.node import KCPNode

        node = KCPNode(
            user_id="alice@test.com",
            db_path=str(tmp_path / "kcp.db"),
            keys_dir=str(tmp_path / "keys"),
        )
        secret = b"Decrypted automatically"
        artifact = node.publish("Secret", content=secret, format="text", visibility="private")

        result = node.get_content(artifact.id)
        assert result == secret

    def test_public_artifact_not_encrypted(self, tmp_path):
        """Public artifact content must be stored as plaintext."""
        import sqlite3
        from kcp.node import KCPNode

        node = KCPNode(
            user_id="alice@test.com",
            db_path=str(tmp_path / "kcp.db"),
            keys_dir=str(tmp_path / "keys"),
        )
        content = b"Public knowledge - visible to all"
        artifact = node.publish("Public", content=content, format="text", visibility="public")

        conn = sqlite3.connect(str(tmp_path / "kcp.db"))
        row = conn.execute(
            "SELECT content FROM kcp_content WHERE content_hash = ?",
            (artifact.content_hash,),
        ).fetchone()
        assert row[0] == content, "Public content must be stored as plaintext"

    def test_signature_still_valid_on_private_artifact(self, tmp_path):
        """Ed25519 signature must cover plaintext hash — valid regardless of encryption."""
        from kcp.node import KCPNode

        node = KCPNode(
            user_id="alice@test.com",
            db_path=str(tmp_path / "kcp.db"),
            keys_dir=str(tmp_path / "keys"),
        )
        artifact = node.publish(
            "Private but signed",
            content=b"secret content",
            format="text",
            visibility="private",
        )
        assert node.verify(artifact) is True

    def test_other_node_cannot_decrypt_private_artifact(self, tmp_path):
        """A different node without the key cannot read private content."""
        from kcp.node import KCPNode

        node_a = KCPNode(
            user_id="alice@test.com",
            db_path=str(tmp_path / "a.db"),
            keys_dir=str(tmp_path / "keys_a"),
        )
        node_b = KCPNode(
            user_id="bob@test.com",
            db_path=str(tmp_path / "b.db"),
            keys_dir=str(tmp_path / "keys_b"),
        )

        secret = b"Alice's private note"
        artifact = node_a.publish("Private", content=secret, format="text", visibility="private")

        # Sync to node B
        payload = node_a.store.get_artifact_with_content(artifact.id)
        assert payload is not None
        node_b.store.import_artifact(payload)

        # Node B gets the raw encrypted blob — cannot decrypt (no key)
        raw = node_b.store.get_content(artifact.content_hash)
        assert raw is not None
        assert is_encrypted(raw), "Blob should still be encrypted on node B"
        # Node B's get_content returns None (can't decrypt) or encrypted blob
        result = node_b.get_content(artifact.id)
        assert result != secret, "Node B must not be able to read Alice's private content"
