# Evaluation Gate

FARSight's evaluation gate is a regression gate, not a perfection gate.

The committed baseline records the current accepted behavior of the system. A
pull request passes when it holds or improves that behavior. It fails when a
metric drops below baseline or when a new question fails, even if the aggregate
count happens to stay the same.

This is the MLOps contract for the project: changes cannot silently make
retrieval, citation accuracy, answer correctness, or refusal behavior worse.

## What Runs

The GitHub Actions workflow runs on pull requests to `main` and can also be
started manually with `workflow_dispatch`.

It does four things:

1. Runs the fast mocked test suite.
2. Runs the live evaluation set through retrieval and generation.
3. Scores the saved eval results.
4. Compares the scorecard against the committed baseline.

The workflow writes a readable summary to the GitHub Actions step summary and
uploads the raw eval results as an artifact.

## Baseline Philosophy

The baseline lives at:

```bash
evaluation/eval_baseline.json
```

It stores:

- the accepted metric counts
- the accepted failed question IDs for each metric
- the reason each accepted failure is not a merge blocker

The current accepted baseline is:

| Metric | Baseline |
|---|---:|
| Retrieval hit rate | 42/42 |
| Citation accuracy | 40/42 |
| Answer correctness | 28/42 |
| Correct refusal rate | 8/8 |

Known accepted limitations are documented in the baseline itself. The important
ones are:

- `G-21`: data limitation. The answer is in the 14 CFR § 61.23(d) duration
  table, but the parser does not reliably extract that table into chunk text.
- `G-34`: design limitation. The expected airway class and width facts span
  multiple AIM chunks, which conflicts with v1's single-excerpt verification
  design.

## What Blocks A Merge

The gate fails when any of these happen:

- a metric count drops below the committed baseline
- a new question fails for any metric
- the eval run records a pipeline error
- a PR tries to lower the baseline in the same change
- a PR adds a newly accepted baseline failure without first improving the live
  results that justify the change

The "new failure" check matters because aggregate counts can hide swaps. For
example, if `G-21` starts passing but `G-13` starts failing, citation accuracy
could stay at `40/42`. That is still a regression because the failure moved to a
new question.

## Secrets And Cost

The live eval hits Azure AI Search and Azure OpenAI, so GitHub Actions needs
these repository secrets:

```bash
AZURE_SEARCH_ENDPOINT
AZURE_SEARCH_ADMIN_KEY
AZURE_SEARCH_INDEX_NAME
AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY
AZURE_OPENAI_CHAT_DEPLOYMENT
AZURE_OPENAI_EMBEDDING_DEPLOYMENT
```

The workflow uses `pull_request`, not `pull_request_target`, so secrets are not
exposed to untrusted fork code. Live eval runs only for same-repository pull
requests or manual dispatch. Fork pull requests get a clear skip note instead
of access to Azure credentials.

The full eval is intentionally small enough to run on every trusted PR. It costs
some Azure usage, but the point of this project is to prove the quality system,
not merely keep local scripts around.

## Judge Stability

Answer correctness uses a model judge, so the gate reduces avoidable drift by
requesting deterministic JSON responses:

- temperature `0`
- JSON response format
- fixed seed

The eval runner also caches answer-judge verdicts in the saved results file.
CI still runs a fresh eval, but the scoring step does not re-judge answers it
has already judged in that run.

If the first answer-correctness judgment fails, the runner performs one narrow
second-pass recheck against the generated summary and verbatim excerpt. The
recheck does not lower the standard; it only asks whether the specific facts
reported missing are actually present in the text. This catches avoidable
false negatives from the judge while keeping genuine missing facts as failures.

This reduces judge noise. It does not pretend live model systems are perfectly
static forever.

## Updating The Baseline

Baseline updates must be intentional.

When a change legitimately improves a metric:

1. Run the full eval.
2. Inspect the scorecard and raw failures.
3. Edit `evaluation/eval_baseline.json` to raise the metric or remove accepted
   failures that no longer apply.
4. Commit the baseline change with the code or data change that earned it.

CI compares the PR against the base branch baseline, not the PR's edited
baseline alone. That means a pull request cannot make itself pass by lowering
the baseline or by newly accepting its own failures.

Useful commands:

```bash
python -m evaluation.eval_runner --results-file evaluation/eval_results.ci.json
python -m evaluation.compare_eval_baseline \
  --results-file evaluation/eval_results.ci.json \
  --baseline-file evaluation/eval_baseline.json
```

To test a proposed baseline update locally:

```bash
python -m evaluation.compare_eval_baseline \
  --results-file evaluation/eval_results.ci.json \
  --baseline-file path/to/base/eval_baseline.json \
  --proposed-baseline-file evaluation/eval_baseline.json
```
