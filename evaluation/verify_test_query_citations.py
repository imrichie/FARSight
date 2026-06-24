# verify_test_query_citations.py
# Verifies that every in-scope expected citation in the evaluation set
# resolves to source chunks in the local processed corpus. This is a
# local corpus check only; live index-side verification is deferred to
# the evaluation runner.
#
# Run from the repo root:  python -m evaluation.verify_test_query_citations

import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from textwrap import indent

TEST_QUERY_FILE = Path("evaluation/test_queries.jsonl")
CHUNK_FILE = Path("data/processed/chunks.json")


@dataclass(frozen=True)
class CitationReference:
    document: str
    section_number: str


@dataclass(frozen=True)
class UnresolvedCitation:
    query_id: str
    expected_citation: str
    reference: CitationReference | None
    reason: str


def load_test_queries(test_query_file: Path = TEST_QUERY_FILE) -> list[dict]:
    return [
        json.loads(line)
        for line in test_query_file.read_text().splitlines()
        if line.strip()
    ]


def load_chunks(chunk_file: Path = CHUNK_FILE) -> list[dict]:
    return json.loads(chunk_file.read_text())


def part_document_for_section(section_number: str) -> str:
    part_number = section_number.split(".", 1)[0]
    return f"14 CFR Part {part_number}"


def dedupe_references(references: list[CitationReference]) -> list[CitationReference]:
    seen = set()
    deduped_references = []
    for reference in references:
        if reference in seen:
            continue
        seen.add(reference)
        deduped_references.append(reference)
    return deduped_references


def parse_citation_references(expected_citation: str | None) -> list[CitationReference]:
    if expected_citation is None:
        return []

    references: list[CitationReference] = []

    for cfr_match in re.finditer(r"14 CFR §§?\s*([^()]*)", expected_citation):
        cfr_citation_text = cfr_match.group(1)
        for section_number in re.findall(r"\d+\.\d+", cfr_citation_text):
            references.append(
                CitationReference(
                    document=part_document_for_section(section_number),
                    section_number=section_number,
                )
            )

    if "AIM" in expected_citation:
        for section_number in re.findall(r"\d+-\d+-\d+", expected_citation):
            references.append(
                CitationReference(document="AIM", section_number=section_number)
            )

    return dedupe_references(references)


def build_chunk_lookup(chunks: list[dict]) -> dict[tuple[str, str], list[dict]]:
    chunks_by_citation = defaultdict(list)
    for chunk in chunks:
        chunks_by_citation[(chunk["document"], chunk["section_number"])].append(chunk)
    return dict(chunks_by_citation)


def find_unresolved_citations(
    test_queries: list[dict], chunks: list[dict]
) -> list[UnresolvedCitation]:
    chunks_by_citation = build_chunk_lookup(chunks)
    unresolved_citations = []

    for query in test_queries:
        if query["question_type"] == "out_of_scope":
            continue

        citation_references = parse_citation_references(query["expected_citation"])
        if not citation_references:
            unresolved_citations.append(
                UnresolvedCitation(
                    query_id=query["id"],
                    expected_citation=query["expected_citation"],
                    reference=None,
                    reason="no parseable citation references",
                )
            )
            continue

        for reference in citation_references:
            if not chunks_by_citation.get((reference.document, reference.section_number)):
                unresolved_citations.append(
                    UnresolvedCitation(
                        query_id=query["id"],
                        expected_citation=query["expected_citation"],
                        reference=reference,
                        reason="reference not found in chunks",
                    )
                )

    return unresolved_citations


def print_fact_review(test_queries: list[dict], chunks: list[dict]) -> None:
    chunks_by_citation = build_chunk_lookup(chunks)

    print("\n=== key fact review aid ===")
    print("Fact presence is for human review only; it is not scored here.\n")

    for query in test_queries:
        if query["question_type"] == "out_of_scope":
            continue

        print(f"--- {query['id']} {query['question']}")
        print(f"expected citation: {query['expected_citation']}")
        print("expected key facts:")
        for key_fact in query["expected_key_facts"]:
            print(f"  - {key_fact}")

        for reference in parse_citation_references(query["expected_citation"]):
            resolved_chunks = chunks_by_citation.get(
                (reference.document, reference.section_number), []
            )
            for chunk in resolved_chunks:
                print(f"\nresolved chunk: {reference.document} {reference.section_number}")
                print(indent(chunk["chunk_text"], "  "))
        print()


def main() -> None:
    test_queries = load_test_queries()
    chunks = load_chunks()

    in_scope_count = sum(
        1 for query in test_queries if query["question_type"] == "in_scope"
    )
    out_of_scope_count = len(test_queries) - in_scope_count
    unresolved_citations = find_unresolved_citations(test_queries, chunks)

    print("=== citation verification summary ===")
    print(f"test queries:       {len(test_queries)}")
    print(f"in-scope queries:   {in_scope_count}")
    print(f"out-of-scope rows:  {out_of_scope_count}")
    print(f"chunks loaded:      {len(chunks)}")
    print("index check:        deferred to the evaluation runner")

    if unresolved_citations:
        print(f"\nFAIL — unresolved citations ({len(unresolved_citations)}):")
        for unresolved in unresolved_citations:
            if unresolved.reference is None:
                print(
                    f"  {unresolved.query_id}: {unresolved.expected_citation} -> "
                    f"{unresolved.reason}"
                )
            else:
                print(
                    f"  {unresolved.query_id}: {unresolved.expected_citation} -> "
                    f"{unresolved.reference.document} {unresolved.reference.section_number} "
                    f"({unresolved.reason})"
                )
        sys.exit(1)

    print("\nPASS — all expected in-scope citations resolve to local chunks")
    print_fact_review(test_queries, chunks)


if __name__ == "__main__":
    main()
