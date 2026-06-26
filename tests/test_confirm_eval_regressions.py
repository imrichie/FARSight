from evaluation.confirm_eval_regressions import (
    confirm_answer_correctness_regressions,
)
from evaluation.eval_runner import score_evaluation_results


def _query(question_id="G-01"):
    return {
        "id": question_id,
        "question": "What is the hearing standard for a third-class medical?",
        "expected_key_facts": ["6 feet", "audiometric test"],
        "expected_citation": "14 CFR § 67.305",
        "question_type": "in_scope",
        "retrieval_type": "direct",
        "answer_expectation_type": "direct",
        "notes": None,
    }


def _chunk():
    return {
        "id": "14-cfr-part-67_67-305",
        "document": "14 CFR Part 67",
        "section_number": "67.305",
        "section_title": "Ear, nose, throat, and equilibrium",
        "chunk_text": "Hearing may be shown at 6 feet or by audiometric testing.",
        "page_number": 8,
        "corpus_version": "2024-01-01",
        "search_score": 3.14,
    }


def _answer(summary):
    return {
        "answer_was_found": True,
        "plain_language_summary": summary,
        "verbatim_excerpt": "Hearing may be shown at 6 feet or by audiometric testing.",
        "excerpt_is_verbatim": True,
        "citation": {
            "available": True,
            "document": "14 CFR Part 67",
            "section_number": "67.305",
            "section_title": "Ear, nose, throat, and equilibrium",
            "page_number": 8,
            "corpus_version": "2024-01-01",
        },
    }


def _result(question_id="G-01", answer_summary="only mentions 6 feet"):
    return {
        **_query(question_id),
        "retrieved_chunks": [_chunk()],
        "answer": _answer(answer_summary),
        "pipeline_error": None,
    }


def _baseline(answer_passed=1, accepted_failures=None):
    return {
        "name": "test baseline",
        "metrics": {
            "retrieval_hit_rate": {"passed": 1, "total": 1, "accepted_failures": []},
            "citation_accuracy": {"passed": 1, "total": 1, "accepted_failures": []},
            "answer_correctness": {
                "passed": answer_passed,
                "total": 1,
                "accepted_failures": [
                    {
                        "id": question_id,
                        "category": "known_limitation",
                        "reason": "accepted failure",
                    }
                    for question_id in accepted_failures or []
                ],
            },
            "correct_refusal_rate": {
                "passed": 0,
                "total": 0,
                "accepted_failures": [],
            },
        },
    }


def _answer_judge(result):
    answer_text = result["answer"]["plain_language_summary"]
    passed = "audiometric" in answer_text
    return {
        "answer_is_correct": passed,
        "missing_key_facts": [] if passed else ["audiometric test"],
        "reason": "all facts present" if passed else "audiometric option missing",
    }


def test_confirmation_replaces_new_answer_failure_when_retry_passes():
    payload = {"metadata": {}, "results": [_result()]}

    def run_query(_query):
        return _result(answer_summary="mentions 6 feet and audiometric testing")

    confirmed_payload, attempts = confirm_answer_correctness_regressions(
        payload,
        [_query()],
        _baseline(answer_passed=1),
        run_query=run_query,
        answer_judge=_answer_judge,
    )
    scorecard = score_evaluation_results(
        confirmed_payload,
        answer_judge=_answer_judge,
    )

    assert attempts[0]["passed"] is True
    assert confirmed_payload["results"][0]["stabilization"]["outcome"] == (
        "replaced_initial_failure"
    )
    assert scorecard["summary"]["answer_correctness"]["passed"] == 1


def test_confirmation_does_not_retry_accepted_answer_failures():
    payload = {"metadata": {}, "results": [_result()]}
    calls = []

    def run_query(query):
        calls.append(query)
        return _result(answer_summary="mentions 6 feet and audiometric testing")

    confirmed_payload, attempts = confirm_answer_correctness_regressions(
        payload,
        [_query()],
        _baseline(answer_passed=0, accepted_failures=["G-01"]),
        run_query=run_query,
        answer_judge=_answer_judge,
    )

    assert attempts == []
    assert calls == []
    assert confirmed_payload["results"][0]["answer"]["plain_language_summary"] == (
        "only mentions 6 feet"
    )


def test_confirmation_records_retry_when_failure_reproduces():
    payload = {"metadata": {}, "results": [_result()]}

    def run_query(_query):
        return _result(answer_summary="still only mentions 6 feet")

    confirmed_payload, attempts = confirm_answer_correctness_regressions(
        payload,
        [_query()],
        _baseline(answer_passed=1),
        run_query=run_query,
        answer_judge=_answer_judge,
    )

    assert attempts[0]["passed"] is False
    assert confirmed_payload["results"][0]["stabilization_attempts"][0][
        "stabilization"
    ]["outcome"] == "failure_reproduced"
    assert confirmed_payload["results"][0]["answer"]["plain_language_summary"] == (
        "only mentions 6 feet"
    )
