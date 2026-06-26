# compare_eval_baseline.py
# Regression gate for FARSight evaluation results. It compares a fresh
# eval run against the committed baseline and fails when quality drops or
# when a new question fails under an otherwise unchanged aggregate score.

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from evaluation.eval_runner import (
    DEFAULT_RESULTS_FILE,
    TEST_QUERY_FILE,
    apply_current_expectations,
    load_evaluation_results,
    score_evaluation_results,
)
from evaluation.verify_test_query_citations import load_test_queries

BASELINE_FILE = Path("evaluation/eval_baseline.json")
METRIC_NAMES = [
    "retrieval_hit_rate",
    "citation_accuracy",
    "answer_correctness",
    "correct_refusal_rate",
]


def load_json_file(path: Path) -> dict:
    return json.loads(path.read_text())


def metric_count(metric_summary: dict) -> str:
    return f"{metric_summary['passed']}/{metric_summary['total']}"


def baseline_metric_count(metric_baseline: dict) -> str:
    return f"{metric_baseline['passed']}/{metric_baseline['total']}"


def accepted_failure_ids(metric_baseline: dict) -> set[str]:
    return {
        failure["id"]
        for failure in metric_baseline.get("accepted_failures", [])
    }


def failed_questions_by_metric(scorecard: dict, metric_name: str) -> dict[str, dict]:
    failures = {}
    for question_score in scorecard["per_question"]:
        metric_result = question_score["metrics"].get(metric_name)
        if not metric_result or metric_result["passed"]:
            continue
        failures[question_score["id"]] = {
            "id": question_score["id"],
            "question": question_score["question"],
            "metric": metric_name,
            "expected": metric_result["expected"],
            "actual": metric_result["actual"],
            "pipeline_error": question_score.get("pipeline_error"),
        }
    return failures


def pipeline_errors(scorecard: dict) -> list[dict]:
    return [
        {
            "id": question_score["id"],
            "question": question_score["question"],
            "error": question_score["pipeline_error"],
        }
        for question_score in scorecard["per_question"]
        if question_score.get("pipeline_error")
    ]


def compare_scorecard_to_baseline(scorecard: dict, baseline: dict) -> dict:
    metric_regressions = []
    total_mismatches = []
    new_failures = []

    for metric_name in METRIC_NAMES:
        current_metric = scorecard["summary"][metric_name]
        baseline_metric = baseline["metrics"][metric_name]

        if current_metric["total"] != baseline_metric["total"]:
            total_mismatches.append(
                {
                    "metric": metric_name,
                    "baseline": baseline_metric_count(baseline_metric),
                    "current": metric_count(current_metric),
                }
            )

        if current_metric["passed"] < baseline_metric["passed"]:
            metric_regressions.append(
                {
                    "metric": metric_name,
                    "baseline": baseline_metric_count(baseline_metric),
                    "current": metric_count(current_metric),
                    "drop": baseline_metric["passed"] - current_metric["passed"],
                }
            )

        current_failures = failed_questions_by_metric(scorecard, metric_name)
        accepted_ids = accepted_failure_ids(baseline_metric)
        for question_id in sorted(set(current_failures) - accepted_ids):
            new_failures.append(current_failures[question_id])

    errors = pipeline_errors(scorecard)
    return {
        "passed": not (
            metric_regressions
            or total_mismatches
            or new_failures
            or errors
        ),
        "metric_regressions": metric_regressions,
        "total_mismatches": total_mismatches,
        "new_failures": new_failures,
        "pipeline_errors": errors,
    }


def compare_proposed_baseline_to_base(proposed_baseline: dict, base_baseline: dict) -> dict:
    lowering_errors = []
    new_accepted_failures = []

    for metric_name in METRIC_NAMES:
        proposed_metric = proposed_baseline["metrics"][metric_name]
        base_metric = base_baseline["metrics"][metric_name]

        if proposed_metric["total"] != base_metric["total"]:
            lowering_errors.append(
                {
                    "metric": metric_name,
                    "reason": "metric total changed",
                    "base": baseline_metric_count(base_metric),
                    "proposed": baseline_metric_count(proposed_metric),
                }
            )

        if proposed_metric["passed"] < base_metric["passed"]:
            lowering_errors.append(
                {
                    "metric": metric_name,
                    "reason": "proposed baseline lowers accepted pass count",
                    "base": baseline_metric_count(base_metric),
                    "proposed": baseline_metric_count(proposed_metric),
                }
            )

        added_failures = (
            accepted_failure_ids(proposed_metric)
            - accepted_failure_ids(base_metric)
        )
        for question_id in sorted(added_failures):
            new_accepted_failures.append(
                {
                    "metric": metric_name,
                    "id": question_id,
                }
            )

    return {
        "passed": not (lowering_errors or new_accepted_failures),
        "lowering_errors": lowering_errors,
        "new_accepted_failures": new_accepted_failures,
    }


def current_results_meet_proposed_baseline(
    scorecard: dict,
    proposed_baseline: dict,
) -> dict:
    return compare_scorecard_to_baseline(scorecard, proposed_baseline)


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def format_new_failure(failure: dict) -> str:
    lines = [
        f"- {failure['metric']}: {failure['id']} — {failure['question']}",
        f"  expected: {compact_json(failure['expected'])}",
        f"  actual: {compact_json(failure['actual'])}",
    ]
    if failure.get("pipeline_error"):
        lines.append(f"  pipeline error: {failure['pipeline_error']}")
    return "\n".join(lines)


def print_gate_report(
    scorecard: dict,
    base_baseline: dict,
    regression_report: dict,
    baseline_integrity_report: dict | None,
    proposed_baseline_report: dict | None,
) -> None:
    print("\n=== evaluation regression gate ===")
    print(f"baseline: {base_baseline['name']}")
    print("\nmetric summary:")
    for metric_name in METRIC_NAMES:
        current_metric = scorecard["summary"][metric_name]
        baseline_metric = base_baseline["metrics"][metric_name]
        print(
            f"  {metric_name}: current {metric_count(current_metric)} "
            f"vs baseline {baseline_metric_count(baseline_metric)}"
        )

    reports_passed = regression_report["passed"]
    if baseline_integrity_report:
        reports_passed = reports_passed and baseline_integrity_report["passed"]
    if proposed_baseline_report:
        reports_passed = reports_passed and proposed_baseline_report["passed"]

    if reports_passed:
        print("\nPASS — no metric dropped and no new question failures appeared.")
        return

    print("\nFAIL — evaluation regressed against the committed baseline.")

    if regression_report["metric_regressions"]:
        print("\nmetric regressions:")
        for regression in regression_report["metric_regressions"]:
            print(
                f"- {regression['metric']}: baseline {regression['baseline']}, "
                f"current {regression['current']} (-{regression['drop']})"
            )

    if regression_report["new_failures"]:
        print("\nnew question failures:")
        for failure in regression_report["new_failures"]:
            print(format_new_failure(failure))

    if regression_report["pipeline_errors"]:
        print("\npipeline errors:")
        for error in regression_report["pipeline_errors"]:
            print(f"- {error['id']} — {error['question']}: {error['error']}")

    if regression_report["total_mismatches"]:
        print("\nmetric total mismatches:")
        for mismatch in regression_report["total_mismatches"]:
            print(
                f"- {mismatch['metric']}: baseline {mismatch['baseline']}, "
                f"current {mismatch['current']}"
            )

    if baseline_integrity_report and not baseline_integrity_report["passed"]:
        print("\nproposed baseline cannot lower the base-branch baseline:")
        for error in baseline_integrity_report["lowering_errors"]:
            print(
                f"- {error['metric']}: {error['reason']} "
                f"(base {error['base']}, proposed {error['proposed']})"
            )
        for failure in baseline_integrity_report["new_accepted_failures"]:
            print(
                f"- {failure['metric']}: proposed baseline newly accepts "
                f"{failure['id']}"
            )

    if proposed_baseline_report and not proposed_baseline_report["passed"]:
        print("\ncurrent results do not meet the proposed baseline:")
        for regression in proposed_baseline_report["metric_regressions"]:
            print(
                f"- {regression['metric']}: proposed "
                f"{regression['baseline']}, current {regression['current']}"
            )
        for failure in proposed_baseline_report["new_failures"]:
            print(format_new_failure(failure))


def build_markdown_summary(
    scorecard: dict,
    base_baseline: dict,
    regression_report: dict,
    baseline_integrity_report: dict | None,
    proposed_baseline_report: dict | None,
) -> str:
    status = "PASS" if (
        regression_report["passed"]
        and (not baseline_integrity_report or baseline_integrity_report["passed"])
        and (not proposed_baseline_report or proposed_baseline_report["passed"])
    ) else "FAIL"

    lines = [
        f"## Evaluation Regression Gate: {status}",
        "",
        f"Baseline: `{base_baseline['name']}`",
        "",
        "| Metric | Current | Baseline |",
        "|---|---:|---:|",
    ]
    for metric_name in METRIC_NAMES:
        lines.append(
            f"| `{metric_name}` | "
            f"{metric_count(scorecard['summary'][metric_name])} | "
            f"{baseline_metric_count(base_baseline['metrics'][metric_name])} |"
        )

    if status == "PASS":
        lines.extend(["", "No metric dropped and no new question failures appeared."])
        return "\n".join(lines) + "\n"

    lines.append("")
    if regression_report["metric_regressions"]:
        lines.append("### Metric Regressions")
        for regression in regression_report["metric_regressions"]:
            lines.append(
                f"- `{regression['metric']}` dropped from "
                f"{regression['baseline']} to {regression['current']}."
            )

    if regression_report["new_failures"]:
        lines.append("### New Question Failures")
        for failure in regression_report["new_failures"]:
            lines.append(
                f"- `{failure['metric']}` `{failure['id']}`: "
                f"{failure['question']}"
            )

    if baseline_integrity_report and not baseline_integrity_report["passed"]:
        lines.append("### Baseline Integrity")
        for error in baseline_integrity_report["lowering_errors"]:
            lines.append(
                f"- `{error['metric']}` {error['reason']}: "
                f"base {error['base']}, proposed {error['proposed']}."
            )
        for failure in baseline_integrity_report["new_accepted_failures"]:
            lines.append(
                f"- `{failure['metric']}` newly accepts `{failure['id']}`."
            )

    return "\n".join(lines) + "\n"


def score_results_file(results_file: Path) -> dict:
    results_payload = load_evaluation_results(results_file)
    results_payload = apply_current_expectations(
        results_payload,
        load_test_queries(TEST_QUERY_FILE),
    )
    return score_evaluation_results(results_payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare eval results against the committed regression baseline."
    )
    parser.add_argument(
        "--results-file",
        type=Path,
        default=DEFAULT_RESULTS_FILE,
        help="Evaluation results file produced by evaluation.eval_runner.",
    )
    parser.add_argument(
        "--baseline-file",
        type=Path,
        default=BASELINE_FILE,
        help="Baseline to compare against. In CI this should be the base branch file.",
    )
    parser.add_argument(
        "--proposed-baseline-file",
        type=Path,
        default=None,
        help="Optional PR baseline file; checked so a PR cannot lower the baseline.",
    )
    parser.add_argument(
        "--summary-file",
        type=Path,
        default=None,
        help="Optional Markdown summary file, e.g. GitHub Actions step summary.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scorecard = score_results_file(args.results_file)
    base_baseline = load_json_file(args.baseline_file)
    regression_report = compare_scorecard_to_baseline(scorecard, base_baseline)

    baseline_integrity_report = None
    proposed_baseline_report = None
    if args.proposed_baseline_file:
        proposed_baseline = load_json_file(args.proposed_baseline_file)
        baseline_integrity_report = compare_proposed_baseline_to_base(
            proposed_baseline,
            base_baseline,
        )
        proposed_baseline_report = current_results_meet_proposed_baseline(
            scorecard,
            proposed_baseline,
        )

    print_gate_report(
        scorecard,
        base_baseline,
        regression_report,
        baseline_integrity_report,
        proposed_baseline_report,
    )

    if args.summary_file:
        args.summary_file.parent.mkdir(parents=True, exist_ok=True)
        args.summary_file.write_text(
            build_markdown_summary(
                scorecard,
                base_baseline,
                regression_report,
                baseline_integrity_report,
                proposed_baseline_report,
            )
        )

    gate_passed = (
        regression_report["passed"]
        and (not baseline_integrity_report or baseline_integrity_report["passed"])
        and (not proposed_baseline_report or proposed_baseline_report["passed"])
    )
    if not gate_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
