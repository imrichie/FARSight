# test_regulation_parser.py
# Unit tests for section-detection and text-assembly logic against
# small fixture text — no PDFs involved.

from src.data_pipeline.regulation_parser import (
    SECTION_HEADING_PATTERN,
    append_wrapped_heading_line,
    assemble_section_text,
    join_wrapped_lines,
)


def test_heading_pattern_captures_section_number_and_title():
    heading_match = SECTION_HEADING_PATTERN.match("§ 91.17 Alcohol or drugs.")
    assert heading_match is not None
    assert heading_match.group(1) == "91.17"
    assert heading_match.group(2) == "Alcohol or drugs."


def test_heading_pattern_rejects_body_text():
    assert SECTION_HEADING_PATTERN.match("under the provisions of this part") is None


def test_hyphenated_word_wrap_is_repaired():
    joined_text = join_wrapped_lines(["act as a crewmember of a civil air-", "craft within 8 hours"])
    assert joined_text == "act as a crewmember of a civil aircraft within 8 hours"


def test_real_compound_hyphen_is_kept():
    joined_text = join_wrapped_lines(["Automatic Dependent Surveillance-", "Broadcast equipment"])
    assert joined_text == "Automatic Dependent Surveillance-Broadcast equipment"


def test_wrapped_heading_line_repairs_title_hyphenation():
    heading_text = append_wrapped_heading_line("Minimum safe altitudes: Gen-", "eral.")
    assert heading_text == "Minimum safe altitudes: General."


def test_lettered_paragraphs_start_new_lines():
    section_text = assemble_section_text(
        [
            "(a) No person may act as a crew-",
            "member of a civil aircraft—",
            "(1) Within 8 hours after drinking;",
            "(b) Except in an emergency, no pilot",
            "may allow an intoxicated person aboard.",
        ]
    )
    section_lines = section_text.split("\n")
    assert len(section_lines) == 2
    assert section_lines[0].startswith("(a) No person may act as a crewmember")
    assert "(1) Within 8 hours after drinking;" in section_lines[0]
    assert section_lines[1].startswith("(b) Except in an emergency")
