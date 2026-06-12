# validate_index.py
# Read-only validation gate for the persisted index: compares the
# farsight-regulations index against data/processed/chunks.json (the
# source of truth) and fails loudly on any discrepancy. Exits non-zero
# on failure so it can run in CI as a pipeline gate.
#
# Documents are verified by exact key lookup rather than full-scan
# search — enumeration proved unreliable on a service at its storage
# quota, while keyed reads are exact.
#
# Run from the repo root:  python3 -m src.data_pipeline.validate_index

import json
import sys
from pathlib import Path

from azure.core.exceptions import ResourceNotFoundError
from dotenv import load_dotenv

from src.data_pipeline.chunk_persister import build_search_client

CHUNK_INPUT_FILE = Path("data/processed/chunks.json")

# Sections whose presence and content we always confirm individually
SPOT_CHECK_CHUNK_IDS = [
    "14-cfr-part-91_91-17",
    "14-cfr-part-91_91-215",
    "14-cfr-part-91_91-309",
    "14-cfr-part-91_91-311",
    "aim_4-3-13",
]


def check_document_count(search_client, expected_chunk_count) -> tuple[bool, str]:
    index_document_count = search_client.get_document_count()
    passed = index_document_count == expected_chunk_count
    return passed, f"index has {index_document_count}, chunks.json has {expected_chunk_count}"


def check_ids_and_content(search_client, regulation_chunks) -> tuple[bool, bool, str, str]:
    """
    One keyed pass over every chunk id covering two checks: the id exists
    in the index, and the indexed document has real content.
    """
    missing_chunk_ids: list[str] = []
    empty_content_ids: list[str] = []

    for position, chunk in enumerate(regulation_chunks):
        try:
            indexed_document = search_client.get_document(
                key=chunk["id"], selected_fields=["id", "chunk_text", "section_number"]
            )
        except ResourceNotFoundError:
            missing_chunk_ids.append(chunk["id"])
            continue

        document_text = (indexed_document.get("chunk_text") or "").strip()
        document_section_number = (indexed_document.get("section_number") or "").strip()
        if not document_text or not document_section_number:
            empty_content_ids.append(chunk["id"])

        if (position + 1) % 500 == 0:
            print(f"  ...checked {position + 1}/{len(regulation_chunks)} ids", flush=True)

    missing_detail = (
        f"{len(missing_chunk_ids)} missing: {', '.join(missing_chunk_ids[:10])}"
        if missing_chunk_ids
        else "every chunk id present in the index"
    )
    empty_detail = (
        f"{len(empty_content_ids)} with empty text or section number: "
        f"{', '.join(empty_content_ids[:10])}"
        if empty_content_ids
        else "no empty chunk_text or missing section_number"
    )
    return not missing_chunk_ids, not empty_content_ids, missing_detail, empty_detail


def check_known_sections(search_client) -> tuple[bool, str]:
    """Fetch a few well-known sections and confirm title and body content."""
    spot_check_failures: list[str] = []
    for chunk_id in SPOT_CHECK_CHUNK_IDS:
        try:
            indexed_document = search_client.get_document(
                key=chunk_id, selected_fields=["section_title", "chunk_text"]
            )
        except ResourceNotFoundError:
            spot_check_failures.append(f"{chunk_id}: not found")
            continue

        section_title = (indexed_document.get("section_title") or "").strip()
        chunk_text_lines = (indexed_document.get("chunk_text") or "").strip().split("\n")
        body_beyond_header = "\n".join(chunk_text_lines[1:]).strip()
        if not section_title:
            spot_check_failures.append(f"{chunk_id}: empty section title")
        if not body_beyond_header:
            spot_check_failures.append(f"{chunk_id}: no body beyond the header line")

    detail = (
        "; ".join(spot_check_failures)
        if spot_check_failures
        else f"all {len(SPOT_CHECK_CHUNK_IDS)} known sections have title and body"
    )
    return not spot_check_failures, detail


def main():
    load_dotenv()
    regulation_chunks = json.loads(CHUNK_INPUT_FILE.read_text())
    search_client = build_search_client()

    print(f"validating index against {CHUNK_INPUT_FILE} ({len(regulation_chunks)} chunks)\n", flush=True)

    count_passed, count_detail = check_document_count(search_client, len(regulation_chunks))
    ids_passed, content_passed, ids_detail, content_detail = check_ids_and_content(
        search_client, regulation_chunks
    )
    spot_passed, spot_detail = check_known_sections(search_client)

    validation_results = [
        ("count match", count_passed, count_detail),
        ("no missing ids", ids_passed, ids_detail),
        ("no empty content", content_passed, content_detail),
        ("known-section spot checks", spot_passed, spot_detail),
    ]

    print("\n=== index validation summary ===")
    for check_name, check_passed, check_detail in validation_results:
        status_mark = "✓" if check_passed else "✗"
        print(f"{status_mark} {check_name}: {check_detail}")

    all_checks_passed = all(passed for _, passed, _ in validation_results)
    print(f"\n{'PASS' if all_checks_passed else 'FAIL'}")
    sys.exit(0 if all_checks_passed else 1)


if __name__ == "__main__":
    main()
