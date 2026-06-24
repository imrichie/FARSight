from src.citation_builder import build_citation_from_chunk


def _complete_chunk():
    return {
        "document": "14 CFR Part 91",
        "section_number": "91.215",
        "section_title": "ATC transponder and altitude reporting equipment and use",
        "page_number": 58,
        "corpus_version": "2024-01-01",
    }


def test_build_citation_from_complete_chunk_metadata():
    citation = build_citation_from_chunk(_complete_chunk())

    assert citation == {
        "available": True,
        "document": "14 CFR Part 91",
        "section_number": "91.215",
        "section_title": "ATC transponder and altitude reporting equipment and use",
        "page_number": 58,
        "corpus_version": "2024-01-01",
    }


def test_missing_metadata_marks_citation_unavailable():
    chunk = _complete_chunk()
    del chunk["section_number"]

    citation = build_citation_from_chunk(chunk)

    assert citation["available"] is False
    assert citation["section_number"] is None


def test_blank_metadata_marks_citation_unavailable():
    chunk = _complete_chunk()
    chunk["document"] = " "

    citation = build_citation_from_chunk(chunk)

    assert citation["available"] is False
    assert citation["document"] is None
