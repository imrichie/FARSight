# chunk_persister.py
# Persistence step of the data pipeline: reads the chunk file, embeds
# each chunk's text with the Azure OpenAI embedding deployment, and
# uploads chunk + vector + metadata to the Azure AI Search index.
#
# Each batch goes end to end — embed, upload, report — so progress lands
# in the index incrementally and a partial run persists partial results.
# Uploads are upserts keyed on the stable chunk id, so re-running after
# a failure overwrites cleanly — no duplicates, no cleanup.
#
# Run from the repo root:  python3 -m src.data_pipeline.chunk_persister

import json
import os
import time
from pathlib import Path

from azure.ai.inference import EmbeddingsClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv

CHUNK_INPUT_FILE = Path("data/processed/chunks.json")

# Batches are sized by estimated tokens, not chunk count: the embedding
# deployment is provisioned at 10K tokens/minute, and a batch that fits
# inside the per-minute quota avoids silent 429 retry loops. Characters
# divided by 4 approximates tokens for this corpus.
EMBEDDING_BATCH_MAX_CHUNKS = 32
EMBEDDING_BATCH_MAX_CHARS = 24_000  # ≈ 6K tokens
ESTIMATED_CHARS_PER_TOKEN = 4

# A run that can't upload shouldn't keep paying to embed — stop after
# this many upload failures in a row (e.g. a storage quota wall)
CONSECUTIVE_UPLOAD_FAILURE_LIMIT = 3


def build_embeddings_client() -> EmbeddingsClient:
    openai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
    embedding_deployment = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]
    return EmbeddingsClient(
        endpoint=f"{openai_endpoint}/openai/deployments/{embedding_deployment}",
        credential=AzureKeyCredential(os.environ["AZURE_OPENAI_API_KEY"]),
    )


def build_search_client() -> SearchClient:
    return SearchClient(
        endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
        index_name=os.environ["AZURE_SEARCH_INDEX_NAME"],
        credential=AzureKeyCredential(os.environ["AZURE_SEARCH_ADMIN_KEY"]),
    )


def build_token_budgeted_batches(regulation_chunks: list[dict]) -> list[list[dict]]:
    """Group chunks into batches capped by count and by estimated tokens."""
    batches: list[list[dict]] = []
    current_batch: list[dict] = []
    current_batch_chars = 0

    for chunk in regulation_chunks:
        chunk_chars = len(chunk["chunk_text"])
        batch_is_full = current_batch and (
            len(current_batch) >= EMBEDDING_BATCH_MAX_CHUNKS
            or current_batch_chars + chunk_chars > EMBEDDING_BATCH_MAX_CHARS
        )
        if batch_is_full:
            batches.append(current_batch)
            current_batch = []
            current_batch_chars = 0
        current_batch.append(chunk)
        current_batch_chars += chunk_chars

    if current_batch:
        batches.append(current_batch)
    return batches


def embed_chunk_batch(
    chunk_batch: list[dict], embeddings_client: EmbeddingsClient
) -> tuple[list[dict], int]:
    """Embed one batch; returns (chunks with vectors attached, tokens used)."""
    embedding_response = embeddings_client.embed(
        input=[chunk["chunk_text"] for chunk in chunk_batch]
    )
    # Pair results by the API's own index field rather than assuming order
    embeddings_by_index = {item.index: item.embedding for item in embedding_response.data}
    embedded_chunks = [
        {**chunk, "embedding_vector": embeddings_by_index[position]}
        for position, chunk in enumerate(chunk_batch)
    ]
    return embedded_chunks, embedding_response.usage.total_tokens


def upload_chunk_batch(
    embedded_chunks: list[dict], search_client: SearchClient
) -> tuple[int, list[str]]:
    """Upsert one batch into the index; returns (uploaded count, failures)."""
    uploaded_document_count = 0
    upload_failures: list[str] = []
    for indexing_result in search_client.merge_or_upload_documents(embedded_chunks):
        if indexing_result.succeeded:
            uploaded_document_count += 1
        else:
            upload_failures.append(f"{indexing_result.key}: {indexing_result.error_message}")
    return uploaded_document_count, upload_failures


def main():
    load_dotenv()
    run_started_at = time.monotonic()

    regulation_chunks = json.loads(CHUNK_INPUT_FILE.read_text())
    chunk_batches = build_token_budgeted_batches(regulation_chunks)
    estimated_total_tokens = sum(len(c["chunk_text"]) for c in regulation_chunks) // ESTIMATED_CHARS_PER_TOKEN

    print(f"chunks loaded:    {len(regulation_chunks)} from {CHUNK_INPUT_FILE}", flush=True)
    print(f"uploading to:     {os.environ['AZURE_SEARCH_INDEX_NAME']} @ {os.environ['AZURE_SEARCH_ENDPOINT']}", flush=True)
    print(f"embedding via:    {os.environ['AZURE_OPENAI_EMBEDDING_DEPLOYMENT']}", flush=True)
    print(f"batches:          {len(chunk_batches)} (≈{estimated_total_tokens:,} tokens total — "
          f"expect ~{estimated_total_tokens // 10_000} min at 10K tokens/min capacity)\n", flush=True)

    embeddings_client = build_embeddings_client()
    search_client = build_search_client()

    chunks_completed = 0
    total_uploaded = 0
    total_tokens_embedded = 0
    run_failures: list[str] = []
    consecutive_upload_failures = 0

    for batch_number, chunk_batch in enumerate(chunk_batches, start=1):
        try:
            embedded_chunks, batch_tokens = embed_chunk_batch(chunk_batch, embeddings_client)
            total_tokens_embedded += batch_tokens
        except Exception as embedding_error:
            failed_ids = ", ".join(chunk["id"] for chunk in chunk_batch)
            run_failures.append(f"embedding batch {batch_number} ({failed_ids}): {embedding_error}")
            print(f"batch {batch_number}/{len(chunk_batches)}  ✗ embedding failed — continuing", flush=True)
            continue

        try:
            uploaded_count, upload_failures = upload_chunk_batch(embedded_chunks, search_client)
            total_uploaded += uploaded_count
            run_failures.extend(upload_failures)
            consecutive_upload_failures = 0
        except Exception as upload_error:
            failed_ids = ", ".join(chunk["id"] for chunk in chunk_batch)
            run_failures.append(f"upload batch {batch_number} ({failed_ids}): {upload_error}")
            consecutive_upload_failures += 1
            print(f"batch {batch_number}/{len(chunk_batches)}  ✗ upload failed — continuing", flush=True)
            if consecutive_upload_failures >= CONSECUTIVE_UPLOAD_FAILURE_LIMIT:
                print(
                    f"\n✗ {consecutive_upload_failures} upload failures in a row — "
                    "aborting run instead of paying to embed chunks that can't be "
                    "uploaded. Re-running after the cause is fixed is safe (upserts).",
                    flush=True,
                )
                break
            continue

        chunks_completed += len(chunk_batch)
        elapsed_seconds = time.monotonic() - run_started_at
        print(
            f"batch {batch_number}/{len(chunk_batches)}  "
            f"{chunks_completed}/{len(regulation_chunks)} chunks  "
            f"{total_tokens_embedded:,} tokens  "
            f"{elapsed_seconds:,.0f}s elapsed",
            flush=True,
        )

    # Give the index a moment, then read the count back as the final check
    time.sleep(3)
    index_document_count = search_client.get_document_count()
    elapsed_seconds = time.monotonic() - run_started_at

    print("\n=== persistence run summary ===", flush=True)
    print(f"chunks embedded:       {chunks_completed}")
    print(f"chunks uploaded:       {total_uploaded}")
    print(f"total tokens embedded: {total_tokens_embedded:,}")
    print(f"total time:            {elapsed_seconds:,.0f}s")
    print(f"index document count:  {index_document_count} (expected {len(regulation_chunks)})")

    if run_failures:
        print(f"\nfailures ({len(run_failures)}):")
        for failure_description in run_failures:
            print(f"  ✗ {failure_description}")
    else:
        print("\nno failures")


if __name__ == "__main__":
    main()
