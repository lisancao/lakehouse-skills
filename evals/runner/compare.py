"""A/B comparison - runs same prompt with and without skill, measures delta."""

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .agent import AgentResponse, load_skill, run_agent


@dataclass
class ComparisonResult:
    """Result of comparing skill vs no-skill performance."""
    case_name: str
    prompt: str

    # Scores (0.0 to 1.0)
    baseline_score: float
    skill_score: float
    delta: float  # skill_score - baseline_score

    # Details
    baseline_passed: int
    baseline_total: int
    skill_passed: int
    skill_total: int

    # Responses
    baseline_response: AgentResponse
    skill_response: AgentResponse

    # Check-level details
    baseline_checks: dict
    skill_checks: dict


def get_skill_version(skill_path: Path, version: str = "HEAD") -> str | None:
    """Get a specific version of a skill file from git.

    Args:
        skill_path: Path to skill file
        version: Git ref (HEAD, HEAD~1, commit hash, etc.)

    Returns:
        Skill content at that version, or None if not found
    """
    try:
        result = subprocess.run(
            ["git", "show", f"{version}:{skill_path}"],
            capture_output=True,
            text=True,
            cwd=skill_path.parent,
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except Exception:
        return None


def run_comparison(
    case_path: Path,
    skill_path: Path | None,
    model: str = "claude-sonnet-4-20250514",
    api_key: str | None = None,
) -> ComparisonResult:
    """Run A/B comparison for a single test case.

    Args:
        case_path: Path to test case YAML
        skill_path: Path to skill file (None for baseline-only)
        model: Model to use
        api_key: API key

    Returns:
        ComparisonResult with scores and delta
    """
    import yaml
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from sdp.judges.pattern_judge import evaluate_code

    # Load test case
    with open(case_path) as f:
        case = yaml.safe_load(f)

    prompt = case["prompt"]
    checks = case["checks"]
    case_name = case_path.stem

    # Run WITHOUT skill (baseline)
    baseline_response = run_agent(
        prompt=prompt,
        skill_content=None,
        model=model,
        api_key=api_key,
    )
    baseline_results = evaluate_code(baseline_response.extracted_code, checks)

    # Run WITH skill
    skill_content = load_skill(skill_path) if skill_path else None
    skill_response = run_agent(
        prompt=prompt,
        skill_content=skill_content,
        model=model,
        api_key=api_key,
    )
    skill_results = evaluate_code(skill_response.extracted_code, checks)

    # Calculate scores
    baseline_score = baseline_results["summary"]["score"]
    skill_score = skill_results["summary"]["score"]

    return ComparisonResult(
        case_name=case_name,
        prompt=prompt,
        baseline_score=baseline_score,
        skill_score=skill_score,
        delta=skill_score - baseline_score,
        baseline_passed=baseline_results["summary"]["total_passed"],
        baseline_total=baseline_results["summary"]["total_checks"],
        skill_passed=skill_results["summary"]["total_passed"],
        skill_total=skill_results["summary"]["total_checks"],
        baseline_response=baseline_response,
        skill_response=skill_response,
        baseline_checks=baseline_results,
        skill_checks=skill_results,
    )


def run_version_comparison(
    case_path: Path,
    skill_path: Path,
    old_version: str = "HEAD~1",
    new_version: str = "HEAD",
    model: str = "claude-sonnet-4-20250514",
    api_key: str | None = None,
) -> dict:
    """Compare two versions of a skill file.

    Args:
        case_path: Path to test case
        skill_path: Path to skill file
        old_version: Git ref for old version
        new_version: Git ref for new version
        model: Model to use
        api_key: API key

    Returns:
        Dict with old_score, new_score, delta
    """
    import yaml
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from sdp.judges.pattern_judge import evaluate_code

    with open(case_path) as f:
        case = yaml.safe_load(f)

    prompt = case["prompt"]
    checks = case["checks"]

    # Get skill versions
    old_skill = get_skill_version(skill_path, old_version)
    new_skill = get_skill_version(skill_path, new_version)

    if old_skill is None:
        # No previous version, just run new
        old_score = 0.0
        old_response = None
    else:
        old_response = run_agent(prompt, old_skill, model, api_key)
        old_results = evaluate_code(old_response.extracted_code, checks)
        old_score = old_results["summary"]["score"]

    new_response = run_agent(prompt, new_skill, model, api_key)
    new_results = evaluate_code(new_response.extracted_code, checks)
    new_score = new_results["summary"]["score"]

    return {
        "case": case_path.stem,
        "old_version": old_version,
        "new_version": new_version,
        "old_score": old_score,
        "new_score": new_score,
        "delta": new_score - old_score,
        "improved": new_score > old_score,
        "regressed": new_score < old_score,
    }
