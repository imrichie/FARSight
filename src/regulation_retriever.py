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

    question_embedding = (
        build_embeddings_client().embed(input=[user_question]).data[0].embedding
    )
    question_vector_query = VectorizedQuery(
        vector=question_embedding,
        k_nearest_neighbors=chunks_to_retrieve,
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
