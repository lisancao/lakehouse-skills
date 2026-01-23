"""MLflow tracing for skill evaluation.

Shows what the agent saw, what it generated, and why.

Example output in MLflow UI:

┌─────────────────────────────────────────────────────────────┐
│ Run: sdp_eval_basic_medallion                               │
├─────────────────────────────────────────────────────────────┤
│ Traces:                                                     │
│                                                             │
│ ┌─ skill_evaluation (span)                                  │
│ │  ├─ skill_loaded: true                                    │
│ │  ├─ skill_name: SDP.md                                    │
│ │  ├─ skill_size: 14832 chars                               │
│ │  │                                                        │
│ │  ├─ ┌─ llm_call (span)                                    │
│ │  │  │  model: claude-sonnet-4-20250514                    │
│ │  │  │  input_tokens: 4521                                 │
│ │  │  │  output_tokens: 342                                 │
│ │  │  │                                                     │
│ │  │  │  [Input] ──────────────────────────                 │
│ │  │  │  System: You are an expert data engineer...         │
│ │  │  │                                                     │
│ │  │  │  # Reference Documentation                          │
│ │  │  │  Use the following documentation...                 │
│ │  │  │  [SKILL CONTENT - 14832 chars]                      │
│ │  │  │                                                     │
│ │  │  │  User: Write an SDP pipeline that:                  │
│ │  │  │  1. Loads orders from /data/orders.parquet...       │
│ │  │  │  ─────────────────────────────────────              │
│ │  │  │                                                     │
│ │  │  │  [Output] ─────────────────────────                 │
│ │  │  │  ```python                                          │
│ │  │  │  from typing import Any                             │
│ │  │  │  from pyspark import pipelines as dp                │
│ │  │  │  ...                                                │
│ │  │  │  ```                                                │
│ │  │  └────────────────────────────────────                 │
│ │  │                                                        │
│ │  ├─ ┌─ evaluation (span)                                  │
│ │  │  │  score: 1.0                                         │
│ │  │  │  passed: 8/8                                        │
│ │  │  │                                                     │
│ │  │  │  checks:                                            │
│ │  │  │    ✓ has_dp_import                                  │
│ │  │  │    ✓ has_spark_any                                  │
│ │  │  │    ✓ decorator_no_catalog                           │
│ │  │  │    ✓ spark_table_has_catalog                        │
│ │  │  │    ...                                              │
│ │  │  └────────────────────────────────────                 │
│ │  │                                                        │
│ └──┴────────────────────────────────────────────────────────┤
│                                                             │
│ Metrics:                                                    │
│   skill_score: 1.0                                          │
│   baseline_score: 0.25                                      │
│   delta: +0.75                                              │
│   latency_ms: 2341                                          │
│   total_tokens: 4863                                        │
└─────────────────────────────────────────────────────────────┘
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

try:
    import mlflow
    from mlflow import MlflowClient
    HAS_MLFLOW = True
except ImportError:
    mlflow = None
    HAS_MLFLOW = False


@dataclass
class TraceContext:
    """Context for a traced evaluation run."""
    skill_name: str | None
    skill_content: str | None
    case_name: str
    prompt: str


def traced_evaluation(
    case_name: str,
    prompt: str,
    skill_path: Path | None,
    run_fn: Callable,
    evaluate_fn: Callable,
) -> dict:
    """Run evaluation with full MLflow tracing.

    This captures:
    - What skill content was provided (if any)
    - The full LLM input/output
    - Evaluation results with per-check details
    - Timing and token usage

    Args:
        case_name: Test case identifier
        prompt: The task prompt
        skill_path: Path to skill file (None for baseline)
        run_fn: Function that calls the LLM (prompt, skill_content) -> response
        evaluate_fn: Function that evaluates output (code, checks) -> results

    Returns:
        Dict with response, evaluation results, and trace ID
    """
    if not HAS_MLFLOW:
        raise ImportError("mlflow required: pip install mlflow")

    # Load skill if provided
    skill_content = None
    skill_name = None
    if skill_path:
        skill_content = skill_path.read_text()
        skill_name = skill_path.name

    # Set up MLflow experiment
    mlflow.set_experiment("skill-evaluation")

    with mlflow.start_run(run_name=f"{case_name}_{'with_skill' if skill_path else 'baseline'}"):
        # Log parameters
        mlflow.log_param("case", case_name)
        mlflow.log_param("skill_name", skill_name or "none")
        mlflow.log_param("skill_loaded", skill_path is not None)
        mlflow.log_param("prompt_preview", prompt[:200])

        if skill_content:
            mlflow.log_param("skill_size_chars", len(skill_content))

        # Trace the LLM call
        with mlflow.start_span(name="llm_call") as span:
            response = run_fn(prompt, skill_content)

            span.set_inputs({
                "prompt": prompt,
                "skill_provided": skill_content is not None,
                "skill_preview": skill_content[:500] + "..." if skill_content else None,
            })
            span.set_outputs({
                "response_preview": response.raw_response[:500] + "...",
                "extracted_code_preview": response.extracted_code[:500] + "...",
            })

            # Log token usage
            mlflow.log_metric("input_tokens", response.input_tokens)
            mlflow.log_metric("output_tokens", response.output_tokens)
            mlflow.log_metric("total_tokens", response.input_tokens + response.output_tokens)

        # Trace the evaluation
        with mlflow.start_span(name="evaluation") as span:
            results = evaluate_fn(response.extracted_code)

            span.set_inputs({"code_length": len(response.extracted_code)})
            span.set_outputs({
                "score": results["summary"]["score"],
                "passed": results["summary"]["total_passed"],
                "total": results["summary"]["total_checks"],
            })

            # Log per-check results
            for category, data in results.items():
                if category == "summary":
                    continue
                for check in data["checks"]:
                    mlflow.log_metric(
                        f"check_{check.name}",
                        1.0 if check.passed else 0.0
                    )

        # Log overall metrics
        mlflow.log_metric("score", results["summary"]["score"])
        mlflow.log_metric("checks_passed", results["summary"]["total_passed"])
        mlflow.log_metric("checks_total", results["summary"]["total_checks"])

        # Log artifacts
        mlflow.log_text(response.raw_response, "raw_response.txt")
        mlflow.log_text(response.extracted_code, "extracted_code.py")
        if skill_content:
            mlflow.log_text(skill_content, "skill_content.md")

        run_id = mlflow.active_run().info.run_id

    return {
        "response": response,
        "results": results,
        "run_id": run_id,
        "trace_url": f"mlflow ui: http://localhost:5000/#/experiments/skill-evaluation/runs/{run_id}",
    }


def traced_comparison(
    case_name: str,
    prompt: str,
    skill_path: Path,
    run_fn: Callable,
    evaluate_fn: Callable,
) -> dict:
    """Run A/B comparison with tracing for both runs.

    Creates a parent run with two child runs:
    - baseline (no skill)
    - with_skill

    The parent run shows the delta.
    """
    if not HAS_MLFLOW:
        raise ImportError("mlflow required: pip install mlflow")

    mlflow.set_experiment("skill-evaluation")

    with mlflow.start_run(run_name=f"{case_name}_comparison"):
        mlflow.log_param("case", case_name)
        mlflow.log_param("skill", skill_path.name)
        mlflow.log_param("comparison_type", "skill_vs_baseline")

        # Run baseline (nested run)
        with mlflow.start_run(run_name="baseline", nested=True):
            with mlflow.start_span(name="baseline_llm_call"):
                baseline_response = run_fn(prompt, None)
            baseline_results = evaluate_fn(baseline_response.extracted_code)
            baseline_score = baseline_results["summary"]["score"]
            mlflow.log_metric("score", baseline_score)
            mlflow.log_text(baseline_response.extracted_code, "code.py")

        # Run with skill (nested run)
        skill_content = skill_path.read_text()
        with mlflow.start_run(run_name="with_skill", nested=True):
            with mlflow.start_span(name="skill_llm_call"):
                skill_response = run_fn(prompt, skill_content)
            skill_results = evaluate_fn(skill_response.extracted_code)
            skill_score = skill_results["summary"]["score"]
            mlflow.log_metric("score", skill_score)
            mlflow.log_text(skill_response.extracted_code, "code.py")

        # Log comparison metrics to parent
        delta = skill_score - baseline_score
        mlflow.log_metric("baseline_score", baseline_score)
        mlflow.log_metric("skill_score", skill_score)
        mlflow.log_metric("delta", delta)
        mlflow.log_metric("improvement_pct", delta * 100)

        # Tag the result
        if delta > 0.05:
            mlflow.set_tag("result", "improved")
        elif delta < -0.05:
            mlflow.set_tag("result", "regressed")
        else:
            mlflow.set_tag("result", "neutral")

        parent_run_id = mlflow.active_run().info.run_id

    return {
        "baseline_score": baseline_score,
        "skill_score": skill_score,
        "delta": delta,
        "run_id": parent_run_id,
        "trace_url": f"http://localhost:5000/#/experiments/skill-evaluation/runs/{parent_run_id}",
    }


# Example usage showing what you'd see
EXAMPLE_TRACE_OUTPUT = """
╔══════════════════════════════════════════════════════════════════╗
║  MLflow Trace: basic_medallion_comparison                        ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Overview:                                                       ║
║  ┌────────────────┬───────────────┬──────────────┐               ║
║  │                │ Baseline      │ With Skill   │               ║
║  ├────────────────┼───────────────┼──────────────┤               ║
║  │ Score          │ 25%           │ 100%         │               ║
║  │ Checks passed  │ 2/8           │ 8/8          │               ║
║  │ Tokens used    │ 1,203         │ 5,847        │               ║
║  │ Latency        │ 1.2s          │ 2.8s         │               ║
║  └────────────────┴───────────────┴──────────────┘               ║
║                                                                  ║
║  Delta: +75% improvement                                         ║
║                                                                  ║
║  ─────────────────────────────────────────────────────────────   ║
║                                                                  ║
║  Drill-down: Baseline Run                                        ║
║  ┌──────────────────────────────────────────────────────────┐    ║
║  │ Input (no skill provided):                               │    ║
║  │   System: You are an expert data engineer...             │    ║
║  │   User: Write an SDP pipeline that loads orders...       │    ║
║  │                                                          │    ║
║  │ Output:                                                  │    ║
║  │   ```python                                              │    ║
║  │   from pyspark.sql import SparkSession                   │    ║
║  │                                                          │    ║
║  │   spark = SparkSession.builder.getOrCreate()  # WRONG    │    ║
║  │                                                          │    ║
║  │   def bronze_orders():                         # WRONG   │    ║
║  │       df = spark.read.parquet(...)            # no decorator │
║  │       df.write.saveAsTable(...)               # WRONG    │    ║
║  │   ```                                                    │    ║
║  │                                                          │    ║
║  │ Checks:                                                  │    ║
║  │   ✗ has_dp_import          (missing)                     │    ║
║  │   ✗ has_spark_any          (missing)                     │    ║
║  │   ✗ decorator_no_catalog   (missing)                     │    ║
║  │   ✗ spark_table_has_catalog (missing)                    │    ║
║  │   ✗ no_write_calls         (has .write)                  │    ║
║  │   ✗ no_saveastable         (has saveAsTable)             │    ║
║  │   ✓ has_typing_import      (n/a - didn't check)          │    ║
║  │   ✓ returns_dataframe      (n/a)                         │    ║
║  └──────────────────────────────────────────────────────────┘    ║
║                                                                  ║
║  ─────────────────────────────────────────────────────────────   ║
║                                                                  ║
║  Drill-down: With Skill Run                                      ║
║  ┌──────────────────────────────────────────────────────────┐    ║
║  │ Input (skill injected - 14,832 chars):                   │    ║
║  │   System: You are an expert data engineer...             │    ║
║  │                                                          │    ║
║  │   # Reference Documentation                              │    ║
║  │   ## What is SDP?                                        │    ║
║  │   ... [skill content] ...                                │    ║
║  │   ## Critical: Table Naming Convention                   │    ║
║  │   > Decorator names and spark.table() use DIFFERENT...   │    ║
║  │   ... [14,832 chars total] ...                           │    ║
║  │                                                          │    ║
║  │   User: Write an SDP pipeline that loads orders...       │    ║
║  │                                                          │    ║
║  │ Output:                                                  │    ║
║  │   ```python                                              │    ║
║  │   from typing import Any                        # ✓      │    ║
║  │   from pyspark import pipelines as dp           # ✓      │    ║
║  │                                                          │    ║
║  │   spark: Any                                    # ✓      │    ║
║  │                                                          │    ║
║  │   @dp.materialized_view(name="bronze.orders")   # ✓      │    ║
║  │   def bronze_orders():                                   │    ║
║  │       return spark.read.parquet(...)            # ✓      │    ║
║  │                                                          │    ║
║  │   @dp.materialized_view(name="silver.orders")   # ✓      │    ║
║  │   def silver_orders():                                   │    ║
║  │       return spark.table("iceberg.bronze...")   # ✓      │    ║
║  │   ```                                                    │    ║
║  │                                                          │    ║
║  │ Checks:                                                  │    ║
║  │   ✓ has_dp_import                                        │    ║
║  │   ✓ has_spark_any                                        │    ║
║  │   ✓ has_typing_import                                    │    ║
║  │   ✓ decorator_no_catalog                                 │    ║
║  │   ✓ spark_table_has_catalog                              │    ║
║  │   ✓ no_write_calls                                       │    ║
║  │   ✓ no_saveastable                                       │    ║
║  │   ✓ returns_dataframe                                    │    ║
║  └──────────────────────────────────────────────────────────┘    ║
║                                                                  ║
║  Insight: The skill's "Critical: Table Naming Convention"        ║
║  section directly led to correct decorator vs spark.table()      ║
║  usage - the #1 source of errors in baseline.                    ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""


if __name__ == "__main__":
    print("MLflow tracing example output:")
    print(EXAMPLE_TRACE_OUTPUT)
