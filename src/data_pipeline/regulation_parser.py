# regulation_parser.py
# Extracts structured regulation sections from a GPO-printed 14 CFR PDF.
# Works from font information rather than raw text: section headings are
# printed in bold, body text in a serif face, and page furniture (running
# headers, page numbers, printer marks, amendment notes) in fonts and sizes
# that never carry regulation text — so cleaning is a font filter, not
# guesswork against the text itself.

import re
from dataclasses import dataclass, field

import fitz

# Font signatures observed in the GPO annual-edition CFR PDFs
SECTION_HEADING_FONT = "NewCenturySchlbk-Bold"
BODY_FONT_PREFIX = "MIonic"

# Regulation text (headings and body) is set at 8pt; everything at other
# sizes is page furniture, tables of contents, or amendment history notes
REGULATION_TEXT_FONT_SIZE = 8

# Matches a section heading like "§ 91.17 Alcohol or drugs."
SECTION_HEADING_PATTERN = re.compile(r"^§\s*(\d+\.\d+[\w–-]*)\s*(.*)$")

# Matches the edition date in the running header, e.g. "(1–1–24 Edition)"
EDITION_DATE_PATTERN = re.compile(r"\((\d{1,2})[–-](\d{1,2})[–-](\d{2}) Edition\)")


def section_number_sort_key(section_number: str) -> tuple[int, int]:
    """Numeric key for a section number like "91.309" → (91, 309)."""
    number_match = re.match(r"(\d+)\.(\d+)", section_number)
    return (int(number_match.group(1)), int(number_match.group(2)))

# Matches a line that begins a top-level lettered paragraph, e.g. "(a) ..."
TOP_LEVEL_PARAGRAPH_PATTERN = re.compile(r"^\([a-z]{1,2}\)\s")

# Matches an appendix heading, e.g. "Appendix A to Part 91—..." — detected
# from raw span text because appendix titles are typeset in small caps.
# Case-sensitive on purpose: small-caps headings render as all-caps glyphs,
# while inline references ("appendix A to part 141") stay lowercase and
# must never trip this
APPENDIX_HEADING_PATTERN = re.compile(r"APPENDIX\s+[A-Z]\s+TO\s+PART\s+\d+")

# Small-caps lines mix 8pt capitals with ~6.5pt small letters; a span this
# small inside a body-font line is the typographic signature of a heading
SMALL_CAPS_SPAN_MAX_SIZE = 7.5


@dataclass
class RegulationSection:
    section_number: str
    section_title: str
    section_text: str
    page_number: int


@dataclass
class ParsedRegulationDocument:
    document_name: str
    part_number: str
    corpus_version: str
    sections: list[RegulationSection] = field(default_factory=list)
    skipped_headings: list[str] = field(default_factory=list)
    out_of_scope_lines_dropped: int = 0


def is_regulation_text_span(text_span: dict) -> bool:
    """Keep only spans in the fonts and size that carry regulation text."""
    font_name = text_span["font"]
    is_regulation_font = (
        font_name == SECTION_HEADING_FONT or font_name.startswith(BODY_FONT_PREFIX)
    )
    return is_regulation_font and round(text_span["size"]) == REGULATION_TEXT_FONT_SIZE


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def join_wrapped_lines(text_lines: list[str]) -> str:
    """
    Join print-wrapped lines back into flowing text, repairing hyphenation.

    A line ending in "-" was hyphenated by the typesetter: the hyphen is
    dropped when the continuation starts lowercase ("air-" + "craft" →
    "aircraft") and kept when it starts uppercase, where the hyphen is a
    real compound ("Surveillance-" + "Broadcast" → "Surveillance-Broadcast").
    """
    joined_text = ""
    for line in text_lines:
        line = line.strip()
        if not line:
            continue
        if not joined_text:
            joined_text = line
        elif joined_text.endswith("-"):
            if line[0].islower():
                joined_text = joined_text[:-1] + line
            else:
                joined_text = joined_text + line
        elif joined_text.endswith("—"):
            joined_text = joined_text + line
        else:
            joined_text = joined_text + " " + line
    return joined_text


def assemble_section_text(body_lines: list[str]) -> str:
    """
    Assemble body lines into section text, one paragraph per line.

    Lines that begin a top-level lettered paragraph — "(a) ...", "(b) ..." —
    start a new output paragraph; everything else joins the current one.
    """
    paragraphs: list[list[str]] = [[]]
    for line in body_lines:
        if TOP_LEVEL_PARAGRAPH_PATTERN.match(line):
            paragraphs.append([line])
        else:
            paragraphs[-1].append(line)
    assembled_paragraphs = [join_wrapped_lines(lines) for lines in paragraphs if lines]
    return "\n".join(paragraph for paragraph in assembled_paragraphs if paragraph)


def extract_regulation_lines(pdf_document: fitz.Document):
    """Yield (line_text, is_heading_line, is_appendix_start, page_number)."""
    for page_index, pdf_page in enumerate(pdf_document):
        for text_block in pdf_page.get_text("dict")["blocks"]:
            for text_line in text_block.get("lines", []):
                # Appendix headings are small caps — only the raw text of
                # every span, sizes included, reconstructs the full words.
                # Both the all-caps glyphs and a sub-7.5pt span must be
                # present, so inline cross-references can never match
                raw_line_text = "".join(span["text"] for span in text_line["spans"])
                has_small_caps_span = any(
                    span["size"] < SMALL_CAPS_SPAN_MAX_SIZE
                    and span["font"].startswith(BODY_FONT_PREFIX)
                    for span in text_line["spans"]
                )
                is_appendix_start = has_small_caps_span and bool(
                    APPENDIX_HEADING_PATTERN.search(raw_line_text)
                )

                regulation_spans = [
                    span for span in text_line["spans"] if is_regulation_text_span(span)
                ]
                if not regulation_spans and not is_appendix_start:
                    continue
                line_text = normalize_whitespace(
                    " ".join(span["text"] for span in regulation_spans)
                )
                if not line_text and not is_appendix_start:
                    continue
                is_heading_line = bool(regulation_spans) and all(
                    span["font"] == SECTION_HEADING_FONT for span in regulation_spans
                )
                yield line_text, is_heading_line, is_appendix_start, page_index + 1


def extract_corpus_version(pdf_document: fitz.Document) -> str:
    """Read the edition date from the running header as an ISO date."""
    for pdf_page in pdf_document:
        date_match = EDITION_DATE_PATTERN.search(pdf_page.get_text())
        if date_match:
            month, day, two_digit_year = date_match.groups()
            return f"20{two_digit_year}-{int(month):02d}-{int(day):02d}"
    return "unknown"


def parse_cfr_part_pdf(
    pdf_file_path: str, document_name: str, part_number: str
) -> ParsedRegulationDocument:
    """
    Parse one GPO-printed CFR part PDF into structured regulation sections.

    Only sections belonging to the requested part are kept — these PDFs
    include the tail of the preceding part and trailing appendix material.
    Bold headings that are not sections of the part (subpart titles, SFARs,
    appendices) are recorded in skipped_headings so nothing fails silently.
    """
    pdf_document = fitz.open(pdf_file_path)
    parsed_document = ParsedRegulationDocument(
        document_name=document_name,
        part_number=part_number,
        corpus_version=extract_corpus_version(pdf_document),
    )

    section_number_prefix = f"{part_number}."
    current_section: RegulationSection | None = None
    current_body_lines: list[str] = []
    reading_heading_continuation = False

    def finalize_current_section():
        if current_section is not None:
            current_section.section_text = assemble_section_text(current_body_lines)
            parsed_document.sections.append(current_section)

    for line_text, is_heading_line, is_appendix_start, page_number in extract_regulation_lines(
        pdf_document
    ):
        # Appendices trail the part and are out of scope for section chunks —
        # stop here so appendix text never bleeds into the last section.
        # (The table of contents also mentions appendices, but it appears
        # before any section has been parsed, so it never trips this.)
        if is_appendix_start and (parsed_document.sections or current_section is not None):
            parsed_document.skipped_headings.append(
                f"p.{page_number}: appendix material begins — section parsing stopped"
            )
            break

        if is_heading_line:
            heading_match = SECTION_HEADING_PATTERN.match(line_text)

            # Sections print in strictly increasing numeric order, so a
            # "heading" whose number is not greater than the current
            # section's is really a wrapped title fragment — e.g. the
            # title of § 91.311 ("Towing: Other than under § 91.309.")
            # breaks onto a second bold line that looks like a heading
            heading_is_out_of_order = (
                heading_match is not None
                and current_section is not None
                and heading_match.group(1).startswith(section_number_prefix)
                and section_number_sort_key(heading_match.group(1))
                <= section_number_sort_key(current_section.section_number)
            )
            if heading_is_out_of_order:
                if reading_heading_continuation:
                    current_section.section_title = normalize_whitespace(
                        f"{current_section.section_title} {line_text}"
                    )
                else:
                    parsed_document.skipped_headings.append(
                        f"p.{page_number}: out-of-order heading kept out: {line_text}"
                    )
                continue

            if heading_match and heading_match.group(1).startswith(section_number_prefix):
                finalize_current_section()
                current_section = RegulationSection(
                    section_number=heading_match.group(1),
                    section_title=heading_match.group(2).strip(),
                    section_text="",
                    page_number=page_number,
                )
                current_body_lines = []
                reading_heading_continuation = True
            elif reading_heading_continuation and current_section is not None and not heading_match:
                # A long section title wrapped onto another bold line
                current_section.section_title = normalize_whitespace(
                    f"{current_section.section_title} {line_text}"
                )
            else:
                # A heading that isn't a section of this part (foreign part
                # like § 68.1, subpart title, [Reserved] range) closes the
                # current section — body text after it must never be
                # appended to the section that came before
                finalize_current_section()
                current_section = None
                current_body_lines = []
                parsed_document.skipped_headings.append(f"p.{page_number}: {line_text}")
                reading_heading_continuation = False
        else:
            if current_section is not None:
                current_body_lines.append(line_text)
            else:
                # Text outside any section of this part — the part preamble,
                # SFARs, or a foreign part's body — is out of scope; counted
                # so the drop is visible, not silent
                parsed_document.out_of_scope_lines_dropped += 1
            reading_heading_continuation = False

    finalize_current_section()
    pdf_document.close()

    # Titles print with a trailing period; the title itself doesn't need it
    for section in parsed_document.sections:
        section.section_title = section.section_title.rstrip(".").strip()

    return parsed_document
