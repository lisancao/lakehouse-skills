"""Agent runner - executes prompts against Claude API with optional skill context."""

import os
from dataclasses import dataclass
from pathlib import Path

try:
    import anthropic
except ImportError:
    anthropic = None


@dataclass
class AgentResponse:
    """Response from agent execution."""
    prompt: str
    skill_used: str | None
    raw_response: str
    extracted_code: str
    model: str
    input_tokens: int
    output_tokens: int


def load_skill(skill_path: str | Path | None) -> str | None:
    """Load skill markdown content."""
    if skill_path is None:
        return None

    path = Path(skill_path)
    if not path.exists():
        raise FileNotFoundError(f"Skill not found: {path}")

    return path.read_text()


def extract_code(response: str) -> str:
    """Extract Python code from agent response.

    Handles:
    - ```python ... ``` blocks
    - ``` ... ``` blocks
    - Raw code (if no blocks found)
    """
    import re

    # Try python-specific blocks first
    python_blocks = re.findall(r'```python\n(.*?)```', response, re.DOTALL)
    if python_blocks:
        return '\n\n'.join(python_blocks)

    # Try generic code blocks
    generic_blocks = re.findall(r'```\n(.*?)```', response, re.DOTALL)
    if generic_blocks:
        return '\n\n'.join(generic_blocks)

    # Fall back to full response (might be raw code)
    return response


def run_agent(
    prompt: str,
    skill_content: str | None = None,
    model: str = "claude-sonnet-4-20250514",
    api_key: str | None = None,
) -> AgentResponse:
    """Execute a prompt against Claude with optional skill context.

    Args:
        prompt: The task prompt
        skill_content: Optional skill markdown to include as context
        model: Model ID to use
        api_key: Anthropic API key (or uses ANTHROPIC_API_KEY env var)

    Returns:
        AgentResponse with raw and extracted code
    """
    if anthropic is None:
        raise ImportError("anthropic package required: pip install anthropic")

    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable required")

    client = anthropic.Anthropic(api_key=api_key)

    # Build system prompt
    system_parts = ["You are an expert data engineer. Write clean, production-ready code."]

    if skill_content:
        system_parts.append(
            "\n\n# Reference Documentation\n"
            "Use the following documentation to guide your implementation:\n\n"
            f"{skill_content}"
        )

    system_prompt = "\n".join(system_parts)

    # Call API
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    raw_response = response.content[0].text

    return AgentResponse(
        prompt=prompt,
        skill_used=skill_content[:100] + "..." if skill_content else None,
        raw_response=raw_response,
        extracted_code=extract_code(raw_response),
        model=model,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )


def run_agent_mock(
    prompt: str,
    skill_content: str | None = None,
    mock_response: str = "",
) -> AgentResponse:
    """Mock agent for testing without API calls."""
    return AgentResponse(
        prompt=prompt,
        skill_used="mock" if skill_content else None,
        raw_response=mock_response,
        extracted_code=extract_code(mock_response),
        model="mock",
        input_tokens=0,
        output_tokens=0,
    )
