# test_regulation_retriever.py
# Unit tests for retrieve_relevant_regulation_chunks: the empty-query
# guard and result-shaping logic. Both Azure clients are mocked — no
# network calls, no credentials required.

from unittest.mock import MagicMock, patch

from src.regulation_retriever import (
    DEFAULT_VECTOR_CANDIDATE_COUNT,
    RETRIEVED_CHUNK_FIELDS,
    retrieve_relevant_regulation_chunks,
)


def _fake_search_result(section_number="91.17"):
    return {
        "id": f"14-cfr-part-91_{section_number.replace('.', '-')}",
        "document": "14 CFR Part 91",
        "part_number": "91",
        "section_number": section_number,
        "section_title": "Alcohol or drugs",
        "chunk_text": f"§ {section_number} Alcohol or drugs\nNo person may act...",
        "page_number": 42,
        "corpus_version": "2024-01-01",
        "@search.score": 3.14,
    }


def test_empty_query_returns_empty_list():
    assert retrieve_relevant_regulation_chunks("") == []


def test_whitespace_only_query_returns_empty_list():
    assert retrieve_relevant_regulation_chunks("   ") == []


def test_returned_chunk_contains_all_required_fields():
    mock_embed = MagicMock()
    mock_embed.embed.return_value.data[0].embedding = [0.1] * 1536
    mock_search = MagicMock()
    mock_search.search.return_value = [_fake_search_result()]

    with (
        patch("src.regulation_retriever.build_embeddings_client", return_value=mock_embed),
        patch("src.regulation_retriever.build_search_client", return_value=mock_search),
    ):
        chunks = retrieve_relevant_regulation_chunks("How long after drinking can I fly?")

    assert len(chunks) == 1
    for field in RETRIEVED_CHUNK_FIELDS:
        assert field in chunks[0], f"missing field: {field}"
    assert "search_score" in chunks[0]


def test_search_score_copied_from_index_score():
    mock_embed = MagicMock()
    mock_embed.embed.return_value.data[0].embedding = [0.0] * 1536
    mock_search = MagicMock()
    mock_search.search.return_value = [_fake_search_result()]

    with (
        patch("src.regulation_retriever.build_embeddings_client", return_value=mock_embed),
        patch("src.regulation_retriever.build_search_client", return_value=mock_search),
    ):
        chunks = retrieve_relevant_regulation_chunks("alcohol limit for pilots")

    assert chunks[0]["search_score"] == 3.14


def test_vector_candidate_pool_is_wider_than_returned_chunk_count():
    mock_embed = MagicMock()
    mock_embed.embed.return_value.data[0].embedding = [0.0] * 1536
    mock_search = MagicMock()
    mock_search.search.return_value = [_fake_search_result()]

    with (
        patch("src.regulation_retriever.build_embeddings_client", return_value=mock_embed),
        patch("src.regulation_retriever.build_search_client", return_value=mock_search),
    ):
        retrieve_relevant_regulation_chunks("What instruments are required for day VFR?")

    search_call = mock_search.search.call_args.kwargs
    vector_query = search_call["vector_queries"][0]
    assert vector_query.k_nearest_neighbors == DEFAULT_VECTOR_CANDIDATE_COUNT
    assert search_call["top"] == 5


def test_vector_candidate_pool_never_smaller_than_requested_chunk_count():
    mock_embed = MagicMock()
    mock_embed.embed.return_value.data[0].embedding = [0.0] * 1536
    mock_search = MagicMock()
    mock_search.search.return_value = [_fake_search_result()]

    with (
        patch("src.regulation_retriever.build_embeddings_client", return_value=mock_embed),
        patch("src.regulation_retriever.build_search_client", return_value=mock_search),
    ):
        retrieve_relevant_regulation_chunks(
            "What instruments are required for day VFR?",
            chunks_to_retrieve=30,
        )

    search_call = mock_search.search.call_args.kwargs
    vector_query = search_call["vector_queries"][0]
    assert vector_query.k_nearest_neighbors == 30
    assert search_call["top"] == 30


def test_no_search_results_returns_empty_list():
    mock_embed = MagicMock()
    mock_embed.embed.return_value.data[0].embedding = [0.0] * 1536
    mock_search = MagicMock()
    mock_search.search.return_value = []

    with (
        patch("src.regulation_retriever.build_embeddings_client", return_value=mock_embed),
        patch("src.regulation_retriever.build_search_client", return_value=mock_search),
    ):
        chunks = retrieve_relevant_regulation_chunks("something obscure")

    assert chunks == []
