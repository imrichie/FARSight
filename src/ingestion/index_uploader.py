# index_uploader.py
# Generates embeddings for regulation chunks and uploads them
# to the Azure AI Search index.


def upload_regulation_chunks_to_index(regulation_chunks: list[dict]) -> None:
    """
    Generate an embedding vector for each chunk and upload all documents
    to the Azure AI Search index.

    The index must already exist with the correct schema before calling this.
    This function is idempotent — re-running it will overwrite existing
    documents with matching chunk_ids rather than creating duplicates.

    Args:
        regulation_chunks: List of chunk dicts produced by pdf_chunker.py.
    """
    raise NotImplementedError
