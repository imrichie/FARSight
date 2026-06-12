# search_index_manager.py
# Creates (or updates) the Azure AI Search index that holds the regulation
# chunks. The schema mirrors the chunk fields written by
# chunk_source_documents.py, plus the vector field the persistence step
# will fill — together these enable hybrid (keyword + vector) retrieval.
#
# Run from the repo root:  python -m src.data_pipeline.search_index_manager

import os

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from dotenv import load_dotenv

# Must match the output dimensions of text-embedding-3-small
EMBEDDING_VECTOR_DIMENSIONS = 1536

VECTOR_ALGORITHM_NAME = "farsight-hnsw"
VECTOR_PROFILE_NAME = "farsight-vector-profile"

DEFAULT_INDEX_NAME = "farsight-regulations"


def build_regulations_index_definition(index_name: str) -> SearchIndex:
    """
    Define the index schema for regulation chunks.

    Field roles:
        - chunk_text and section_title are searchable for keyword queries
        - document is searchable and filterable — questions can be scoped
          to one source document at retrieval time
        - the remaining metadata fields are filterable for citation
          assembly and corpus-version checks
        - embedding_vector carries the chunk embedding for vector search
    """
    index_fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="chunk_text", type=SearchFieldDataType.String),
        SearchableField(name="document", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="part_number", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="section_number", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="section_title", type=SearchFieldDataType.String),
        SimpleField(name="page_number", type=SearchFieldDataType.Int32, filterable=True),
        SimpleField(name="corpus_version", type=SearchFieldDataType.String, filterable=True),
        SearchField(
            name="embedding_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            vector_search_dimensions=EMBEDDING_VECTOR_DIMENSIONS,
            vector_search_profile_name=VECTOR_PROFILE_NAME,
        ),
    ]

    vector_search_configuration = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name=VECTOR_ALGORITHM_NAME)],
        profiles=[
            VectorSearchProfile(
                name=VECTOR_PROFILE_NAME,
                algorithm_configuration_name=VECTOR_ALGORITHM_NAME,
            )
        ],
    )

    return SearchIndex(
        name=index_name,
        fields=index_fields,
        vector_search=vector_search_configuration,
    )


def create_or_update_regulations_search_index() -> None:
    """
    Create the regulations index, or update its definition if it already
    exists — idempotent like the Bicep templates, safe to re-run.
    """
    load_dotenv()
    search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
    search_admin_key = os.environ["AZURE_SEARCH_ADMIN_KEY"]
    index_name = os.environ.get("AZURE_SEARCH_INDEX_NAME", DEFAULT_INDEX_NAME)

    index_client = SearchIndexClient(
        endpoint=search_endpoint, credential=AzureKeyCredential(search_admin_key)
    )
    index_definition = build_regulations_index_definition(index_name)
    created_index = index_client.create_or_update_index(index_definition)

    print(f"index ready: {created_index.name}")
    for field in created_index.fields:
        field_traits = []
        if field.key:
            field_traits.append("key")
        if field.searchable:
            field_traits.append("searchable")
        if field.filterable:
            field_traits.append("filterable")
        if field.vector_search_dimensions:
            field_traits.append(f"vector[{field.vector_search_dimensions}]")
        print(f"  {field.name:<18} {field.type:<30} {', '.join(field_traits)}")


if __name__ == "__main__":
    create_or_update_regulations_search_index()
