from evaluation.verify_test_query_citations import (
    CitationReference,
    find_unresolved_citations,
    parse_citation_references,
)


def test_parse_single_cfr_citation():
    references = parse_citation_references("14 CFR § 91.155")

    assert references == [
        CitationReference(document="14 CFR Part 91", section_number="91.155")
    ]


def test_parse_cfr_citation_with_paragraph_suffix():
    references = parse_citation_references("14 CFR § 61.57(b)")

    assert references == [
        CitationReference(document="14 CFR Part 61", section_number="61.57")
    ]


def test_parse_multiple_cfr_citations():
    references = parse_citation_references("14 CFR §§ 91.409, 91.413")

    assert references == [
        CitationReference(document="14 CFR Part 91", section_number="91.409"),
        CitationReference(document="14 CFR Part 91", section_number="91.413"),
    ]


def test_parse_aim_citation_with_paragraph_suffix():
    references = parse_citation_references("AIM 8-1-2(d)")

    assert references == [CitationReference(document="AIM", section_number="8-1-2")]


def test_parse_multiple_aim_citations():
    references = parse_citation_references("AIM 6-4-2 / 4-1-20")

    assert references == [
        CitationReference(document="AIM", section_number="6-4-2"),
        CitationReference(document="AIM", section_number="4-1-20"),
    ]


def test_parse_mixed_cfr_and_aim_citation():
    references = parse_citation_references("14 CFR § 71.33 (AIM 3-2-2)")

    assert references == [
        CitationReference(document="14 CFR Part 71", section_number="71.33"),
        CitationReference(document="AIM", section_number="3-2-2"),
    ]


def test_unresolved_citations_are_reported_for_in_scope_queries():
    test_queries = [
        {
            "id": "G-01",
            "question_type": "in_scope",
            "expected_citation": "14 CFR § 91.155",
        }
    ]
    chunks = [
        {
            "document": "14 CFR Part 91",
            "section_number": "91.157",
            "chunk_text": "wrong section",
        }
    ]

    unresolved = find_unresolved_citations(test_queries, chunks)

    assert len(unresolved) == 1
    assert unresolved[0].query_id == "G-01"
    assert unresolved[0].reference == CitationReference(
        document="14 CFR Part 91",
        section_number="91.155",
    )
    assert unresolved[0].reason == "reference not found in chunks"


def test_unparseable_in_scope_citation_is_reported():
    test_queries = [
        {
            "id": "G-99",
            "question_type": "in_scope",
            "expected_citation": "some unsupported citation format",
        }
    ]

    unresolved = find_unresolved_citations(test_queries, chunks=[])

    assert len(unresolved) == 1
    assert unresolved[0].reference is None
    assert unresolved[0].reason == "no parseable citation references"


def test_out_of_scope_queries_do_not_require_citation_resolution():
    test_queries = [
        {
            "id": "R-01",
            "question_type": "out_of_scope",
            "expected_citation": None,
        }
    ]

    assert find_unresolved_citations(test_queries, chunks=[]) == []
