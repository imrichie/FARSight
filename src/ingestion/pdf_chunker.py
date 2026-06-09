# pdf_chunker.py
# Parses each source PDF into tagged, regulation-sized text chunks
# ready for embedding and upload to Azure AI Search.


def chunk_pdf_into_regulation_segments(pdf_file_path: str, source_document: str, part_number: str) -> list[dict]:
    """
    Parse a single FAR/AIM PDF into regulation-sized text chunks.

    Each chunk is returned as a dict with the following fields:
        - chunk_text: the regulation text
        - source_document: e.g. "14 CFR Part 91" or "AIM"
        - part_number: e.g. "91" or "AIM"
        - section_identifier: e.g. "§91.155" (best-effort extracted from text)
        - page_number: page in the source PDF

    Args:
        pdf_file_path: Absolute path to the PDF file.
        source_document: Human-readable name for the source (used in citations).
        part_number: Short identifier for the regulatory part.

    Returns:
        A list of chunk dicts ready for embedding and upload.
    """
    raise NotImplementedError
