#!/usr/bin/env python3
"""SDP Skill Evaluation Runner.

Evaluates AI-generated code against SDP skill requirements.
Tracks results in MLflow for comparison across skill versions.

Usage:
    # Evaluate a single response
    python run_eval.py --case basic_medallion --code /path/to/generated.py

    # Evaluate with inline code
    python run_eval.py --case basic_medallion --code-inline "from pyspark..."

    # Run all cases against a model (requires API setup)
    python run_eval.py --all --model claude-3-5-sonnet

    # List available cases
    python run_eval.py --list
"""

import argparse
import sys
from pathlib import Path

import yaml

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from judges.pattern_judge import evaluate_code, format_results

CASES_DIR = Path(__file__).parent / "cases"


def load_case(case_name: str) -> dict:
    """Load a test case YAML file."""
    case_file = CASES_DIR / f"{case_name}.yaml"
    if not case_file.exists():
        raise FileNotFoundError(f"Case not found: {case_file}")

    with open(case_file) as f:
        return yaml.safe_load(f)


def list_cases() -> list[str]:
    """List available test cases."""
    return [f.stem for f in CASES_DIR.glob("*.yaml")]


def run_evaluation(case_name: str, code: str, track_mlflow: bool = False) -> dict:
    """Run evaluation for a single case.

    Args:
        case_name: Name of test case (without .yaml)
        code: Generated code to evaluate
        track_mlflow: Whether to log to MLflow

    Returns:
        Evaluation results dict
    """
    case = load_case(case_name)
    results = evaluate_code(code, case["checks"])

    if track_mlflow:
        try:
            import mlflow

            with mlflow.start_run(run_name=f"sdp_eval_{case_name}"):
                # Log the case info
                mlflow.log_param("case", case_name)
                mlflow.log_param("skill", case.get("skill", "unknown"))
                mlflow.log_param("prompt", case.get("prompt", "")[:500])

                # Log metrics per category
                for category, data in results.items():
                    if category == "summary":
                        mlflow.log_metric("overall_score", data["score"])
                        mlflow.log_metric("checks_passed", data["total_passed"])
                        mlflow.log_metric("checks_total", data["total_checks"])
                    else:
                        mlflow.log_metric(f"{category}_score", data["passed"] / data["total"])

                # Log the code as artifact
                mlflow.log_text(code, "generated_code.py")

        except ImportError:
            print("Warning: mlflow not installed, skipping tracking")

    return results


def main():
    parser = argparse.ArgumentParser(description="SDP Skill Evaluation")
    parser.add_argument("--case", help="Test case name (e.g., basic_medallion)")
    parser.add_argument("--code", help="Path to generated code file")
    parser.add_argument("--code-inline", help="Inline code string to evaluate")
    parser.add_argument("--list", action="store_true", help="List available cases")
    parser.add_argument("--mlflow", action="store_true", help="Track results in MLflow")
    parser.add_argument("--show-prompt", action="store_true", help="Show the prompt for a case")

    args = parser.parse_args()

    if args.list:
        print("Available test cases:")
        for case in list_cases():
            print(f"  - {case}")
        return

    if args.show_prompt and args.case:
        case = load_case(args.case)
        print(f"Prompt for {args.case}:")
        print("-" * 40)
        print(case.get("prompt", "No prompt defined"))
        return

    if not args.case:
        parser.error("--case is required (or use --list)")

    # Get code to evaluate
    if args.code_inline:
        code = args.code_inline
    elif args.code:
        with open(args.code) as f:
            code = f.read()
    else:
        parser.error("Either --code or --code-inline is required")

    # Run evaluation
    results = run_evaluation(args.case, code, track_mlflow=args.mlflow)

    # Print results
    print(format_results(results))

    # Exit with code based on pass/fail
    if results["summary"]["score"] < 1.0:
        sys.exit(1)


if __name__ == "__main__":
    main()
