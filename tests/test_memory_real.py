from datetime import UTC, datetime

from neuclx.memory import EvidenceMemory, MemoryEntry


def test_memory_persists_and_searches_verified_records(tmp_path):
    db_path = tmp_path / "memory.sqlite3"
    memory = EvidenceMemory(str(db_path))

    entry = MemoryEntry(
        key="alpha-1",
        content="This is a measured source record.",
        source_id="repo-1",
        evidence_state="measured",
        created_at=datetime.now(UTC).isoformat(),
    )

    memory.store(entry)
    results = memory.search("measured source")

    assert any(item.key == "alpha-1" for item in results)
    assert memory.get("alpha-1").content == "This is a measured source record."


def test_memory_rejects_unverified_content():
    memory = EvidenceMemory(":memory:")
    try:
        memory.store(
            MemoryEntry(
                key="bad-1",
                content="fake content",
                source_id="repo-2",
                evidence_state="declared",
                created_at=datetime.now(UTC).isoformat(),
            )
        )
        assert False, "expected an unverified memory entry to be rejected"
    except ValueError:
        pass
