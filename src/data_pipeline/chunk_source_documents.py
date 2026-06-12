# chunk_source_documents.py
# Entry point for the chunking step of the data pipeline. Parses each
# source PDF into sections, chunks them, writes the result to
# data/processed/chunks.json, and prints a summary so parsing problems
# are visible immediately — never silent.
#
# Run from the repo root:  python -m src.data_pipeline.chunk_source_documents

import json
import sys
from collections import Counter
from pathlib import Path

from src.data_pipeline.aim_parser import parse_aim_pdf
from src.data_pipeline.regulation_parser import parse_cfr_part_pdf
from src.data_pipeline.section_chunker import chunk_parsed_document

CHUNK_OUTPUT_FILE = Path("data/processed/chunks.json")

CFR_SOURCE_DOCUMENTS = [
    {
        "pdf_file_path": "data/14-CFR-Part-61.pdf",
        "document_name": "14 CFR Part 61",
        "part_number": "61",
    },
    {
        "pdf_file_path": "data/14-CFR-Part-67.pdf",
        "document_name": "14 CFR Part 67",
        "part_number": "67",
    },
    {
        "pdf_file_path": "data/14-CFR-Part-71.pdf",
        "document_name": "14 CFR Part 71",
        "part_number": "71",
    },
    {
        "pdf_file_path": "data/14-CFR-Part-91.pdf",
        "document_name": "14 CFR Part 91",
        "part_number": "91",
    },
]

AIM_PDF_FILE_PATH = "data/AIM.pdf"


def print_document_summary(document_name, document_chunks, skipped_headings, warnings, out_of_scope_lines_dropped):
    chunk_lengths = [len(chunk["chunk_text"]) for chunk in document_chunks]
    print(f"\n=== {document_name} ===")
    print(f"chunks: {len(document_chunks)}")
    print(
        f"chunk length — avg: {sum(chunk_lengths) // len(chunk_lengths)}, "
        f"min: {min(chunk_lengths)}, max: {max(chunk_lengths)}"
    )
    if out_of_scope_lines_dropped:
        print(f"out-of-scope body lines dropped (preamble, SFARs, foreign parts): {out_of_scope_lines_dropped}")

    if warnings:
        print(f"\nchunking warnings ({len(warnings)}):")
        for warning in warnings:
            print(f"  ⚠ {warning}")

    if skipped_headings:
        print(f"\nskipped headings — not sections of this part ({len(skipped_headings)}):")
        for skipped_heading in skipped_headings:
            print(f"  • {skipped_heading}")


def main():
    parsed_documents = [
        parse_cfr_part_pdf(
            source_document["pdf_file_path"],
            source_document["document_name"],
            source_document["part_number"],
        )
        for source_document in CFR_SOURCE_DOCUMENTS
    ]
    parsed_documents.append(parse_aim_pdf(AIM_PDF_FILE_PATH))

    all_chunks = []
    for parsed_document in parsed_documents:
        document_chunks, chunking_warnings = chunk_parsed_document(parsed_document)
        all_chunks.extend(document_chunks)
        print(f"corpus version for {parsed_document.document_name}: {parsed_document.corpus_version}")
        print_document_summary(
            parsed_document.document_name,
            document_chunks,
            parsed_document.skipped_headings,
            chunking_warnings,
            parsed_document.out_of_scope_lines_dropped,
        )

    # Duplicate ids would silently overwrite each other at upload time —
    # fail loudly here instead, before anything is written
    duplicate_chunk_ids = [
        chunk_id for chunk_id, count in Counter(c["id"] for c in all_chunks).items() if count > 1
    ]
    if duplicate_chunk_ids:
        print(f"\n✗ duplicate chunk ids found ({len(duplicate_chunk_ids)}):")
        for duplicate_id in duplicate_chunk_ids:
            print(f"  ✗ {duplicate_id}")
        print("chunk file NOT written — fix the parser before persisting")
        sys.exit(1)

    CHUNK_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHUNK_OUTPUT_FILE.write_text(json.dumps(all_chunks, indent=2, ensure_ascii=False))
    print(f"\nwrote {len(all_chunks)} chunks to {CHUNK_OUTPUT_FILE} — all chunk ids unique")


if __name__ == "__main__":
    main()
