#!/usr/bin/env python3
"""
KCP Cross-Session Demo
======================
Demonstrates the core value proposition: knowledge persists across sessions.

Run twice:
    python demo.py          # Session 1: publishes artifacts
    python demo.py --read   # Session 2: retrieves artifacts from Session 1

Or use make:
    make demo               # runs Session 1
    make demo-read          # runs Session 2
"""
import argparse
import sys
import os

# Allow running from repo root without installing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "sdk", "python"))

from kcp import KCPNode

DB_PATH = "/tmp/kcp-demo.db"
KEYS_DIR = "/tmp/kcp-demo-keys"
USER_ID = "demo@kcp-protocol.org"
TENANT_ID = "kcp-demo"


def session_1_publish():
    """SESSION 1 — Publishes 3 knowledge artifacts and exits."""
    print("\n" + "═" * 58)
    print("  KCP Demo — SESSION 1: Publishing knowledge")
    print("  Database:", DB_PATH)
    print("═" * 58)

    node = KCPNode(
        user_id=USER_ID,
        tenant_id=TENANT_ID,
        db_path=DB_PATH,
        keys_dir=KEYS_DIR,
    )

    # Artifact 1: base knowledge
    a1 = node.publish(
        title="Rate Limiting Strategies",
        content=(
            "## Token Bucket\n\n"
            "The most common approach. Allows burst traffic up to bucket size, "
            "then throttles at a steady rate.\n\n"
            "## Leaky Bucket\n\n"
            "Smooths output rate. Useful for downstream services that can't "
            "handle bursts.\n\n"
            "## Fixed Window\n\n"
            "Simple but suffers from boundary spikes."
        ),
        tags=["architecture", "rate-limiting", "api-design"],
        format="markdown",
    )
    print(f"\n✅ Published: [{a1.id[:8]}…] {a1.title}")
    print(f"   Tags: {a1.tags}")
    print(f"   Hash: {a1.content_hash[:24]}…")
    print(f"   Sig:  {a1.signature[:24]}…")

    # Artifact 2: derived from artifact 1
    a2 = node.publish(
        title="Rate Limiting in gRPC Services",
        content=(
            "## Building on General Strategies\n\n"
            "gRPC adds complexity: streaming RPCs, per-method limits, "
            "and metadata-based client identification.\n\n"
            "## Recommended: Token Bucket per (client_id, method)\n\n"
            "Use interceptors to apply limits transparently."
        ),
        tags=["grpc", "rate-limiting", "microservices"],
        format="markdown",
        derived_from=a1.id,
    )
    print(f"\n✅ Published: [{a2.id[:8]}…] {a2.title}")
    print(f"   Derived from: [{a1.id[:8]}…] {a1.title}")

    # Artifact 3: unrelated topic
    a3 = node.publish(
        title="SQLite as Application Database",
        content=(
            "SQLite is underrated for production applications.\n\n"
            "- Up to 281 TB database size\n"
            "- WAL mode: concurrent readers + one writer\n"
            "- Zero-config, embedded, no server\n\n"
            "KCP itself uses SQLite + FTS5 for local storage."
        ),
        tags=["sqlite", "database", "architecture"],
        format="markdown",
    )
    print(f"\n✅ Published: [{a3.id[:8]}…] {a3.title}")

    stats = node.stats()
    print(f"\n📊 Node stats: {stats.get('artifacts', 0)} artifacts in {DB_PATH}")
    print("\n" + "─" * 58)
    print("  Now run:  python demo.py --read")
    print("  Or:       make demo-read")
    print("─" * 58 + "\n")


def session_2_read():
    """SESSION 2 — Opens same DB and retrieves artifacts from Session 1."""
    print("\n" + "═" * 58)
    print("  KCP Demo — SESSION 2: Reading persisted knowledge")
    print("  Database:", DB_PATH)
    print("═" * 58)

    if not os.path.exists(DB_PATH):
        print(f"\n❌ Database not found: {DB_PATH}")
        print("   Run Session 1 first:  python demo.py\n")
        sys.exit(1)

    # New process, new node — same DB
    node = KCPNode(
        user_id=USER_ID,
        tenant_id=TENANT_ID,
        db_path=DB_PATH,
        keys_dir=KEYS_DIR,
    )

    stats = node.stats()
    print(f"\n📊 Found {stats.get('artifacts', 0)} artifacts from previous session\n")

    # Search — full-text search across sessions
    print("🔍 Searching: 'rate limiting'")
    response = node.search("rate limiting")
    results = response.results
    for r in results:
        print(f"   [{r.id[:8]}…] {r.title}  (relevance: {r.relevance:.3f})")

    print("\n🔍 Searching: 'sqlite'")
    response2 = node.search("sqlite")
    results2 = response2.results
    for r in results2:
        print(f"   [{r.id[:8]}…] {r.title}")

    # Get first result and verify signature
    if results:
        first_id = results[0].id
        artifact = node.get(first_id)
        print(f"\n📄 Full artifact: {artifact.title}")
        print(f"   ID:        {artifact.id}")
        print(f"   Tags:      {artifact.tags}")
        print(f"   Created:   {artifact.timestamp}")
        print(f"   Hash:      {artifact.content_hash[:32]}…")

        valid = node.verify(artifact)
        print(f"   Signature: {'✅ VALID' if valid else '❌ INVALID'}")

    # Show lineage — lineage() returns a list of dicts
    print("\n🌳 Lineage of 'Rate Limiting in gRPC Services':")
    response_grpc = node.search("grpc rate limiting")
    results_grpc = response_grpc.results
    if results_grpc:
        lineage = node.lineage(results_grpc[0].id)
        for i, item in enumerate(lineage):
            indent = "  " * i
            parent_id = item.get("derived_from")
            parent_info = f" ← derived from [{parent_id[:8]}…]" if parent_id else " (root)"
            print(f"   {indent}[{item['id'][:8]}…] {item['title']}{parent_info}")

    print("\n" + "─" * 58)
    print("  ✅ Knowledge survived the session boundary!")
    print("  Same DB, new process, full access + verified signatures.")
    print("─" * 58 + "\n")


def main():
    parser = argparse.ArgumentParser(description="KCP Cross-Session Demo")
    parser.add_argument("--read", action="store_true", help="Run Session 2 (read mode)")
    parser.add_argument("--clean", action="store_true", help="Delete demo database")
    args = parser.parse_args()

    if args.clean:
        for path in [DB_PATH, KEYS_DIR]:
            import shutil
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                print(f"🗑  Removed: {path}")
        print("✅ Demo state cleaned.\n")
        return

    if args.read:
        session_2_read()
    else:
        session_1_publish()


if __name__ == "__main__":
    main()
