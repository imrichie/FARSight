# regulation_retriever.py
# Retrieval layer: takes a plain English question and returns the most
# relevant regulation chunks from the farsight-regulations index.
#
# Retrieval is hybrid by design — the question embedding is matched
# against chunk vectors (semantic, handles paraphrased pilot phrasing)
# while the question text runs a BM25 keyword search over chunk_text
# (exact tokens like "91.215" and "ADS-B"). Azure AI Search fuses both
# rankings with Reciprocal Rank Fusion.
#
# The question is embedded with the same text-embedding-3-small
# deployment the chunks used — both must share one vector space for
# nearest-neighbor distance to mean anything.

import re

from azure.search.documents.models import VectorizedQuery
from dotenv import load_dotenv

from src.data_pipeline.chunk_persister import build_embeddings_client, build_search_client

DEFAULT_CHUNKS_TO_RETRIEVE = 5
DEFAULT_VECTOR_CANDIDATE_COUNT = DEFAULT_CHUNKS_TO_RETRIEVE
REPEATED_SECTION_EXPANSION_MINIMUM = 3
SECTION_EXPANSION_CHUNK_LIMIT = 30
QUESTION_TOKEN_STOPWORDS = {
    "about",
    "after",
    "aircraft",
    "airplane",
    "allowed",
    "and",
    "are",
    "can",
    "does",
    "for",
    "from",
    "have",
    "how",
    "into",
    "is",
    "legal",
    "legally",
    "must",
    "need",
    "required",
    "requirements",
    "the",
    "to",
    "what",
    "when",
    "where",
    "with",
}

# Every field the generation step and citation assembly will need later
RETRIEVED_CHUNK_FIELDS = [
    "id",
    "document",
    "part_number",
    "section_number",
    "section_title",
    "chunk_text",
    "page_number",
    "corpus_version",
]


def build_retrieved_chunk_from_search_result(search_result: dict) -> dict:
    retrieved_chunk = {field: search_result[field] for field in RETRIEVED_CHUNK_FIELDS}
    retrieved_chunk["search_score"] = search_result["@search.score"]
    return retrieved_chunk


def source_section_key(chunk: dict) -> tuple[str | None, str | None]:
    return chunk.get("document"), chunk.get("section_number")


def odata_string_literal(value: str) -> str:
    return value.replace("'", "''")


def important_question_tokens(user_question: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", user_question.lower())
        if len(token) > 2 and token not in QUESTION_TOKEN_STOPWORDS
    ]


def score_chunk_against_question(user_question: str, chunk: dict) -> int:
    question_tokens = important_question_tokens(user_question)
    candidate_text = " ".join(
        [chunk.get("section_title") or "", chunk.get("chunk_text") or ""]
    ).lower()
    candidate_tokens = re.findall(r"[a-z0-9]+", candidate_text)
    overlap_score = sum(candidate_tokens.count(token) for token in question_tokens)
    return overlap_score


def fetch_section_chunks(search_client, document: str, section_number: str) -> list[dict]:
    section_filter = (
        f"document eq '{odata_string_literal(document)}' "
        f"and section_number eq '{odata_string_literal(section_number)}'"
    )
    search_results = search_client.search(
        search_text="*",
        filter=section_filter,
        select=RETRIEVED_CHUNK_FIELDS,
        top=SECTION_EXPANSION_CHUNK_LIMIT,
    )
    return [
        build_retrieved_chunk_from_search_result(search_result)
        for search_result in search_results
    ]


def replace_repeated_sections_with_best_siblings(
    search_client,
    user_question: str,
    retrieved_regulation_chunks: list[dict],
) -> list[dict]:
    section_counts = {}
    for chunk in retrieved_regulation_chunks:
        section_key = source_section_key(chunk)
        section_counts[section_key] = section_counts.get(section_key, 0) + 1

    repeated_section_keys = {
        section_key
        for section_key, count in section_counts.items()
        if count >= REPEATED_SECTION_EXPANSION_MINIMUM and all(section_key)
    }
    if not repeated_section_keys:
        return retrieved_regulation_chunks

    ranked_siblings_by_section = {}
    for document, section_number in repeated_section_keys:
        section_chunks = fetch_section_chunks(search_client, document, section_number)
        ranked_siblings_by_section[(document, section_number)] = sorted(
            section_chunks,
            key=lambda chunk: (
                -score_chunk_against_question(user_question, chunk),
                chunk.get("id") or "",
            ),
        )

    selected_chunk_ids = set()
    sibling_offsets = {section_key: 0 for section_key in repeated_section_keys}
    adjusted_chunks = []

    for chunk in retrieved_regulation_chunks:
        section_key = source_section_key(chunk)
        replacement_chunk = chunk
        if section_key in ranked_siblings_by_section:
            sibling_candidates = ranked_siblings_by_section[section_key]
            sibling_offset = sibling_offsets[section_key]
            while (
                sibling_offset < len(sibling_candidates)
                and sibling_candidates[sibling_offset]["id"] in selected_chunk_ids
            ):
                sibling_offset += 1

            if sibling_offset < len(sibling_candidates):
                replacement_chunk = sibling_candidates[sibling_offset]
                sibling_offsets[section_key] = sibling_offset + 1

        if replacement_chunk["id"] in selected_chunk_ids:
            continue
        selected_chunk_ids.add(replacement_chunk["id"])
        adjusted_chunks.append(replacement_chunk)

    return adjusted_chunks


def retrieve_relevant_regulation_chunks(
    user_question: str, chunks_to_retrieve: int = DEFAULT_CHUNKS_TO_RETRIEVE
) -> list[dict]:
    """
    Run hybrid (vector + keyword) search for the user's question.

    Returns the top chunks as dicts carrying the retrieved fields plus
    search_score, ordered most relevant first. Returns an empty list
    when nothing matches.
    """
    load_dotenv()

    if not user_question or not user_question.strip():
        return []

    question_embedding = (
        build_embeddings_client().embed(input=[user_question]).data[0].embedding
    )
    vector_candidate_count = max(chunks_to_retrieve, DEFAULT_VECTOR_CANDIDATE_COUNT)
    question_vector_query = VectorizedQuery(
        vector=question_embedding,
        k_nearest_neighbors=vector_candidate_count,
        fields="embedding_vector",
    )

    search_client = build_search_client()
    search_results = search_client.search(
        search_text=user_question,
        vector_queries=[question_vector_query],
        select=RETRIEVED_CHUNK_FIELDS,
        top=chunks_to_retrieve,
    )

    retrieved_regulation_chunks = [
        build_retrieved_chunk_from_search_result(search_result)
        for search_result in search_results
    ]
    return replace_repeated_sections_with_best_siblings(
        search_client,
        user_question,
        retrieved_regulation_chunks,
    )


def print_retrieved_chunks(user_question: str, retrieved_regulation_chunks: list[dict]) -> None:
    """Readable terminal output for eyeballing retrieval quality."""
    print(f'question: "{user_question}"\n')
    if not retrieved_regulation_chunks:
        print("no chunks retrieved")
        return
    for rank, chunk in enumerate(retrieved_regulation_chunks, start=1):
        chunk_text_preview = " ".join(chunk["chunk_text"].split())[:200]
        print(f"#{rank}  score {chunk['search_score']:.4f}  "
              f"[{chunk['document']}] {chunk['section_number']} — {chunk['section_title']}")
        print(f"    {chunk_text_preview}\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print('usage: python3 -m src.regulation_retriever "your question here" [k]')
        sys.exit(1)
    question_from_terminal = sys.argv[1]
    requested_chunk_count = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_CHUNKS_TO_RETRIEVE
    print_retrieved_chunks(
        question_from_terminal,
        retrieve_relevant_regulation_chunks(question_from_terminal, requested_chunk_count),
    )
