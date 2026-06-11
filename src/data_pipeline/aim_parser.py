# aim_parser.py
# Extracts structured paragraphs from the FAA Aeronautical Information
# Manual PDF. The AIM is typeset differently from the CFR parts: paragraph
# headings are Helvetica-Bold ("4−3−13. Traffic Control Light Signals"),
# and page furniture shares fonts with real content (NOTE and REFERENCE
# blocks), so furniture is removed by page position — header and footer
# zones — rather than by font.

import re
from datetime import datetime

import fitz

from src.data_pipeline.regulation_parser import (
    ParsedRegulationDocument,
    RegulationSection,
    join_wrapped_lines,
    normalize_whitespace,
)

AIM_HEADING_FONT = "Helvetica-Bold"

# Vertical page zones (page height is 792pt): anything above or below
# these bounds is a running header or footer, never content
PAGE_HEADER_ZONE_BOTTOM = 55
PAGE_FOOTER_ZONE_TOP = 735

# Matches an AIM paragraph heading like "4−3−13. Traffic Control Light
# Signals" — the AIM prints dashes as Unicode minus signs (U+2212)
AIM_PARAGRAPH_HEADING_PATTERN = re.compile(r"^(\d+[−-]\d+[−-]\d+)\.\s*(.*)$")

# Matches table-of-contents dot leaders, e.g. "4−3−13. Traffic ... 4−3−19"
TOC_DOT_LEADER_PATTERN = re.compile(r"(\.\s){4,}")

# Matches a line that begins a top-level AIM subparagraph, e.g. "a. ..."
AIM_SUBPARAGRAPH_PATTERN = re.compile(r"^[a-z]\.\s")

# Matches a line that begins a numbered sub-item, e.g. "1. ..." — the
# required space after the period keeps decimals like "29.92" from matching
AIM_NUMBERED_ITEM_PATTERN = re.compile(r"^\d{1,2}\.\s")

# Block labels that start a labeled passage (notes, examples, references)
AIM_BLOCK_LABEL_PATTERN = re.compile(r"^(NOTE|EXAMPLE|PHRASEOLOGY|REFERENCE)[−-]")

# The cover prints the publication date, e.g. "April 20, 2023"
COVER_DATE_PATTERN = re.compile(r"([A-Z][a-z]+ \d{1,2}, \d{4})")

# Back-matter pages identify themselves in the footer page label:
# "Appendix 3−1" for appendices, "PCG A−1" for the Pilot/Controller
# Glossary. Numbered paragraphs end where these pages begin.
BACK_MATTER_FOOTER_PATTERN = re.compile(r"Appendix\s+\d|PCG")


def assemble_aim_paragraph_text(body_lines: list[str]) -> str:
    """
    Assemble AIM body lines, one passage per output line.

    Top-level subparagraphs ("a. ..."), numbered sub-items ("1. ..."),
    and labeled blocks (NOTE−, EXAMPLE−, PHRASEOLOGY−, REFERENCE−) each
    start a new passage.
    """
    passages: list[list[str]] = [[]]
    for line in body_lines:
        if (
            AIM_SUBPARAGRAPH_PATTERN.match(line)
            or AIM_NUMBERED_ITEM_PATTERN.match(line)
            or AIM_BLOCK_LABEL_PATTERN.match(line)
        ):
            passages.append([line])
        else:
            passages[-1].append(line)
    assembled_passages = [join_wrapped_lines(lines) for lines in passages if lines]
    return "\n".join(passage for passage in assembled_passages if passage)


def page_begins_back_matter(page_text_dict: dict) -> bool:
    """True when the page's footer labels it as appendix or glossary."""
    for text_block in page_text_dict["blocks"]:
        for text_line in text_block.get("lines", []):
            if text_line["bbox"][1] > PAGE_FOOTER_ZONE_TOP:
                footer_text = " ".join(span["text"] for span in text_line["spans"])
                if BACK_MATTER_FOOTER_PATTERN.search(footer_text):
                    return True
    return False


def extract_aim_content_lines(pdf_document: fitz.Document):
    """
    Yield (line_text, is_heading_line, page_number) for AIM content lines.

    Stops at the first appendix or glossary page — the back matter has no
    numbered paragraphs and must never bleed into the last one.
    """
    for page_index, pdf_page in enumerate(pdf_document):
        page_text_dict = pdf_page.get_text("dict")
        if page_begins_back_matter(page_text_dict):
            return
        for text_block in page_text_dict["blocks"]:
            for text_line in text_block.get("lines", []):
                line_top = text_line["bbox"][1]
                if line_top < PAGE_HEADER_ZONE_BOTTOM or line_top > PAGE_FOOTER_ZONE_TOP:
                    continue
                line_text = normalize_whitespace(
                    " ".join(span["text"] for span in text_line["spans"])
                )
                if not line_text or TOC_DOT_LEADER_PATTERN.search(line_text):
                    continue
                is_heading_line = all(
                    span["font"] == AIM_HEADING_FONT for span in text_line["spans"]
                ) and bool(AIM_PARAGRAPH_HEADING_PATTERN.match(line_text))
                yield line_text, is_heading_line, page_index + 1


def extract_aim_publication_date(pdf_document: fitz.Document) -> str:
    """Read the publication date from the AIM cover as an ISO date."""
    date_match = COVER_DATE_PATTERN.search(pdf_document[0].get_text())
    if date_match:
        return datetime.strptime(date_match.group(1), "%B %d, %Y").strftime("%Y-%m-%d")
    return "unknown"


def parse_aim_pdf(pdf_file_path: str) -> ParsedRegulationDocument:
    """
    Parse the AIM PDF into structured paragraphs, one per numbered
    paragraph (e.g. 4−3−13). Paragraph numbers are normalized to plain
    hyphens ("4-3-13") for citations and chunk ids.
    """
    pdf_document = fitz.open(pdf_file_path)
    parsed_document = ParsedRegulationDocument(
        document_name="AIM",
        part_number="AIM",
        corpus_version=extract_aim_publication_date(pdf_document),
    )

    current_section: RegulationSection | None = None
    current_body_lines: list[str] = []

    def finalize_current_section():
        if current_section is not None:
            current_section.section_text = assemble_aim_paragraph_text(current_body_lines)
            parsed_document.sections.append(current_section)

    for line_text, is_heading_line, page_number in extract_aim_content_lines(pdf_document):
        if is_heading_line:
            heading_match = AIM_PARAGRAPH_HEADING_PATTERN.match(line_text)
            finalize_current_section()
            current_section = RegulationSection(
                section_number=re.sub(r"[−]", "-", heading_match.group(1)),
                section_title=heading_match.group(2).strip(),
                section_text="",
                page_number=page_number,
            )
            current_body_lines = []
        elif current_section is not None:
            current_body_lines.append(line_text)
        else:
            parsed_document.out_of_scope_lines_dropped += 1

    finalize_current_section()
    pdf_document.close()
    return parsed_document
