# answer_generator.py
# Generation layer: turns retrieved regulation chunks into a grounded,
# cited answer. The model writes the plain-language summary and selects
# the verbatim excerpt, but the citation is assembled in code from the
# chosen chunk's metadata — the model never writes a section number into
# the citation. That separation is FARSight's core trust mechanism.

import json
import os
import re

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import AssistantMessage, SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

FALLBACK_MESSAGE = (
    "I could not find a confident answer to that question in the FAR/AIM. "
    "Please consult the official FAA documentation or a certified flight instructor."
)

GROUNDED_ANSWER_SYSTEM_PROMPT = """\
You are the answer engine for FARSight, a question-answering tool for pilots
built on the FAA regulations (14 CFR) and the Aeronautical Information Manual.

You will receive a pilot's question and a numbered list of regulation chunks
retrieved for it. Follow these rules exactly:

1. Answer ONLY from the provided chunks. Your own aviation knowledge must
   never add facts that are not in the chunk text.
2. Decide which single chunk best answers the question. If the answer draws
   on more than one chunk, choose the one the verbatim excerpt comes from.
3. Write a plain-language summary: one or two sentences in everyday English.
   The summary must stay strictly consistent with the quoted regulation text —
   simplify it, never add to it or contradict it.
4. Copy a verbatim excerpt: one single CONTIGUOUS, unedited span copied from
   the chunk, quoted word for word. Never reassemble the quote from separate
   clauses or skip over text in the middle — a spliced quote is not a quote.
   If the full relevant text is too long, quote the single most relevant
   continuous passage instead. Do not paraphrase, shorten words, or fix
   typography inside the quote. Quote, don't compose.
5. If the chunks do not actually contain the answer, say so — do not force
   an answer from loosely related text.

Respond with JSON only, no other text, in exactly this shape:
{
  "answer_found": true or false,
  "chosen_chunk_number": <number of the chunk the excerpt comes from, or null>,
  "plain_language_summary": "<summary, or empty string if answer_found is false>",
  "verbatim_excerpt": "<exact quote from the chunk, or empty string if answer_found is false>"
}
"""


def build_chat_client() -> ChatCompletionsClient:
    openai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
    chat_deployment = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"]
    return ChatCompletionsClient(
        endpoint=f"{openai_endpoint}/openai/deployments/{chat_deployment}",
        credential=AzureKeyCredential(os.environ["AZURE_OPENAI_API_KEY"]),
    )


def format_chunks_for_prompt(retrieved_regulation_chunks: list[dict]) -> str:
    formatted_chunks = []
    for chunk_number, chunk in enumerate(retrieved_regulation_chunks, start=1):
        formatted_chunks.append(f"--- chunk {chunk_number} ---\n{chunk['chunk_text']}")
    return "\n\n".join(formatted_chunks)


def parse_model_json_response(model_response_text: str) -> dict:
    """Parse the model's JSON reply, tolerating accidental code fences."""
    response_text = model_response_text.strip()
    response_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", response_text)
    return json.loads(response_text)


def normalize_for_quote_check(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def build_fallback_answer() -> dict:
    return {
        "answer_was_found": False,
        "plain_language_summary": FALLBACK_MESSAGE,
        "verbatim_excerpt": None,
        "excerpt_is_verbatim": None,
        "citation": None,
    }


def generate_cited_answer(
    user_question: str, retrieved_regulation_chunks: list[dict]
) -> dict:
    """
    Generate a grounded answer from the retrieved chunks.

    Returns a cited_answer dict:
        - answer_was_found: False means the uncertainty state — the chunks
          did not contain the answer
        - plain_language_summary: everyday-English answer (or the fallback
          message when no answer was found)
        - verbatim_excerpt: exact regulation text chosen by the model
        - excerpt_is_verbatim: code-side check that the excerpt really
          appears in the chosen chunk — the model's quote is never trusted
          blindly
        - citation: document, section number, title, page, and corpus
          version read from the chosen chunk's metadata in code; the model
          only picks WHICH chunk, it never writes the citation

    Whether the model's own judgment of "the chunks don't contain the
    answer" is reliable enough is an open question — the evaluation suite
    (Milestone 5) measures exactly this with its out-of-scope test queries.
    """
    load_dotenv()

    if not retrieved_regulation_chunks:
        return build_fallback_answer()

    chat_client = build_chat_client()
    conversation_messages = [
        SystemMessage(content=GROUNDED_ANSWER_SYSTEM_PROMPT),
        UserMessage(
            content=(
                f"Pilot's question: {user_question}\n\n"
                f"Retrieved regulation chunks:\n\n"
                f"{format_chunks_for_prompt(retrieved_regulation_chunks)}"
            )
        ),
    ]

    # An excerpt that fails verification is treated as a non-answer:
    # one corrective retry, then the honest uncertainty state. An
    # unverified quote is never shown to a user as regulation text.
    for generation_attempt in range(2):
        chat_response = chat_client.complete(messages=conversation_messages)
        model_reply_text = chat_response.choices[0].message.content
        model_reply = parse_model_json_response(model_reply_text)

        chosen_chunk_number = model_reply.get("chosen_chunk_number")
        chunk_number_is_valid = (
            isinstance(chosen_chunk_number, int)
            and 1 <= chosen_chunk_number <= len(retrieved_regulation_chunks)
        )
        if not model_reply.get("answer_found") or not chunk_number_is_valid:
            return build_fallback_answer()

        chosen_chunk = retrieved_regulation_chunks[chosen_chunk_number - 1]
        verbatim_excerpt = model_reply.get("verbatim_excerpt", "").strip()

        # Trust but verify: the excerpt must appear in the chunk as one
        # contiguous span or the answer does not ship
        excerpt_is_verbatim = normalize_for_quote_check(
            verbatim_excerpt
        ) in normalize_for_quote_check(chosen_chunk["chunk_text"])

        if excerpt_is_verbatim:
            return {
                "answer_was_found": True,
                "plain_language_summary": model_reply.get("plain_language_summary", "").strip(),
                "verbatim_excerpt": verbatim_excerpt,
                "excerpt_is_verbatim": True,
                "citation": {
                    "document": chosen_chunk["document"],
                    "section_number": chosen_chunk["section_number"],
                    "section_title": chosen_chunk["section_title"],
                    "page_number": chosen_chunk["page_number"],
                    "corpus_version": chosen_chunk["corpus_version"],
                },
            }

        # Feed the failure back and let the model try once more
        conversation_messages.append(AssistantMessage(content=model_reply_text))
        conversation_messages.append(
            UserMessage(
                content=(
                    "Your verbatim_excerpt was not found in the chosen chunk as one "
                    "contiguous span — it appears to be reassembled or edited. "
                    "Respond again with the same JSON shape, quoting one single "
                    "continuous passage from the chunk, copied exactly."
                )
            )
        )

    return build_fallback_answer()


def print_cited_answer(cited_answer: dict) -> None:
    """Readable terminal output for a grounded answer."""
    print(f"\nANSWER\n  {cited_answer['plain_language_summary']}")
    if not cited_answer["answer_was_found"]:
        return
    verbatim_mark = "✓ verbatim" if cited_answer["excerpt_is_verbatim"] else "⚠ NOT FOUND VERBATIM IN CHUNK"
    print(f"\nREGULATION TEXT ({verbatim_mark})\n  “{cited_answer['verbatim_excerpt']}”")
    citation = cited_answer["citation"]
    print(
        f"\nSOURCE\n  {citation['document']}, {citation['section_number']} — "
        f"{citation['section_title']} (p. {citation['page_number']}, "
        f"edition {citation['corpus_version']})"
    )


if __name__ == "__main__":
    import sys

    from src.regulation_retriever import retrieve_relevant_regulation_chunks

    if len(sys.argv) < 2:
        print('usage: python3 -m src.answer_generator "your question here"')
        sys.exit(1)
    question_from_terminal = sys.argv[1]
    print(f'question: "{question_from_terminal}"')
    print("retrieving...")
    retrieved_chunks = retrieve_relevant_regulation_chunks(question_from_terminal)
    print(f"retrieved {len(retrieved_chunks)} chunks — generating...")
    print_cited_answer(generate_cited_answer(question_from_terminal, retrieved_chunks))
