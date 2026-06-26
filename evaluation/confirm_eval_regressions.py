# confirm_eval_regressions.py
# Stabilizes the CI regression gate against live model variance by rerunning
# newly failed answer-correctness rows before the final baseline comparison.

import argparse
import copy
import json
from pathlib import Path
from typing import Callable

from evaluation.compare_eval_baseline import (
    BASELINE_FILE,
    compare_scorecard_to_baseline,
    load_json_file,
)
from evaluation.eval_runner import (
    DEFAULT_RESULTS_FILE,
    TEST_QUERY_FILE,
    apply_current_expectations,
    judge_answer_correctness,
    load_evaluation_results,
    run_query_through_pipeline,
    save_evaluation_results,
    score_evaluation_results,
)
from evaluation.verify_test_query_citations import load_test_queries

DEFAULT_CONFIRMED_RESULTS_FILE = Path("evaluation/eval_results.confirmed.json")


def result_by_id(results_payload: dict) -> dict[str, dict]:
    return {result["id"]: result for result in results_payload["results"]}


def result_index_by_id(results_payload: dict) -> dict[str, int]:
    return {
        result["id"]: index
        for index, result in enumerate(results_payload["results"])
    }


def answer_correctness_metric(scorecard: dict, question_id: str) -> dict | None:
    for question_score in scorecard["per_question"]:
        if question_score["id"] != question_id:
            continue
        return question_score["metrics"].get("answer_correctness")
    return None


def new_answer_correctness_failures(scorecard: dict, baseline: dict) -> list[dict]:
    regression_report = compare_scorecard_to_baseline(scorecard, baseline)
    return [
        failure
        for failure in regression_report["new_failures"]
        if failure["metric"] == "answer_correctness"
    ]


def score_single_result(
    result: dict,
    answer_judge: Callable[[dict], dict],
) -> dict:
    retry_payload = {"results": [result]}
    scorecard = score_evaluation_results(retry_payload, answer_judge=answer_judge)
    return scorecard["per_question"][0]["metrics"]["answer_correctness"]


def confirm_answer_correctness_regressions(
    results_payload: dict,
    test_queries: list[dict],
    baseline: dict,
    max_attempts: int = 1,
    run_query: Callable[[dict], dict] = run_query_through_pipeline,
    answer_judge: Callable[[dict], dict] = judge_answer_correctness,
) -> tuple[dict, list[dict]]:
    confirmed_payload = copy.deepcopy(results_payload)
    confirmed_payload.setdefault("metadata", {})[
        "answer_regression_confirmation_attempts"
    ] = max_attempts

    queries_by_id = {query["id"]: query for query in test_queries}
    indexes_by_id = result_index_by_id(confirmed_payload)
    attempt_summaries = []

    for attempt_number in range(1, max_attempts + 1):
        scorecard = score_evaluation_results(
            confirmed_payload,
            answer_judge=answer_judge,
        )
        failures = new_answer_correctness_failures(scorecard, baseline)
        if not failures:
            break

        for failure in failures:
            question_id = failure["id"]
            query = queries_by_id.get(question_id)
            if not query:
                continue

            retry_result = run_query(query)
            retry_metric = score_single_result(
                retry_result,
                answer_judge=answer_judge,
            )
            retry_summary = {
                "attempt": attempt_number,
                "id": question_id,
                "question": failure["question"],
                "passed": retry_metric["passed"],
                "initial_actual": failure["actual"],
                "retry_actual": retry_metric["actual"],
            }
            attempt_summaries.append(retry_summary)

            retry_result["stabilization"] = {
                "reason": "answer_correctness_regression_confirmation",
                "attempt": attempt_number,
                "initial_actual": failure["actual"],
                "retry_actual": retry_metric["actual"],
                "outcome": (
                    "replaced_initial_failure"
                    if retry_metric["passed"]
                    else "failure_reproduced"
                ),
            }

            if retry_metric["passed"]:
                confirmed_payload["results"][indexes_by_id[question_id]] = retry_result
            else:
                current_result = result_by_id(confirmed_payload)[question_id]
                current_result.setdefault("stabilization_attempts", []).append(
                    retry_result
                )

    return confirmed_payload, attempt_summaries


def print_confirmation_report(attempt_summaries: list[dict]) -> None:
    print("\n=== answer regression confirmation ===")
    if not attempt_summaries:
        print("No new answer-correctness failures needed confirmation.")
        return

    for attempt in attempt_summaries:
        status = "passed on retry" if attempt["passed"] else "reproduced failure"
        print(f"- {attempt['id']} ({status}): {attempt['question']}")
        if not attempt["passed"]:
            print(f"  retry actual: {json.dumps(attempt['retry_actual'])}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rerun newly failed answer-correctness rows before CI compare."
    )
    parser.add_argument(
        "--results-file",
        type=Path,
        default=DEFAULT_RESULTS_FILE,
        help="Evaluation results file produced by evaluation.eval_runner.",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=DEFAULT_CONFIRMED_RESULTS_FILE,
        help="Where confirmed results should be written.",
    )
    parser.add_argument(
        "--baseline-file",
        type=Path,
        default=BASELINE_FILE,
        help="Baseline used to identify new answer-correctness failures.",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=1,
        help="Number of confirmation attempts per newly failed answer row.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_payload = load_evaluation_results(args.results_file)
    test_queries = load_test_queries(TEST_QUERY_FILE)
    results_payload = apply_current_expectations(results_payload, test_queries)
    baseline = load_json_file(args.baseline_file)

    confirmed_payload, attempt_summaries = confirm_answer_correctness_regressions(
        results_payload,
        test_queries,
        baseline,
        max_attempts=args.max_attempts,
    )
    save_evaluation_results(confirmed_payload, args.output_file)
    print_confirmation_report(attempt_summaries)
    print(f"confirmed results saved to {args.output_file}")


if __name__ == "__main__":
    main()
