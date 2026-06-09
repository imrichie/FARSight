# regulation_retriever.py
# Accepts a plain English question and returns the most relevant
# regulation chunks from Azure AI Search using hybrid search.


def retrieve_relevant_regulation_chunks(user_question: str, max_chunks_to_return: int = 5) -> list[dict]:
    """
    Search the Azure AI Search index for regulation chunks relevant
    to the user's question using hybrid (keyword + vector) search.

    Each returned chunk includes:
        - chunk_text: the regulation text
        - source_document: e.g. "14 CFR Part 91"
        - section_identifier: e.g. "§91.155"
        - page_number: page in the source PDF
        - search_score: relevance score from Azure AI Search

    Args:
        user_question: The plain English question from the user.
        max_chunks_to_return: Number of top results to return (default 5).

    Returns:
        A list of chunk dicts ordered by relevance score, highest first.
        Returns an empty list if no results are found.
    """
    raise NotImplementedError
