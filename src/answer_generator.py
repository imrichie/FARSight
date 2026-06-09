# answer_generator.py
# Takes a user question and retrieved regulation chunks and produces
# a cited answer using the deployed Azure OpenAI model.


def generate_cited_answer(user_question: str, retrieved_regulation_chunks: list[dict]) -> dict:
    """
    Generate a cited answer from the retrieved regulation chunks.

    The model is instructed to answer only from the provided chunks.
    If no chunks are provided or none are sufficiently relevant,
    the fallback message is returned instead of a generated answer.

    Args:
        user_question: The plain English question from the user.
        retrieved_regulation_chunks: Chunks returned by regulation_retriever.py.

    Returns:
        A dict with:
            - answer_text: the generated answer, or the fallback message
            - citation_source_document: source document name (or None)
            - citation_section_identifier: section reference (or None)
            - citation_page_number: page number (or None)
            - answer_was_found: True if a grounded answer was generated,
                                False if the fallback was returned
    """
    raise NotImplementedError


FALLBACK_MESSAGE = (
    "I could not find a confident answer to that question in the FAR/AIM. "
    "Please consult the official FAA documentation or a certified flight instructor."
)
