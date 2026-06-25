# eval_runner.py
# Runs the FARSight test query set through retrieval and answer generation,
# saves raw pipeline output, then scores the saved results.

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from azure.ai.inference.models import SystemMessage, UserMessage
from dotenv import load_dotenv

from evaluation.verify_test_query_citations import (
    CitationReference,
    load_test_queries,
    parse_citation_references,
)
from src.answer_generator import (
    build_chat_client,
    generate_cited_answer,
    parse_model_json_response,
)
from src.regulation_retriever import (
    DEFAULT_CHUNKS_TO_RETRIEVE,
    retrieve_relevant_regulation_chunks,
)

TEST_QUERY_FILE = Path("evaluation/test_queries.jsonl")
DEFAULT_RESULTS_FILE = Path("evaluation/eval_results.json")

ANSWER_JUDGE_SYSTEM_PROMPT = """\
You are a strict evaluator for FARSight, a FAA regulation question-answering tool.

You will receive:
- a pilot question
- the expected key facts
- the generated answer summary
- the generated verbatim excerpt, if any

Decide whether the generated answer contains every expected key fact.
Count equivalent wording as present, including common aviation abbreviations
and unit expansions such as "SM" and "statute miles". Do not give credit for
facts that are only implied, absent, contradicted, or outside the generated
answer text.

Respond with JSON only, in exactly this shape:
{
  "answer_is_correct": true or false,
  "missing_key_facts": ["any expected key facts that are absent"],
  "reason": "one short sentence"
}
"""


def citation_reference_label(reference: CitationReference) -> str:
    return f"{reference.document} {reference.section_number}"


def citation_from_answer_label(answer: dict | None) -> str:
    if not answer or not answer.get("citation"):
        return "none"
    citation = answer["citation"]
    if not citation.get("available", True):
        return "unavailable"
    return f"{citation.get('document')} {citation.get('section_number')}"


def unique_labels(labels: list[str]) -> list[str]:
    seen = set()
    unique = []
    for label in labels:
        if label in seen:
            continue
        seen.add(label)
        unique.append(label)
    return unique


def chunk_matches_reference(chunk: dict, reference: CitationReference) -> bool:
    return (
        chunk.get("document") == reference.document
        and chunk.get("section_number") == reference.section_number
    )


def answer_citation_matches_reference(answer: dict | None, reference: CitationReference) -> bool:
    if not answer or not answer.get("citation"):
        return False
    citation = answer["citation"]
    if not citation.get("available", True):
        return False
    return (
        citation.get("document") == reference.document
        and citation.get("section_number") == reference.section_number
    )


def expected_references_for_result(result: dict) -> list[CitationReference]:
    return parse_citation_references(result.get("expected_citation"))


def retrieved_citation_labels(result: dict) -> list[str]:
    return unique_labels(
        [
            f"{chunk.get('document')} {chunk.get('section_number')}"
            for chunk in result.get("retrieved_chunks", [])
        ]
    )


def result_has_fallback_answer(result: dict) -> bool:
    answer = result.get("answer") or {}
    return answer.get("answer_was_found") is False and not answer.get("citation")


def compact_chunk_for_results(chunk: dict, rank: int) -> dict:
    stored_chunk = dict(chunk)
    stored_chunk["rank"] = rank
    return stored_chunk


def run_query_through_pipeline(
    query: dict,
    chunks_to_retrieve: int = DEFAULT_CHUNKS_TO_RETRIEVE,
    retrieve_chunks: Callable[[str, int], list[dict]] = retrieve_relevant_regulation_chunks,
    generate_answer: Callable[[str, list[dict]], dict] = generate_cited_answer,
) -> dict:
    result = {
        "id": query["id"],
        "question": query["question"],
        "question_type": query["question_type"],
        "retrieval_type": query["retrieval_type"],
        "expected_key_facts": query["expected_key_facts"],
        "expected_citation": query["expected_citation"],
        "notes": query["notes"],
        "retrieved_chunks": [],
        "answer": None,
        "pipeline_error": None,
    }

    try:
        retrieved_chunks = retrieve_chunks(query["question"], chunks_to_retrieve)
        result["retrieved_chunks"] = [
            compact_chunk_for_results(chunk, rank)
            for rank, chunk in enumerate(retrieved_chunks, start=1)
        ]
        result["answer"] = generate_answer(query["question"], retrieved_chunks)
    except Exception as error:  # noqa: BLE001 - eval should record per-query failures.
        result["pipeline_error"] = f"{type(error).__name__}: {error}"

    return result


def run_evaluation_pipeline(
    test_queries: list[dict],
    chunks_to_retrieve: int = DEFAULT_CHUNKS_TO_RETRIEVE,
    retrieve_chunks: Callable[[str, int], list[dict]] = retrieve_relevant_regulation_chunks,
    generate_answer: Callable[[str, list[dict]], dict] = generate_cited_answer,
    progress_callback: Callable[[int, int, dict], None] | None = None,
) -> dict:
    results = []
    for index, query in enumerate(test_queries, start=1):
        if progress_callback:
            progress_callback(index, len(test_queries), query)
        results.append(
            run_query_through_pipeline(
                query,
                chunks_to_retrieve=chunks_to_retrieve,
                retrieve_chunks=retrieve_chunks,
                generate_answer=generate_answer,
            )
        )

    return {
        "metadata": {
            "generated_at": datetime.now(UTC).isoformat(),
            "test_query_file": str(TEST_QUERY_FILE),
            "chunks_to_retrieve": chunks_to_retrieve,
            "result_count": len(results),
        },
        "results": results,
    }


def save_evaluation_results(results_payload: dict, results_file: Path) -> None:
    results_file.parent.mkdir(parents=True, exist_ok=True)
    results_file.write_text(json.dumps(results_payload, indent=2) + "\n")


def load_evaluation_results(results_file: Path) -> dict:
    return json.loads(results_file.read_text())


def answer_text_for_judging(answer: dict | None) -> str:
    if not answer or not answer.get("answer_was_found"):
        return ""
    answer_parts = [
        answer.get("plain_language_summary") or "",
        answer.get("verbatim_excerpt") or "",
    ]
    return "\n\n".join(part.strip() for part in answer_parts if part and part.strip())


def build_failed_answer_judgment(result: dict, reason: str) -> dict:
    return {
        "answer_is_correct": False,
        "missing_key_facts": result.get("expected_key_facts", []),
        "reason": reason,
    }


def judge_answer_correctness(result: dict) -> dict:
    answer_text = answer_text_for_judging(result.get("answer"))
    if not answer_text:
        return build_failed_answer_judgment(result, "no generated answer to judge")

    load_dotenv()
    expected_key_facts = result["expected_key_facts"]
    user_message = {
        "question": result["question"],
        "expected_key_facts": expected_key_facts,
        "generated_answer_text": answer_text,
    }

    try:
        response = build_chat_client().complete(
            messages=[
                SystemMessage(content=ANSWER_JUDGE_SYSTEM_PROMPT),
                UserMessage(content=json.dumps(user_message, indent=2)),
            ]
        )
        model_reply = response.choices[0].message.content
        judgment = parse_model_json_response(model_reply)
    except Exception as error:  # noqa: BLE001 - judge failures should be scorecard-visible.
        return build_failed_answer_judgment(
            result,
            f"answer judge failed: {type(error).__name__}: {error}",
        )

    missing_key_facts = judgment.get("missing_key_facts", [])
    if not isinstance(missing_key_facts, list):
        missing_key_facts = expected_key_facts

    return {
        "answer_is_correct": judgment.get("answer_is_correct") is True,
        "missing_key_facts": missing_key_facts,
        "reason": str(judgment.get("reason", "")).strip(),
    }


def score_retrieval_hit(result: dict) -> dict:
    expected_references = expected_references_for_result(result)
    matched_references = [
        reference
        for reference in expected_references
        if any(
            chunk_matches_reference(chunk, reference)
            for chunk in result.get("retrieved_chunks", [])
        )
    ]
    return {
        "passed": bool(matched_references),
        "expected": [citation_reference_label(reference) for reference in expected_references],
        "actual": retrieved_citation_labels(result),
        "matched": [citation_reference_label(reference) for reference in matched_references],
    }


def score_citation_accuracy(result: dict) -> dict:
    expected_references = expected_references_for_result(result)
    answer = result.get("answer")
    return {
        "passed": any(
            answer_citation_matches_reference(answer, reference)
            for reference in expected_references
        ),
        "expected": [citation_reference_label(reference) for reference in expected_references],
        "actual": citation_from_answer_label(answer),
    }


def score_answer_correctness(
    result: dict,
    answer_judge: Callable[[dict], dict] = judge_answer_correctness,
) -> dict:
    judgment = result.get("answer_judgment")
    if not judgment:
        judgment = answer_judge(result)
        result["answer_judgment"] = judgment

    return {
        "passed": judgment["answer_is_correct"] is True,
        "expected": result.get("expected_key_facts", []),
        "actual": {
            "missing_key_facts": judgment.get("missing_key_facts", []),
            "reason": judgment.get("reason", ""),
        },
    }


def score_correct_refusal(result: dict) -> dict:
    return {
        "passed": result_has_fallback_answer(result),
        "expected": "fallback answer with no citation",
        "actual": citation_from_answer_label(result.get("answer")),
    }


def build_metric_summary(per_question_scores: list[dict]) -> dict:
    metric_names = [
        "retrieval_hit_rate",
        "citation_accuracy",
        "answer_correctness",
        "correct_refusal_rate",
    ]
    summary = {}
    for metric_name in metric_names:
        scored_items = [
            question_score["metrics"][metric_name]
            for question_score in per_question_scores
            if metric_name in question_score["metrics"]
        ]
        passed = sum(1 for item in scored_items if item["passed"])
        total = len(scored_items)
        summary[metric_name] = {
            "passed": passed,
            "total": total,
            "percentage": (passed / total * 100) if total else None,
        }
    return summary


def score_evaluation_results(
    results_payload: dict,
    answer_judge: Callable[[dict], dict] = judge_answer_correctness,
) -> dict:
    per_question_scores = []

    for result in results_payload["results"]:
        metrics = {}
        if result["question_type"] == "in_scope":
            metrics["retrieval_hit_rate"] = score_retrieval_hit(result)
            metrics["citation_accuracy"] = score_citation_accuracy(result)
            metrics["answer_correctness"] = score_answer_correctness(result, answer_judge)
        else:
            metrics["correct_refusal_rate"] = score_correct_refusal(result)

        per_question_scores.append(
            {
                "id": result["id"],
                "question": result["question"],
                "question_type": result["question_type"],
                "pipeline_error": result.get("pipeline_error"),
                "metrics": metrics,
            }
        )

    return {
        "metadata": results_payload.get("metadata", {}),
        "summary": build_metric_summary(per_question_scores),
        "per_question": per_question_scores,
    }


def format_metric_line(metric_name: str, metric_summary: dict) -> str:
    if metric_summary["total"] == 0:
        return f"{metric_name}: n/a"
    return (
        f"{metric_name}: {metric_summary['passed']}/{metric_summary['total']} "
        f"({metric_summary['percentage']:.1f}%)"
    )


def print_scorecard(scorecard: dict, results_file: Path) -> None:
    summary = scorecard["summary"]
    print("\n=== evaluation scorecard ===")
    print(f"results file: {results_file}")
    print(format_metric_line("retrieval hit rate", summary["retrieval_hit_rate"]))
    print(format_metric_line("citation accuracy", summary["citation_accuracy"]))
    print(format_metric_line("answer correctness", summary["answer_correctness"]))
    print(format_metric_line("correct refusal rate", summary["correct_refusal_rate"]))

    failures = []
    for question_score in scorecard["per_question"]:
        failed_metrics = {
            metric_name: metric_result
            for metric_name, metric_result in question_score["metrics"].items()
            if not metric_result["passed"]
        }
        if question_score.get("pipeline_error") or failed_metrics:
            failures.append((question_score, failed_metrics))

    if not failures:
        print("\nNo failures.")
        return

    print("\n=== failures ===")
    for question_score, failed_metrics in failures:
        print(f"\n{question_score['id']} - {question_score['question']}")
        if question_score.get("pipeline_error"):
            print(f"  pipeline error: {question_score['pipeline_error']}")
        for metric_name, metric_result in failed_metrics.items():
            print(f"  {metric_name}: FAIL")
            print(f"    expected: {metric_result['expected']}")
            print(f"    actual: {metric_result['actual']}")


def print_progress(index: int, total: int, query: dict) -> None:
    print(f"[{index}/{total}] {query['id']} {query['question']}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run and score the FARSight evaluation set.")
    parser.add_argument(
        "--score-only",
        action="store_true",
        help="Score an existing results file without running retrieval or generation.",
    )
    parser.add_argument(
        "--results-file",
        type=Path,
        default=DEFAULT_RESULTS_FILE,
        help="Where raw evaluation results are written or read.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_CHUNKS_TO_RETRIEVE,
        help="Number of chunks to retrieve for each question.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.score_only:
        results_payload = load_evaluation_results(args.results_file)
    else:
        test_queries = load_test_queries(TEST_QUERY_FILE)
        results_payload = run_evaluation_pipeline(
            test_queries,
            chunks_to_retrieve=args.top_k,
            progress_callback=print_progress,
        )
        # Save before scoring so raw retrieval/generation output survives
        # even if answer judging fails partway through.
        save_evaluation_results(results_payload, args.results_file)
        print(f"\nsaved raw results to {args.results_file}")

    scorecard = score_evaluation_results(results_payload)
    # Save again after scoring to cache answer-judge verdicts. That keeps
    # --score-only stable and avoids re-judging the same generated answers.
    save_evaluation_results(results_payload, args.results_file)
    print_scorecard(scorecard, args.results_file)


if __name__ == "__main__":
    main()
