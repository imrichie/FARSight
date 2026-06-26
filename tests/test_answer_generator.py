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


def _nearby_uas_registration_chunk():
    return {
        "id": "aim_11-2-2",
        "document": "AIM",
        "part_number": None,
        "section_number": "11-2-2",
        "section_title": "Registration Requirements",
        "chunk_text": (
            "AIM 11-2-2 Registration Requirements\n"
            "To register a UAS online under Part 48, refer to the FAA's "
            "DroneZone website."
        ),
        "page_number": 699,
        "corpus_version": "2023-04-20",
        "search_score": 2.2,
    }


def _registration_certificate_chunk():
    return {
        "id": "14-cfr-part-91_91-203",
        "document": "14 CFR Part 91",
        "part_number": "91",
        "section_number": "91.203",
        "section_title": "Civil aircraft: Certifications required",
        "chunk_text": (
            "§ 91.203 Civil aircraft: Certifications required\n"
            "No person may operate a civil aircraft unless it has within it "
            "an appropriate and current airworthiness certificate and an "
            "effective U.S. registration certificate."
        ),
        "page_number": 129,
        "corpus_version": "2024-01-01",
        "search_score": 1.9,
    }


def _model_response(payload: dict):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=json.dumps(payload))
            )
        ]
    )


def _raw_model_response(content: str):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content)
            )
        ]
    )


def _answerable_gate_response():
    return _model_response(
        {
            "answerable": True,
            "reason": "directly supported by the retrieved chunk",
        }
    )


def _not_answerable_gate_response():
    return _model_response(
        {
            "answerable": False,
            "reason": "the retrieved chunks are only topically nearby",
        }
    )


def _source_selection_response(chosen_chunk_number=1):
    return _model_response(
        {
            "answer_found": True,
            "chosen_chunk_number": chosen_chunk_number,
            "question_focus": "directly responsive source",
            "reason": "this chunk directly answers the question",
        }
    )


def _no_source_selection_response():
    return _model_response(
        {
            "answer_found": False,
            "chosen_chunk_number": None,
            "question_focus": "unsupported question",
            "reason": "none of the chunks directly answer the question",
        }
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
    chat_client.complete.side_effect = [
        _source_selection_response(),
        _model_response(
            {
                "answer_found": True,
                "chosen_chunk_number": 1,
                "plain_language_summary": "A pilot must wait 8 hours after drinking.",
                "verbatim_excerpt": "within 8 hours after the consumption of any alcoholic beverage.",
            }
        ),
        _answerable_gate_response(),
    ]

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
    chat_client.complete.side_effect = [
        _source_selection_response(),
        _model_response(
            {
                "answer_found": False,
                "chosen_chunk_number": None,
                "plain_language_summary": "",
                "verbatim_excerpt": "",
            }
        ),
    ]

    with patch("src.answer_generator.build_chat_client", return_value=chat_client):
        cited_answer = generate_cited_answer(
            "What are airline pilot rest requirements?",
            [_retrieved_chunk()],
        )

    assert _fallback_was_returned(cited_answer)


def test_model_invalid_chunk_number_returns_fallback_message():
    chat_client = MagicMock()
    chat_client.complete.side_effect = [
        _source_selection_response(),
        _model_response(
            {
                "answer_found": True,
                "chosen_chunk_number": 2,
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

    assert _fallback_was_returned(cited_answer)


def test_malformed_generation_response_returns_fallback_message():
    chat_client = MagicMock()
    chat_client.complete.side_effect = [
        _source_selection_response(),
        _raw_model_response("not valid json"),
    ]

    with patch("src.answer_generator.build_chat_client", return_value=chat_client):
        cited_answer = generate_cited_answer(
            "How long after drinking can I fly?",
            [_retrieved_chunk()],
        )

    assert chat_client.complete.call_count == 2
    assert _fallback_was_returned(cited_answer)


def test_unverified_excerpt_retries_once_and_returns_cited_answer_on_success():
    chat_client = MagicMock()
    chat_client.complete.side_effect = [
        _source_selection_response(),
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
        _answerable_gate_response(),
    ]

    with patch("src.answer_generator.build_chat_client", return_value=chat_client):
        cited_answer = generate_cited_answer(
            "How long after drinking can I fly?",
            [_retrieved_chunk()],
        )

    second_attempt_messages = chat_client.complete.call_args_list[2].kwargs["messages"]
    assert chat_client.complete.call_count == 4
    assert "not found in the chosen chunk" in second_attempt_messages[-1].content
    assert cited_answer["answer_was_found"] is True
    assert cited_answer["citation"]["section_number"] == "91.17"


def test_unverified_excerpt_twice_falls_back_after_retry():
    chat_client = MagicMock()
    chat_client.complete.side_effect = [
        _source_selection_response(),
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

    assert chat_client.complete.call_count == 3
    assert _fallback_was_returned(cited_answer)


def test_not_answerable_gate_vetoes_verified_answer():
    chat_client = MagicMock()
    chat_client.complete.side_effect = [
        _source_selection_response(),
        _model_response(
            {
                "answer_found": True,
                "chosen_chunk_number": 1,
                "plain_language_summary": (
                    "For small unmanned aircraft, the FAA says to register "
                    "through DroneZone."
                ),
                "verbatim_excerpt": (
                    "To register a UAS online under Part 48, refer to the "
                    "FAA's DroneZone website."
                ),
            }
        ),
        _not_answerable_gate_response(),
    ]

    with patch("src.answer_generator.build_chat_client", return_value=chat_client):
        cited_answer = generate_cited_answer(
            "How do I register my aircraft with the FAA?",
            [_nearby_uas_registration_chunk()],
        )

    assert chat_client.complete.call_count == 3
    assert _fallback_was_returned(cited_answer)


def test_malformed_gate_response_allows_verified_answer():
    chat_client = MagicMock()
    chat_client.complete.side_effect = [
        _source_selection_response(),
        _model_response(
            {
                "answer_found": True,
                "chosen_chunk_number": 1,
                "plain_language_summary": "A pilot must wait 8 hours after drinking.",
                "verbatim_excerpt": "within 8 hours after the consumption of any alcoholic beverage.",
            }
        ),
        _raw_model_response("not valid json"),
    ]

    with patch("src.answer_generator.build_chat_client", return_value=chat_client):
        cited_answer = generate_cited_answer(
            "How long after drinking can I fly?",
            [_retrieved_chunk()],
        )

    assert cited_answer["answer_was_found"] is True
    assert cited_answer["citation"]["section_number"] == "91.17"


def test_answerability_gate_allows_valid_registration_certificate_answer():
    chat_client = MagicMock()
    chat_client.complete.side_effect = [
        _source_selection_response(chosen_chunk_number=2),
        _model_response(
            {
                "answer_found": True,
                "chosen_chunk_number": 1,
                "plain_language_summary": (
                    "The aircraft must carry an airworthiness certificate and "
                    "registration certificate."
                ),
                "verbatim_excerpt": (
                    "an appropriate and current airworthiness certificate and an "
                    "effective U.S. registration certificate."
                ),
            }
        ),
        _answerable_gate_response(),
    ]

    with patch("src.answer_generator.build_chat_client", return_value=chat_client):
        cited_answer = generate_cited_answer(
            "What documents must be on board the aircraft?",
            [_nearby_uas_registration_chunk(), _registration_certificate_chunk()],
        )

    selection_messages = chat_client.complete.call_args_list[0].kwargs["messages"]
    selection_prompt = selection_messages[-1].content
    generation_messages = chat_client.complete.call_args_list[1].kwargs["messages"]
    generation_prompt = generation_messages[-1].content
    assert "DroneZone" in selection_prompt
    assert "§ 91.203" in generation_prompt
    assert "DroneZone" not in generation_prompt
    assert cited_answer["answer_was_found"] is True
    assert cited_answer["citation"]["section_number"] == "91.203"


def test_no_direct_source_selection_returns_fallback_message():
    chat_client = MagicMock()
    chat_client.complete.return_value = _no_source_selection_response()

    with patch("src.answer_generator.build_chat_client", return_value=chat_client):
        cited_answer = generate_cited_answer(
            "How do I register my aircraft with the FAA?",
            [_nearby_uas_registration_chunk()],
        )

    assert chat_client.complete.call_count == 1
    assert _fallback_was_returned(cited_answer)
