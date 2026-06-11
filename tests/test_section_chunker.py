# test_section_chunker.py
# Unit tests for section-to-chunk conversion and the lettered-paragraph
# splitting logic against small fixture sections — no PDFs involved.

from src.data_pipeline.regulation_parser import ParsedRegulationDocument, RegulationSection
from src.data_pipeline.section_chunker import (
    SECTION_SPLIT_CHARACTER_THRESHOLD,
    chunk_parsed_document,
    find_sequential_paragraph_boundaries,
    sanitize_for_chunk_id,
)


def build_fixture_document(sections):
    return ParsedRegulationDocument(
        document_name="14 CFR Part 91",
        part_number="91",
        corpus_version="2024-01-01",
        sections=sections,
    )


def test_short_section_becomes_one_chunk_with_header():
    fixture_document = build_fixture_document(
        [RegulationSection("91.15", "Dropping objects", "No pilot in command may drop objects.", 10)]
    )
    chunks, warnings = chunk_parsed_document(fixture_document)
    assert len(chunks) == 1
    assert warnings == []
    assert chunks[0]["chunk_text"].startswith("§ 91.15 Dropping objects\n")
    assert chunks[0]["section_number"] == "91.15"
    assert chunks[0]["corpus_version"] == "2024-01-01"


def test_chunk_id_contains_only_azure_search_safe_characters():
    assert sanitize_for_chunk_id("14 CFR Part 91") == "14-cfr-part-91"
    assert sanitize_for_chunk_id("91.215") == "91-215"


def test_long_section_splits_at_lettered_paragraphs_with_header_prepended():
    paragraph_padding = "x" * (SECTION_SPLIT_CHARACTER_THRESHOLD // 2)
    section_text = (
        f"Introductory applicability text.\n"
        f"(a) First requirement. {paragraph_padding}\n"
        f"(b) Second requirement. {paragraph_padding}\n"
        f"(c) Third requirement. {paragraph_padding}"
    )
    fixture_document = build_fixture_document(
        [RegulationSection("91.205", "Instrument and equipment requirements", section_text, 40)]
    )
    chunks, warnings = chunk_parsed_document(fixture_document)
    assert warnings == []
    assert len(chunks) == 3
    assert [chunk["id"][-2:] for chunk in chunks] == ["_a", "_b", "_c"]
    for chunk in chunks:
        assert chunk["chunk_text"].startswith("§ 91.205 Instrument and equipment requirements\n")
    # intro text travels with the first piece
    assert "Introductory applicability text." in chunks[0]["chunk_text"]
    assert "(b) Second requirement." in chunks[1]["chunk_text"]


def test_out_of_sequence_labels_are_not_split_points():
    boundaries = find_sequential_paragraph_boundaries(
        "(a) First paragraph.\n(d)(2) of this section does not apply.\n(b) Second paragraph."
    )
    boundary_labels = [label for _, label in boundaries]
    assert boundary_labels == ["a", "b"]


def test_long_section_without_paragraphs_stays_whole_with_warning():
    fixture_document = build_fixture_document(
        [
            RegulationSection(
                "91.313",
                "Restricted category aircraft",
                "y" * (SECTION_SPLIT_CHARACTER_THRESHOLD + 100),
                70,
            )
        ]
    )
    chunks, warnings = chunk_parsed_document(fixture_document)
    assert len(chunks) == 1
    assert len(warnings) == 1
    assert "91.313" in warnings[0]
