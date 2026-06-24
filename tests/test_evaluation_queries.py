import json
from pathlib import Path

TEST_QUERY_FILE = Path("evaluation/test_queries.jsonl")

REQUIRED_FIELDS = {
    "id",
    "question",
    "expected_key_facts",
    "expected_citation",
    "question_type",
    "retrieval_type",
    "notes",
}

QUESTION_TYPES = {"in_scope", "out_of_scope"}
RETRIEVAL_TYPES = {"direct", "paraphrase", "synthesis", "trap", "refusal"}


def load_test_queries() -> list[dict]:
    return [
        json.loads(line)
        for line in TEST_QUERY_FILE.read_text().splitlines()
        if line.strip()
    ]


def test_test_query_file_has_expected_count_and_unique_ids():
    test_queries = load_test_queries()
    query_ids = [query["id"] for query in test_queries]

    assert len(test_queries) == 50
    assert len(query_ids) == len(set(query_ids))


def test_test_query_rows_all_have_the_same_required_shape():
    for query in load_test_queries():
        assert set(query) == REQUIRED_FIELDS
        assert query["question"].strip()
        assert query["question_type"] in QUESTION_TYPES
        assert query["retrieval_type"] in RETRIEVAL_TYPES
        assert isinstance(query["expected_key_facts"], list)
        assert query["expected_key_facts"]


def test_test_query_scope_counts_match_the_source_document():
    test_queries = load_test_queries()
    in_scope_queries = [
        query for query in test_queries if query["question_type"] == "in_scope"
    ]
    out_of_scope_queries = [
        query for query in test_queries if query["question_type"] == "out_of_scope"
    ]

    assert len(in_scope_queries) == 42
    assert len(out_of_scope_queries) == 8


def test_expected_citation_is_explicit_for_every_row():
    for query in load_test_queries():
        if query["question_type"] == "in_scope":
            assert isinstance(query["expected_citation"], str)
            assert query["expected_citation"].strip()
        else:
            assert query["expected_citation"] is None
            assert query["retrieval_type"] == "refusal"
