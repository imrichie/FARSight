# test_regulation_retriever_integration.py
# Integration tests: one targeted query per source document against the
# live farsight-regulations index. Confirms that hybrid retrieval surfaces
# content from each corpus and that every returned chunk has its metadata
# fields populated.
#
# Requires Azure credentials in .env and a healthy index.
# Skip these during CI:  python3 -m pytest tests/ -m "not integration"
# Run alone:             python3 -m pytest tests/test_regulation_retriever_integration.py

import pytest

from src.regulation_retriever import RETRIEVED_CHUNK_FIELDS, retrieve_relevant_regulation_chunks


def _assert_fields_populated(chunk: dict) -> None:
    for field in RETRIEVED_CHUNK_FIELDS:
        assert chunk.get(field) is not None, f"field '{field}' is None or missing"
    assert "search_score" in chunk


@pytest.mark.integration
def test_part_91_query_returns_relevant_chunk():
    """G-05: 'How long after drinking can I fly?' → Part 91 §91.17."""
    results = retrieve_relevant_regulation_chunks("How long after drinking can I fly?")
    assert len(results) >= 1
    assert any(r["document"] == "14 CFR Part 91" for r in results)
    for chunk in results:
        _assert_fields_populated(chunk)


@pytest.mark.integration
def test_part_61_query_returns_relevant_chunk():
    """G-17: 'What documents must a pilot carry to act as PIC?' → Part 61 §61.3."""
    results = retrieve_relevant_regulation_chunks(
        "What documents must a pilot carry to act as pilot in command?"
    )
    assert len(results) >= 1
    assert any(r["document"] == "14 CFR Part 61" for r in results)
    for chunk in results:
        _assert_fields_populated(chunk)


@pytest.mark.integration
def test_part_67_query_returns_relevant_chunk():
    """'What vision is required for a first class medical?' → Part 67 §67.103."""
    results = retrieve_relevant_regulation_chunks(
        "What are the vision standards required for a first class airman medical certificate?"
    )
    assert len(results) >= 1
    assert any(r["document"] == "14 CFR Part 67" for r in results)
    for chunk in results:
        _assert_fields_populated(chunk)


@pytest.mark.integration
def test_part_71_query_returns_relevant_chunk():
    """'What are the dimensions of VOR Federal airways?' → Part 71."""
    results = retrieve_relevant_regulation_chunks(
        "What are the dimensions and altitudes of VOR Federal airways?"
    )
    assert len(results) >= 1
    assert any(r["document"] == "14 CFR Part 71" for r in results)
    for chunk in results:
        _assert_fields_populated(chunk)


@pytest.mark.integration
def test_aim_query_returns_relevant_chunk():
    """'What equipment is required for ADS-B Out?' → AIM 4-3-13."""
    results = retrieve_relevant_regulation_chunks("What equipment is required for ADS-B Out?")
    assert len(results) >= 1
    assert any(r["document"] == "AIM" for r in results)
    for chunk in results:
        _assert_fields_populated(chunk)
