from evaluation.compare_eval_baseline import (
    compare_proposed_baseline_to_base,
    compare_scorecard_to_baseline,
)


def _metric_result(passed=True, expected=None, actual=None):
    return {
        "passed": passed,
        "expected": expected or ["expected"],
        "actual": actual or "actual",
    }


def _summary(passed, total):
    return {
        "passed": passed,
        "total": total,
        "percentage": passed / total * 100,
    }


def _baseline_metric(passed, total, accepted_failure_ids=None):
    return {
        "passed": passed,
        "total": total,
        "accepted_failures": [
            {
                "id": question_id,
                "category": "known_limitation",
                "reason": "accepted current limitation",
            }
            for question_id in accepted_failure_ids or []
        ],
    }


def _baseline(
    retrieval_passed=2,
    retrieval_failures=None,
    citation_passed=2,
    citation_failures=None,
    answer_passed=2,
    answer_failures=None,
    refusal_passed=1,
    refusal_failures=None,
):
    return {
        "name": "test baseline",
        "metrics": {
            "retrieval_hit_rate": _baseline_metric(
                retrieval_passed, 2, retrieval_failures
            ),
            "citation_accuracy": _baseline_metric(
                citation_passed, 2, citation_failures
            ),
            "answer_correctness": _baseline_metric(
                answer_passed, 2, answer_failures
            ),
            "correct_refusal_rate": _baseline_metric(
                refusal_passed, 1, refusal_failures
            ),
        },
    }


def _scorecard(
    retrieval_failures=None,
    citation_failures=None,
    answer_failures=None,
    refusal_failures=None,
):
    retrieval_failures = set(retrieval_failures or [])
    citation_failures = set(citation_failures or [])
    answer_failures = set(answer_failures or [])
    refusal_failures = set(refusal_failures or [])

    per_question = []
    for question_id in ["G-01", "G-02"]:
        per_question.append(
            {
                "id": question_id,
                "question": f"Question {question_id}",
                "question_type": "in_scope",
                "pipeline_error": None,
                "metrics": {
                    "retrieval_hit_rate": _metric_result(
                        passed=question_id not in retrieval_failures,
                        expected=["14 CFR Part 91 91.155"],
                        actual=["14 CFR Part 91 91.155"],
                    ),
                    "citation_accuracy": _metric_result(
                        passed=question_id not in citation_failures,
                        expected=["14 CFR Part 91 91.155"],
                        actual="14 CFR Part 91 91.155",
                    ),
                    "answer_correctness": _metric_result(
                        passed=question_id not in answer_failures,
                        expected=["expected fact"],
                        actual={"missing_key_facts": ["expected fact"]},
                    ),
                },
            }
        )

    per_question.append(
        {
            "id": "R-01",
            "question": "Out of scope question",
            "question_type": "out_of_scope",
            "pipeline_error": None,
            "metrics": {
                "correct_refusal_rate": _metric_result(
                    passed="R-01" not in refusal_failures,
                    expected="fallback answer with no citation",
                    actual="none",
                )
            },
        }
    )

    return {
        "summary": {
            "retrieval_hit_rate": _summary(2 - len(retrieval_failures), 2),
            "citation_accuracy": _summary(2 - len(citation_failures), 2),
            "answer_correctness": _summary(2 - len(answer_failures), 2),
            "correct_refusal_rate": _summary(1 - len(refusal_failures), 1),
        },
        "per_question": per_question,
    }


def test_scorecard_passes_when_metrics_and_failures_match_baseline():
    baseline = _baseline(answer_passed=1, answer_failures=["G-01"])
    scorecard = _scorecard(answer_failures=["G-01"])

    report = compare_scorecard_to_baseline(scorecard, baseline)

    assert report["passed"] is True


def test_metric_drop_fails_gate():
    baseline = _baseline(answer_passed=2)
    scorecard = _scorecard(answer_failures=["G-01"])

    report = compare_scorecard_to_baseline(scorecard, baseline)

    assert report["passed"] is False
    assert report["metric_regressions"] == [
        {
            "metric": "answer_correctness",
            "baseline": "2/2",
            "current": "1/2",
            "drop": 1,
        }
    ]


def test_new_failure_fails_even_when_metric_count_holds():
    baseline = _baseline(answer_passed=1, answer_failures=["G-01"])
    scorecard = _scorecard(answer_failures=["G-02"])

    report = compare_scorecard_to_baseline(scorecard, baseline)

    assert report["passed"] is False
    assert report["metric_regressions"] == []
    assert report["new_failures"][0]["id"] == "G-02"
    assert report["new_failures"][0]["metric"] == "answer_correctness"


def test_pipeline_error_fails_gate_even_if_metric_counts_hold():
    baseline = _baseline()
    scorecard = _scorecard()
    scorecard["per_question"][0]["pipeline_error"] = "TimeoutError: model timed out"

    report = compare_scorecard_to_baseline(scorecard, baseline)

    assert report["passed"] is False
    assert report["pipeline_errors"] == [
        {
            "id": "G-01",
            "question": "Question G-01",
            "error": "TimeoutError: model timed out",
        }
    ]


def test_proposed_baseline_cannot_lower_base_metric_count():
    base = _baseline(answer_passed=2)
    proposed = _baseline(answer_passed=1, answer_failures=["G-01"])

    report = compare_proposed_baseline_to_base(proposed, base)

    assert report["passed"] is False
    assert report["lowering_errors"][0]["metric"] == "answer_correctness"


def test_proposed_baseline_cannot_newly_accept_failure():
    base = _baseline(answer_passed=1, answer_failures=["G-01"])
    proposed = _baseline(answer_passed=1, answer_failures=["G-02"])

    report = compare_proposed_baseline_to_base(proposed, base)

    assert report["passed"] is False
    assert report["new_accepted_failures"] == [
        {"metric": "answer_correctness", "id": "G-02"}
    ]
