# reset_index.py
# Deletes the regulations search index and waits until Azure confirms it
# is gone. This is the cleanup step before recreating the schema and
# uploading a fresh corpus when the free-tier storage ceiling is full.
#
# Run from the repo root:  python -m src.data_pipeline.reset_index

import os
import time

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents.indexes import SearchIndexClient
from dotenv import load_dotenv

from src.data_pipeline.search_index_manager import DEFAULT_INDEX_NAME

DELETE_CONFIRMATION_CHECKS = 30
DELETE_CONFIRMATION_SLEEP_SECONDS = 2


def build_search_index_client() -> SearchIndexClient:
    return SearchIndexClient(
        endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
        credential=AzureKeyCredential(os.environ["AZURE_SEARCH_ADMIN_KEY"]),
    )


def delete_index_if_present(index_client: SearchIndexClient, index_name: str) -> bool:
    try:
        index_client.delete_index(index_name)
    except ResourceNotFoundError:
        return False
    return True


def wait_until_index_is_absent(
    index_client: SearchIndexClient,
    index_name: str,
    checks: int = DELETE_CONFIRMATION_CHECKS,
    sleep_seconds: int = DELETE_CONFIRMATION_SLEEP_SECONDS,
) -> None:
    for check_number in range(checks):
        try:
            index_client.get_index(index_name)
        except ResourceNotFoundError:
            print(f"confirmed absent: {index_name}")
            return

        if check_number < checks - 1:
            time.sleep(sleep_seconds)

    raise TimeoutError(f"timed out waiting for {index_name} to be deleted")


def reset_regulations_search_index() -> None:
    load_dotenv()
    index_name = os.environ.get("AZURE_SEARCH_INDEX_NAME", DEFAULT_INDEX_NAME)
    index_client = build_search_index_client()

    if delete_index_if_present(index_client, index_name):
        print(f"delete requested: {index_name}")
    else:
        print(f"index already absent: {index_name}")

    wait_until_index_is_absent(index_client, index_name)


if __name__ == "__main__":
    reset_regulations_search_index()
