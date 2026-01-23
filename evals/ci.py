#!/usr/bin/env python3
"""Skill Evaluation CI Pipeline.

Runs when skill files change to measure impact on agent performance.

Usage:
    # Evaluate a skill change (compares HEAD vs HEAD~1)
    python evals/ci.py --skill .claude/skills/query-engines/spark/SDP.md

    # Compare skill vs no-skill baseline
    python evals/ci.py --skill .claude/skills/query-engines/spark/SDP.md --baseline

    # Run all cases for a skill
    python evals/ci.py --skill .claude/skills/query-engines/spark/SDP.md --all-cases

    # Dry run (show what would be evaluated)
    python evals/ci.py --skill .claude/skills/query-engines/spark/SDP.md --dry-run

    # Use specific model
    python evals/ci.py --skill ... --model claude-3-5-haiku-20241022
"""

import argparse
import json
import sys
from pathlib import Path

# Skill to test case mapping
SKILL_CASES = {
    "SDP.md": ["basic_medallion", "streaming_kafka", "naming_gotcha"],
    "Kafka.md": [],  # Add when Kafka cases exist
    "Iceberg.md": [],
    "PySpark.md": [],
}


def find_cases_for_skill(skill_path: Path) -> list[Path]:
    """Find test cases that apply to a skill."""
    skill_name = skill_path.name
    cases_dir = Path(__file__).parent / "sdp" / "cases"

    if skill_name in SKILL_CASES:
        return [cases_dir / f"{case}.yaml" for case in SKILL_CASES[skill_name]]

    # Default: look for cases that reference the skill
    cases = []
    for case_file in cases_dir.glob("*.yaml"):
        content = case_file.read_text()
        if skill_name in content or skill_path.stem in content:
            cases.append(case_file)
    return cases


def format_result(result: dict) -> str:
    """Format a single result for display."""
    lines = []

    case = result.get("case", "unknown")
    delta = result.get("delta", 0)
    delta_pct = delta * 100

    if "baseline_score" in result:
        # Baseline comparison
        baseline = result["baseline_score"] * 100
        skill = result["skill_score"] * 100
        indicator = "+" if delta > 0 else "" if delta == 0 else ""

        lines.append(f"  {case}:")
        lines.append(f"    baseline: {baseline:.0f}%")
        lines.append(f"    w/skill:  {skill:.0f}% ({indicator}{delta_pct:+.0f}%)")
    else:
        # Version comparison
        old = result.get("old_score", 0) * 100
        new = result.get("new_score", 0) * 100
        indicator = "improved" if result.get("improved") else "regressed" if result.get("regressed") else "unchanged"

        lines.append(f"  {case}:")
        lines.append(f"    {result.get('old_version', 'old')}: {old:.0f}%")
        lines.append(f"    {result.get('new_version', 'new')}: {new:.0f}% ({indicator}, {delta_pct:+.0f}%)")

    return "\n".join(lines)


def run_baseline_comparison(
    skill_path: Path,
    cases: list[Path],
    model: str,
    api_key: str | None,
) -> list[dict]:
    """Run skill vs no-skill comparison."""
    from runner.compare import run_comparison

    results = []
    for case_path in cases:
        print(f"  Running {case_path.stem}...", file=sys.stderr)
        result = run_comparison(case_path, skill_path, model, api_key)
        results.append({
            "case": result.case_name,
            "baseline_score": result.baseline_score,
            "skill_score": result.skill_score,
            "delta": result.delta,
            "baseline_passed": result.baseline_passed,
            "baseline_total": result.baseline_total,
            "skill_passed": result.skill_passed,
            "skill_total": result.skill_total,
        })
    return results


def run_version_comparison(
    skill_path: Path,
    cases: list[Path],
    old_version: str,
    new_version: str,
    model: str,
    api_key: str | None,
) -> list[dict]:
    """Run old-version vs new-version comparison."""
    from runner.compare import run_version_comparison as _run_version_comparison

    results = []
    for case_path in cases:
        print(f"  Running {case_path.stem}...", file=sys.stderr)
        result = _run_version_comparison(
            case_path, skill_path, old_version, new_version, model, api_key
        )
        results.append(result)
    return results


def main():
    parser = argparse.ArgumentParser(description="Skill Evaluation CI")
    parser.add_argument("--skill", required=True, help="Path to skill file")
    parser.add_argument("--baseline", action="store_true", help="Compare skill vs no-skill")
    parser.add_argument("--old-version", default="HEAD~1", help="Git ref for old version")
    parser.add_argument("--new-version", default="HEAD", help="Git ref for new version")
    parser.add_argument("--model", default="claude-sonnet-4-20250514", help="Model to use")
    parser.add_argument("--all-cases", action="store_true", help="Run all cases for skill")
    parser.add_argument("--case", help="Run specific case only")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--fail-on-regression", action="store_true", help="Exit 1 if any regression")

    args = parser.parse_args()

    skill_path = Path(args.skill)
    if not skill_path.exists():
        print(f"Error: Skill not found: {skill_path}", file=sys.stderr)
        sys.exit(1)

    # Find applicable test cases
    if args.case:
        cases = [Path(__file__).parent / "sdp" / "cases" / f"{args.case}.yaml"]
    else:
        cases = find_cases_for_skill(skill_path)

    if not cases:
        print(f"No test cases found for {skill_path.name}", file=sys.stderr)
        sys.exit(0)

    # Dry run - just show what would happen
    if args.dry_run:
        print(f"Skill: {skill_path}")
        print(f"Model: {args.model}")
        print(f"Mode: {'baseline comparison' if args.baseline else 'version comparison'}")
        print(f"Cases ({len(cases)}):")
        for case in cases:
            print(f"  - {case.stem}")
        return

    print(f"Evaluating {skill_path.name} with {len(cases)} cases...", file=sys.stderr)

    # Run comparisons
    api_key = None  # Will use ANTHROPIC_API_KEY env var

    if args.baseline:
        results = run_baseline_comparison(skill_path, cases, args.model, api_key)
    else:
        results = run_version_comparison(
            skill_path, cases, args.old_version, args.new_version, args.model, api_key
        )

    # Output results
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"\n{'='*50}")
        print(f"Results for {skill_path.name}")
        print(f"{'='*50}")
        for result in results:
            print(format_result(result))

        # Summary
        avg_delta = sum(r["delta"] for r in results) / len(results) if results else 0
        print(f"\n{'='*50}")
        print(f"Average delta: {avg_delta*100:+.1f}%")

        if args.baseline:
            avg_baseline = sum(r["baseline_score"] for r in results) / len(results)
            avg_skill = sum(r["skill_score"] for r in results) / len(results)
            print(f"Baseline avg:  {avg_baseline*100:.1f}%")
            print(f"With skill:    {avg_skill*100:.1f}%")

    # Check for regressions
    if args.fail_on_regression:
        regressions = [r for r in results if r.get("delta", 0) < 0]
        if regressions:
            print(f"\n{len(regressions)} regression(s) detected!", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
