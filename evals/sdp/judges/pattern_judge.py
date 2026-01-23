"""Pattern-based judge for SDP skill evaluation.

Runs regex checks against generated code. Each check is binary (pass/fail).
No LLM-as-judge, no vibes - just concrete pattern matching.
"""

import re
from dataclasses import dataclass


@dataclass
class CheckResult:
    name: str
    passed: bool
    description: str
    pattern: str
    required: bool  # True = must match, False = must NOT match


def run_check(code: str, check: dict) -> CheckResult:
    """Run a single pattern check against code."""
    pattern = check["pattern"]
    required = check.get("required", True)
    description = check.get("description", "")

    matches = bool(re.search(pattern, code, re.MULTILINE))

    # required=True means pattern MUST match
    # required=False means pattern must NOT match
    if required:
        passed = matches
    else:
        passed = not matches

    return CheckResult(
        name=check["name"],
        passed=passed,
        description=description,
        pattern=pattern,
        required=required,
    )


def evaluate_code(code: str, checks: dict) -> dict:
    """Evaluate code against all check categories.

    Args:
        code: Generated Python code string
        checks: Dict of category -> list of checks from YAML

    Returns:
        Dict with results per category and overall score
    """
    results = {}
    total_passed = 0
    total_checks = 0

    for category, check_list in checks.items():
        category_results = []
        for check in check_list:
            result = run_check(code, check)
            category_results.append(result)
            total_checks += 1
            if result.passed:
                total_passed += 1

        results[category] = {
            "checks": category_results,
            "passed": sum(1 for r in category_results if r.passed),
            "total": len(category_results),
        }

    results["summary"] = {
        "total_passed": total_passed,
        "total_checks": total_checks,
        "score": total_passed / total_checks if total_checks > 0 else 0,
    }

    return results


def format_results(results: dict) -> str:
    """Format results as human-readable string."""
    lines = []

    for category, data in results.items():
        if category == "summary":
            continue

        lines.append(f"\n## {category}")
        for check in data["checks"]:
            status = "PASS" if check.passed else "FAIL"
            lines.append(f"  [{status}] {check.name}")
            if not check.passed and check.description:
                lines.append(f"         {check.description}")

    summary = results["summary"]
    lines.append(f"\n## Summary: {summary['total_passed']}/{summary['total_checks']} checks passed")
    lines.append(f"Score: {summary['score']:.1%}")

    return "\n".join(lines)
