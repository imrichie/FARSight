# section_chunker.py
# Turns parsed regulation sections into enriched chunks ready for
# embedding and persistence. One section is one chunk; sections longer
# than the split threshold are divided at top-level lettered paragraphs,
# with the parent section header prepended to every piece so no chunk
# ever loses its regulatory context.

import re

from src.data_pipeline.regulation_parser import ParsedRegulationDocument, RegulationSection

# Sections longer than this are split at their lettered paragraphs.
# Generous enough that most sections stay whole, small enough that
# a retrieved chunk stays focused on one rule.
SECTION_SPLIT_CHARACTER_THRESHOLD = 6000

# Matches a top-level lettered paragraph at the start of a line —
# CFR style "(a) ", AIM style "a. "
CFR_LETTERED_PARAGRAPH_PATTERN = re.compile(r"^\(([a-z]{1,2})\)\s", re.MULTILINE)
AIM_LETTERED_PARAGRAPH_PATTERN = re.compile(r"^([a-z])\.\s", re.MULTILINE)

# Matches an AIM numbered sub-item at the start of a line, e.g. "1. " —
# the second, deeper split level for pieces still over the threshold
AIM_NUMBERED_ITEM_PATTERN = re.compile(r"^(\d{1,2})\.\s", re.MULTILINE)


def next_paragraph_letter(current_letter: str) -> str:
    """CFR paragraph letters run (a)–(z), then double up: (aa), (bb), ..."""
    if len(current_letter) == 1:
        return "aa" if current_letter == "z" else chr(ord(current_letter) + 1)
    return current_letter[0] * 2 if current_letter[0] == "z" else chr(ord(current_letter[0]) + 1) * 2


def find_sequential_paragraph_boundaries(
    section_text: str,
    paragraph_pattern: re.Pattern = CFR_LETTERED_PARAGRAPH_PATTERN,
) -> list[tuple[int, str]]:
    """
    Find the character offsets where top-level lettered paragraphs begin.

    Only accepts paragraphs in strict alphabetical sequence starting at (a) —
    this rejects inline cross-references like "(a)(2)" that happen to land
    at the start of a wrapped line.
    """
    boundaries: list[tuple[int, str]] = []
    expected_letter = "a"
    for match in paragraph_pattern.finditer(section_text):
        if match.group(1) == expected_letter:
            boundaries.append((match.start(), expected_letter))
            expected_letter = next_paragraph_letter(expected_letter)
    return boundaries


def find_sequential_numbered_boundaries(piece_text: str) -> list[tuple[int, str]]:
    """
    Find the offsets where AIM numbered sub-items begin, accepting only
    items in strict 1, 2, 3... sequence — same false-positive guard as
    the lettered split.
    """
    boundaries: list[tuple[int, str]] = []
    expected_item_number = 1
    for match in AIM_NUMBERED_ITEM_PATTERN.finditer(piece_text):
        if int(match.group(1)) == expected_item_number:
            boundaries.append((match.start(), str(expected_item_number)))
            expected_item_number += 1
    return boundaries


def split_text_at_boundaries(text: str, boundaries: list[tuple[int, str]]) -> list[tuple[str, str]]:
    """Split text at boundary offsets; text before the first boundary
    stays with the first piece."""
    pieces: list[tuple[str, str]] = []
    for boundary_index, (start_offset, piece_label) in enumerate(boundaries):
        piece_start = 0 if boundary_index == 0 else start_offset
        piece_end = (
            boundaries[boundary_index + 1][0]
            if boundary_index + 1 < len(boundaries)
            else len(text)
        )
        pieces.append((piece_label, text[piece_start:piece_end].strip()))
    return pieces


def sanitize_for_chunk_id(raw_text: str) -> str:
    """Azure AI Search keys allow only letters, digits, dashes, underscores."""
    return re.sub(r"[^A-Za-z0-9_-]", "-", raw_text.lower()).strip("-")


def build_chunk(
    parsed_document: ParsedRegulationDocument,
    section: RegulationSection,
    chunk_text: str,
    paragraph_label: str | None = None,
) -> dict:
    chunk_id = (
        f"{sanitize_for_chunk_id(parsed_document.document_name)}"
        f"_{sanitize_for_chunk_id(section.section_number)}"
    )
    if paragraph_label is not None:
        chunk_id = f"{chunk_id}_{paragraph_label}"
    return {
        "id": chunk_id,
        "document": parsed_document.document_name,
        "part_number": parsed_document.part_number,
        "section_number": section.section_number,
        "section_title": section.section_title,
        "chunk_text": chunk_text,
        "page_number": section.page_number,
        "corpus_version": parsed_document.corpus_version,
    }


def chunk_parsed_document(parsed_document: ParsedRegulationDocument) -> tuple[list[dict], list[str]]:
    """
    Convert every parsed section into one or more chunks.

    Returns the chunks plus a list of warnings for sections that were too
    long to stay whole but had no clean lettered paragraphs to split at.
    """
    chunks: list[dict] = []
    chunking_warnings: list[str] = []

    # The AIM cites paragraphs as "AIM 4-3-13", not with a § symbol,
    # and splits at "a." subparagraphs rather than "(a)"
    document_is_aim = parsed_document.part_number == "AIM"
    paragraph_pattern = (
        AIM_LETTERED_PARAGRAPH_PATTERN if document_is_aim else CFR_LETTERED_PARAGRAPH_PATTERN
    )

    for section in parsed_document.sections:
        if document_is_aim:
            section_header = f"AIM {section.section_number} {section.section_title}"
        else:
            section_header = f"§ {section.section_number} {section.section_title}"
        whole_section_text = f"{section_header}\n{section.section_text}"

        if len(whole_section_text) <= SECTION_SPLIT_CHARACTER_THRESHOLD:
            chunks.append(build_chunk(parsed_document, section, whole_section_text))
            continue

        boundaries = find_sequential_paragraph_boundaries(section.section_text, paragraph_pattern)
        if len(boundaries) < 2 and document_is_aim:
            # Some AIM paragraphs have numbered items but no lettered
            # subparagraphs — fall back to the numbered level directly
            boundaries = find_sequential_numbered_boundaries(section.section_text)
        if len(boundaries) < 2:
            chunking_warnings.append(
                f"{section.section_number} is {len(whole_section_text)} chars "
                "but has no lettered paragraphs to split at — kept whole"
            )
            chunks.append(build_chunk(parsed_document, section, whole_section_text))
            continue

        # Any introductory text before (a) stays with the first piece
        for paragraph_label, piece_text in split_text_at_boundaries(
            section.section_text, boundaries
        ):
            piece_chunk_text = f"{section_header}\n{piece_text}"
            if len(piece_chunk_text) <= SECTION_SPLIT_CHARACTER_THRESHOLD or not document_is_aim:
                if len(piece_chunk_text) > SECTION_SPLIT_CHARACTER_THRESHOLD:
                    chunking_warnings.append(
                        f"{section.section_number}({paragraph_label}) is still "
                        f"{len(piece_chunk_text)} chars after the lettered-paragraph "
                        "split — no deeper split rule exists for CFR text"
                    )
                chunks.append(
                    build_chunk(parsed_document, section, piece_chunk_text, paragraph_label)
                )
                continue

            # AIM piece still over the threshold — split one level deeper
            # at its numbered sub-items, parent header prepended to every
            # sub-piece
            numbered_boundaries = find_sequential_numbered_boundaries(piece_text)
            if len(numbered_boundaries) < 2:
                chunking_warnings.append(
                    f"{section.section_number}({paragraph_label}) is "
                    f"{len(piece_chunk_text)} chars with no numbered sub-items "
                    "to split at — kept whole"
                )
                chunks.append(
                    build_chunk(parsed_document, section, piece_chunk_text, paragraph_label)
                )
                continue

            for item_label, item_text in split_text_at_boundaries(
                piece_text, numbered_boundaries
            ):
                item_chunk_text = f"{section_header}\n{item_text}"
                if len(item_chunk_text) > SECTION_SPLIT_CHARACTER_THRESHOLD:
                    chunking_warnings.append(
                        f"{section.section_number}({paragraph_label})({item_label}) "
                        f"is still {len(item_chunk_text)} chars after the numbered "
                        "sub-item split — no deeper split rule exists"
                    )
                chunks.append(
                    build_chunk(
                        parsed_document,
                        section,
                        item_chunk_text,
                        paragraph_label=f"{paragraph_label}_{item_label}",
                    )
                )

    return chunks, chunking_warnings
