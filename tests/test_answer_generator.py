import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.answer_generator import FALLBACK_MESSAGE, generate_cited_answer


def _retrieved_chunk():
    return {
        "id": "14-cfr-part-91_91-17",
        "document": "14 CFR Part 91",
        "part_number": "91",
        "section_number": "91.17",
        "section_title": "Alcohol or drugs",
        "chunk_text": (
            "§ 91.17 Alcohol or drugs\n"
            "No person may act or attempt to act as a crewmember of a civil "
            "aircraft within 8 hours after the consumption of any alcoholic beverage."
        ),
        "page_number": 42,
        "corpus_version": "2024-01-01",
        "search_score": 3.14,
    }


def _model_response(payload: dict):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=json.dumps(payload))
            )
        ]
    )


def _fallback_was_returned(cited_answer: dict) -> bool:
    return (
        cited_answer["answer_was_found"] is False
        and cited_answer["plain_language_summary"] == FALLBACK_MESSAGE
        and cited_answer["verbatim_excerpt"] is None
        and cited_answer["citation"] is None
    )


def test_valid_question_with_relevant_chunk_returns_cited_answer():
    chat_client = MagicMock()
    chat_client.complete.return_value = _model_response(
        {
            "answer_found": True,
            "chosen_chunk_number": 1,
            "plain_language_summary": "A pilot must wait 8 hours after drinking.",
            "verbatim_excerpt": "within 8 hours after the consumption of any alcoholic beverage.",
        }
    )

    with patch("src.answer_generator.build_chat_client", return_value=chat_client):
        cited_answer = generate_cited_answer(
            "How long after drinking can I fly?",
            [_retrieved_chunk()],
        )

    assert cited_answer["answer_was_found"] is True
    assert cited_answer["excerpt_is_verbatim"] is True
    assert cited_answer["citation"]["section_number"] == "91.17"


def test_empty_chunks_return_fallback_message():
    with patch("src.answer_generator.build_chat_client") as build_chat_client:
        cited_answer = generate_cited_answer(
            "How long after drinking can I fly?",
            [],
        )

    assert _fallback_was_returned(cited_answer)
    build_chat_client.assert_not_called()


def test_model_answer_found_false_returns_fallback_message():
    chat_client = MagicMock()
    chat_client.complete.return_value = _model_response(
        {
            "answer_found": False,
            "chosen_chunk_number": None,
            "plain_language_summary": "",
            "verbatim_excerpt": "",
        }
    )

    with patch("src.answer_generator.build_chat_client", return_value=chat_client):
        cited_answer = generate_cited_answer(
            "What are airline pilot rest requirements?",
            [_retrieved_chunk()],
        )

    assert _fallback_was_returned(cited_answer)


def test_model_invalid_chunk_number_returns_fallback_message():
    chat_client = MagicMock()
    chat_client.complete.return_value = _model_response(
        {
            "answer_found": True,
            "chosen_chunk_number": 2,
            "plain_language_summary": "A pilot must wait 8 hours after drinking.",
            "verbatim_excerpt": "within 8 hours after the consumption of any alcoholic beverage.",
        }
    )

    with patch("src.answer_generator.build_chat_client", return_value=chat_client):
        cited_answer = generate_cited_answer(
            "How long after drinking can I fly?",
            [_retrieved_chunk()],
        )

    assert _fallback_was_returned(cited_answer)


def test_unverified_excerpt_retries_once_and_returns_cited_answer_on_success():
    chat_client = MagicMock()
    chat_client.complete.side_effect = [
        _model_response(
            {
                "answer_found": True,
                "chosen_chunk_number": 1,
                "plain_language_summary": "A pilot must wait 8 hours after drinking.",
                "verbatim_excerpt": "a spliced quote that is not in the chunk",
            }
        ),
        _model_response(
            {
                "answer_found": True,
                "chosen_chunk_number": 1,
                "plain_language_summary": "A pilot must wait 8 hours after drinking.",
                "verbatim_excerpt": "within 8 hours after the consumption of any alcoholic beverage.",
            }
        ),
    ]

    with patch("src.answer_generator.build_chat_client", return_value=chat_client):
        cited_answer = generate_cited_answer(
            "How long after drinking can I fly?",
            [_retrieved_chunk()],
        )

    second_attempt_messages = chat_client.complete.call_args_list[1].kwargs["messages"]
    assert chat_client.complete.call_count == 2
    assert "not found in the chosen chunk" in second_attempt_messages[-1].content
    assert cited_answer["answer_was_found"] is True
    assert cited_answer["citation"]["section_number"] == "91.17"


def test_unverified_excerpt_twice_falls_back_after_retry():
    chat_client = MagicMock()
    chat_client.complete.side_effect = [
        _model_response(
            {
                "answer_found": True,
                "chosen_chunk_number": 1,
                "plain_language_summary": "A pilot must wait 8 hours after drinking.",
                "verbatim_excerpt": "a spliced quote that is not in the chunk",
            }
        ),
        _model_response(
            {
                "answer_found": True,
                "chosen_chunk_number": 1,
                "plain_language_summary": "A pilot must wait 8 hours after drinking.",
                "verbatim_excerpt": "another quote that is still not in the chunk",
            }
        ),
    ]

    with patch("src.answer_generator.build_chat_client", return_value=chat_client):
        cited_answer = generate_cited_answer(
            "How long after drinking can I fly?",
            [_retrieved_chunk()],
        )

    assert chat_client.complete.call_count == 2
    assert _fallback_was_returned(cited_answer)
