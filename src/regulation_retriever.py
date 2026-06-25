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

from azure.search.documents.models import VectorizedQuery
from dotenv import load_dotenv

from src.data_pipeline.chunk_persister import build_embeddings_client, build_search_client

DEFAULT_CHUNKS_TO_RETRIEVE = 5
DEFAULT_VECTOR_CANDIDATE_COUNT = 20

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

    search_results = build_search_client().search(
        search_text=user_question,
        vector_queries=[question_vector_query],
        select=RETRIEVED_CHUNK_FIELDS,
        top=chunks_to_retrieve,
    )

    retrieved_regulation_chunks = []
    for search_result in search_results:
        retrieved_chunk = {field: search_result[field] for field in RETRIEVED_CHUNK_FIELDS}
        retrieved_chunk["search_score"] = search_result["@search.score"]
        retrieved_regulation_chunks.append(retrieved_chunk)
    return retrieved_regulation_chunks


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
