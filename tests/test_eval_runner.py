import json

import evaluation.eval_runner as eval_runner
from evaluation.eval_runner import (
    ANSWER_JUDGE_VERSION,
    apply_current_expectations,
    judge_answer_correctness,
    load_evaluation_results,
    run_evaluation_pipeline,
    save_evaluation_results,
    score_evaluation_results,
)


def _query(
    question_type="in_scope",
    expected_citation="14 CFR § 91.155",
    answer_expectation_type="direct",
):
    return {
        "id": "G-01" if question_type == "in_scope" else "R-01",
        "question": "What are the VFR weather minimums in Class C airspace?",
        "expected_key_facts": ["3 SM visibility"],
        "expected_citation": expected_citation,
        "question_type": question_type,
        "retrieval_type": "direct" if question_type == "in_scope" else "refusal",
        "answer_expectation_type": (
            answer_expectation_type if question_type == "in_scope" else "refusal"
        ),
        "notes": None,
    }


def _chunk(section_number="91.155"):
    return {
        "id": f"14-cfr-part-91_{section_number.replace('.', '-')}",
        "document": "14 CFR Part 91",
        "part_number": "91",
        "section_number": section_number,
        "section_title": "Basic VFR weather minimums",
        "chunk_text": "Class C requires 3 statute miles visibility.",
        "page_number": 100,
        "corpus_version": "2024-01-01",
        "search_score": 3.14,
    }


def _answer(section_number="91.155", answer_was_found=True):
    if not answer_was_found:
        return {
            "answer_was_found": False,
            "plain_language_summary": "I could not find a confident answer.",
            "verbatim_excerpt": None,
            "excerpt_is_verbatim": None,
            "citation": None,
        }

    return {
        "answer_was_found": True,
        "plain_language_summary": "Class C requires 3 SM visibility.",
        "verbatim_excerpt": "Class C requires 3 statute miles visibility.",
        "excerpt_is_verbatim": True,
        "citation": {
            "available": True,
            "document": "14 CFR Part 91",
            "section_number": section_number,
            "section_title": "Basic VFR weather minimums",
            "page_number": 100,
            "corpus_version": "2024-01-01",
        },
    }


def _passing_judge(_result):
    return {
        "answer_is_correct": True,
        "missing_key_facts": [],
        "reason": "all key facts are present",
    }


def _failing_judge(_result):
    return {
        "answer_is_correct": False,
        "missing_key_facts": ["3 SM visibility"],
        "reason": "visibility is missing",
    }


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeChatClient:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def complete(self, messages, **completion_options):
        self.calls.append(
            {
                "messages": messages,
                "completion_options": completion_options,
            }
        )
        return _FakeResponse(json.dumps(self.replies.pop(0)))


def test_run_evaluation_pipeline_saves_raw_query_outputs():
    def retrieve_chunks(question, chunks_to_retrieve):
        assert question == "What are the VFR weather minimums in Class C airspace?"
        assert chunks_to_retrieve == 5
        return [_chunk()]

    def generate_answer(question, retrieved_chunks):
        assert question == "What are the VFR weather minimums in Class C airspace?"
        assert retrieved_chunks == [_chunk()]
        return _answer()

    payload = run_evaluation_pipeline(
        [_query()],
        retrieve_chunks=retrieve_chunks,
        generate_answer=generate_answer,
    )

    assert payload["metadata"]["result_count"] == 1
    assert payload["results"][0]["id"] == "G-01"
    assert payload["results"][0]["answer_expectation_type"] == "direct"
    assert payload["results"][0]["retrieved_chunks"][0]["rank"] == 1
    assert payload["results"][0]["answer"]["citation"]["section_number"] == "91.155"
    assert payload["results"][0]["pipeline_error"] is None


def test_in_scope_question_scores_all_metrics_as_passed():
    payload = {
        "results": [
            {
                **_query(),
                "retrieved_chunks": [_chunk()],
                "answer": _answer(),
                "pipeline_error": None,
            }
        ]
    }

    scorecard = score_evaluation_results(payload, answer_judge=_passing_judge)

    assert scorecard["summary"]["retrieval_hit_rate"]["passed"] == 1
    assert scorecard["summary"]["citation_accuracy"]["passed"] == 1
    assert scorecard["summary"]["answer_correctness"]["passed"] == 1
    assert scorecard["summary"]["correct_refusal_rate"]["total"] == 0


def test_saved_results_can_be_loaded_and_scored_without_pipeline_calls(tmp_path):
    results_file = tmp_path / "eval_results.json"
    payload = {
        "metadata": {"result_count": 1},
        "results": [
            {
                **_query(),
                "retrieved_chunks": [_chunk()],
                "answer": _answer(),
                "pipeline_error": None,
            }
        ],
    }

    save_evaluation_results(payload, results_file)
    loaded_payload = load_evaluation_results(results_file)
    scorecard = score_evaluation_results(loaded_payload, answer_judge=_passing_judge)

    assert scorecard["summary"]["retrieval_hit_rate"]["passed"] == 1
    assert scorecard["summary"]["citation_accuracy"]["passed"] == 1
    assert scorecard["summary"]["answer_correctness"]["passed"] == 1


def test_retrieval_hit_rate_fails_when_expected_chunk_is_missing():
    payload = {
        "results": [
            {
                **_query(),
                "retrieved_chunks": [_chunk(section_number="91.157")],
                "answer": _answer(),
                "pipeline_error": None,
            }
        ]
    }

    scorecard = score_evaluation_results(payload, answer_judge=_passing_judge)
    metric = scorecard["per_question"][0]["metrics"]["retrieval_hit_rate"]

    assert metric["passed"] is False
    assert metric["expected"] == ["14 CFR Part 91 91.155"]
    assert metric["actual"] == ["14 CFR Part 91 91.157"]


def test_citation_accuracy_fails_when_answer_cites_wrong_section():
    payload = {
        "results": [
            {
                **_query(),
                "retrieved_chunks": [_chunk()],
                "answer": _answer(section_number="91.157"),
                "pipeline_error": None,
            }
        ]
    }

    scorecard = score_evaluation_results(payload, answer_judge=_passing_judge)
    metric = scorecard["per_question"][0]["metrics"]["citation_accuracy"]

    assert metric["passed"] is False
    assert metric["expected"] == ["14 CFR Part 91 91.155"]
    assert metric["actual"] == "14 CFR Part 91 91.157"


def test_answer_correctness_uses_answer_judge_verdict():
    payload = {
        "results": [
            {
                **_query(),
                "retrieved_chunks": [_chunk()],
                "answer": _answer(),
                "pipeline_error": None,
            }
        ]
    }

    scorecard = score_evaluation_results(payload, answer_judge=_failing_judge)
    metric = scorecard["per_question"][0]["metrics"]["answer_correctness"]

    assert metric["passed"] is False
    assert metric["actual"]["missing_key_facts"] == ["3 SM visibility"]


def test_model_judge_rechecks_failed_judgment_and_accepts_supported_answer(monkeypatch):
    client = _FakeChatClient(
        [
            {
                "answer_is_correct": False,
                "missing_key_facts": ["24 hours after decompression dives"],
                "reason": "decompression wait is missing",
            },
            {
                "answer_is_correct": True,
                "missing_key_facts": [],
                "reason": "the excerpt includes the decompression wait",
            },
        ]
    )
    monkeypatch.setattr(eval_runner, "build_chat_client", lambda: client)
    result = {
        **_query(answer_expectation_type="list"),
        "expected_key_facts": [
            "12 hours after a non-decompression dive before flights up to 8,000 ft",
            "24 hours after decompression dives",
        ],
        "answer": {
            **_answer(),
            "plain_language_summary": (
                "Wait 12 hours after a non-decompression dive and 24 hours if "
                "the dive required a controlled ascent."
            ),
            "verbatim_excerpt": (
                "The recommended wait time is at least 24 hours after diving "
                "that required a controlled ascent (i.e., decompression stop diving)."
            ),
        },
    }

    judgment = judge_answer_correctness(result)

    assert judgment["answer_is_correct"] is True
    assert judgment["missing_key_facts"] == []
    assert judgment["answer_judge_rechecked"] is True
    assert len(client.calls) == 2


def test_model_judge_recheck_keeps_confirmed_failure(monkeypatch):
    client = _FakeChatClient(
        [
            {
                "answer_is_correct": False,
                "missing_key_facts": ["3 SM visibility"],
                "reason": "visibility is missing",
            },
            {
                "answer_is_correct": False,
                "missing_key_facts": ["3 SM visibility"],
                "reason": "the answer only discusses cloud clearance",
            },
        ]
    )
    monkeypatch.setattr(eval_runner, "build_chat_client", lambda: client)
    result = {
        **_query(),
        "answer": {
            **_answer(),
            "plain_language_summary": "Stay 500 feet below the clouds.",
            "verbatim_excerpt": "Aircraft must remain 500 feet below clouds.",
        },
    }

    judgment = judge_answer_correctness(result)

    assert judgment["answer_is_correct"] is False
    assert judgment["missing_key_facts"] == ["3 SM visibility"]
    assert judgment["reason"] == "the answer only discusses cloud clearance"
    assert judgment["answer_judge_rechecked"] is True
    assert len(client.calls) == 2


def test_model_judge_evidence_check_accepts_supported_numeric_fact(monkeypatch):
    client = _FakeChatClient(
        [
            {
                "answer_is_correct": False,
                "missing_key_facts": ["24 hours after decompression dives"],
                "reason": "decompression wait is missing",
            },
            {
                "answer_is_correct": False,
                "missing_key_facts": ["24 hours after decompression dives"],
                "reason": "not stated as a standalone rule",
            },
        ]
    )
    monkeypatch.setattr(eval_runner, "build_chat_client", lambda: client)
    result = {
        **_query(answer_expectation_type="list"),
        "expected_key_facts": [
            "24 hours after decompression dives",
        ],
        "answer": {
            **_answer(),
            "plain_language_summary": (
                "Wait 24 hours if the dive required a controlled ascent."
            ),
            "verbatim_excerpt": (
                "The recommended wait time is at least 24 hours after diving "
                "that required a controlled ascent (i.e., decompression stop diving)."
            ),
        },
    }

    judgment = judge_answer_correctness(result)

    assert judgment["answer_is_correct"] is True
    assert judgment["missing_key_facts"] == []
    assert judgment["answer_judge_rechecked"] is True
    assert judgment["answer_judge_evidence_checked"] is True


def test_answer_correctness_caches_answer_judge_verdict():
    payload = {
        "results": [
            {
                **_query(),
                "retrieved_chunks": [_chunk()],
                "answer": _answer(),
                "pipeline_error": None,
            }
        ]
    }

    score_evaluation_results(payload, answer_judge=_passing_judge)

    assert payload["results"][0]["answer_judgment"] == {
        "answer_is_correct": True,
        "missing_key_facts": [],
        "reason": "all key facts are present",
        "answer_judge_version": ANSWER_JUDGE_VERSION,
        "judged_expected_key_facts": ["3 SM visibility"],
        "judged_answer_expectation_type": "direct",
    }


def test_answer_correctness_reuses_cached_answer_judge_verdict():
    payload = {
        "results": [
            {
                **_query(),
                "retrieved_chunks": [_chunk()],
                "answer": _answer(),
                "pipeline_error": None,
                "answer_judgment": {
                    "answer_is_correct": True,
                    "missing_key_facts": [],
                    "reason": "cached verdict",
                    "answer_judge_version": ANSWER_JUDGE_VERSION,
                    "judged_expected_key_facts": ["3 SM visibility"],
                    "judged_answer_expectation_type": "direct",
                },
            }
        ]
    }

    def fail_if_called(_result):
        raise AssertionError("answer judge should not be called")

    scorecard = score_evaluation_results(payload, answer_judge=fail_if_called)

    assert scorecard["summary"]["answer_correctness"]["passed"] == 1


def test_answer_correctness_refreshes_stale_cached_judgment():
    payload = {
        "results": [
            {
                **_query(),
                "retrieved_chunks": [_chunk()],
                "answer": _answer(),
                "pipeline_error": None,
                "answer_judgment": {
                    "answer_is_correct": False,
                    "missing_key_facts": ["old fact"],
                    "reason": "old verdict",
                    "answer_judge_version": "old-version",
                    "judged_expected_key_facts": ["old fact"],
                    "judged_answer_expectation_type": "list",
                },
            }
        ]
    }

    scorecard = score_evaluation_results(payload, answer_judge=_passing_judge)

    assert scorecard["summary"]["answer_correctness"]["passed"] == 1
    assert payload["results"][0]["answer_judgment"]["answer_judge_version"] == (
        ANSWER_JUDGE_VERSION
    )


def test_answer_correctness_refreshes_judgment_for_changed_expectation_type():
    payload = {
        "results": [
            {
                **_query(answer_expectation_type="list"),
                "retrieved_chunks": [_chunk()],
                "answer": _answer(),
                "pipeline_error": None,
                "answer_judgment": {
                    "answer_is_correct": False,
                    "missing_key_facts": ["3 SM visibility"],
                    "reason": "old direct verdict",
                    "answer_judge_version": ANSWER_JUDGE_VERSION,
                    "judged_expected_key_facts": ["3 SM visibility"],
                    "judged_answer_expectation_type": "direct",
                },
            }
        ]
    }

    scorecard = score_evaluation_results(payload, answer_judge=_passing_judge)

    assert scorecard["summary"]["answer_correctness"]["passed"] == 1
    assert payload["results"][0]["answer_judgment"][
        "judged_answer_expectation_type"
    ] == "list"


def test_score_only_expectations_can_be_refreshed_from_current_queries():
    payload = {
        "metadata": {},
        "results": [
            {
                **_query(),
                "expected_key_facts": ["old fact"],
                "expected_citation": "14 CFR § 91.999",
                "answer_expectation_type": "list",
                "retrieved_chunks": [_chunk()],
                "answer": _answer(),
                "pipeline_error": None,
            }
        ],
    }
    current_query = {
        **_query(answer_expectation_type="direct"),
        "expected_key_facts": ["new fact"],
        "expected_citation": "14 CFR § 91.155",
    }

    apply_current_expectations(payload, [current_query])

    assert payload["results"][0]["expected_key_facts"] == ["new fact"]
    assert payload["results"][0]["expected_citation"] == "14 CFR § 91.155"
    assert payload["results"][0]["answer_expectation_type"] == "direct"


def test_out_of_scope_question_passes_when_fallback_answer_is_returned():
    payload = {
        "results": [
            {
                **_query(question_type="out_of_scope", expected_citation=None),
                "retrieved_chunks": [_chunk()],
                "answer": _answer(answer_was_found=False),
                "pipeline_error": None,
            }
        ]
    }

    scorecard = score_evaluation_results(payload, answer_judge=_passing_judge)
    metric = scorecard["per_question"][0]["metrics"]["correct_refusal_rate"]

    assert metric["passed"] is True
    assert scorecard["summary"]["correct_refusal_rate"]["passed"] == 1


def test_out_of_scope_question_fails_when_cited_answer_is_returned():
    payload = {
        "results": [
            {
                **_query(question_type="out_of_scope", expected_citation=None),
                "retrieved_chunks": [_chunk()],
                "answer": _answer(),
                "pipeline_error": None,
            }
        ]
    }

    scorecard = score_evaluation_results(payload, answer_judge=_passing_judge)
    metric = scorecard["per_question"][0]["metrics"]["correct_refusal_rate"]

    assert metric["passed"] is False
    assert metric["expected"] == "fallback answer with no citation"
    assert metric["actual"] == "14 CFR Part 91 91.155"
