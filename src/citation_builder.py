# citation_builder.py
# Builds source citations from retrieved chunk metadata. The model can
# choose which chunk answers a question, but it never writes the citation.

REQUIRED_CITATION_FIELDS = [
    "document",
    "section_number",
    "section_title",
    "page_number",
    "corpus_version",
]


def build_unavailable_citation() -> dict:
    return {
        "available": False,
        "document": None,
        "section_number": None,
        "section_title": None,
        "page_number": None,
        "corpus_version": None,
    }


def metadata_value_is_present(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def build_citation_from_chunk(retrieved_chunk: dict) -> dict:
    if not all(
        metadata_value_is_present(retrieved_chunk.get(field))
        for field in REQUIRED_CITATION_FIELDS
    ):
        return build_unavailable_citation()

    return {
        "available": True,
        "document": retrieved_chunk["document"],
        "section_number": retrieved_chunk["section_number"],
        "section_title": retrieved_chunk["section_title"],
        "page_number": retrieved_chunk["page_number"],
        "corpus_version": retrieved_chunk["corpus_version"],
    }
