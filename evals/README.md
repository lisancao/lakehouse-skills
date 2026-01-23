# Skill Evaluation System

Measure whether skill files actually improve agent performance. CI/CD for AI prompts.

## The Goal

```
Edit SDP.md → CI runs → "SDP.md v2: +15% vs v1, +40% vs baseline"
```

Changes to skill files should have measurable effects. Bad changes get caught before merge.

## How It Works

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  Skill Change   │────>│ Agent Runner │────>│   Judge     │
│  (SDP.md edit)  │     │ (Claude API) │     │ (patterns)  │
└─────────────────┘     └──────────────┘     └─────────────┘
                              │                     │
                              v                     v
                        ┌──────────────┐     ┌─────────────┐
                        │  Response A  │     │  Score: 75% │
                        │  (no skill)  │     │             │
                        └──────────────┘     └─────────────┘
                              │                     │
                              v                     v
                        ┌──────────────┐     ┌─────────────┐
                        │  Response B  │     │  Score: 95% │
                        │  (w/ skill)  │     │             │
                        └──────────────┘     └─────────────┘
                                                   │
                                                   v
                                            Delta: +20%
```

## Quick Start

### 1. Set up API key

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Run a baseline comparison

```bash
# Compare skill vs no-skill for SDP
python evals/ci.py \
  --skill .claude/skills/query-engines/spark/SDP.md \
  --baseline

# Output:
# ==================================================
# Results for SDP.md
# ==================================================
#   basic_medallion:
#     baseline: 25%
#     w/skill:  100% (+75%)
#   naming_gotcha:
#     baseline: 14%
#     w/skill:  86% (+72%)
# ==================================================
# Average delta: +73.5%
```

### 3. Run a version comparison

```bash
# Compare current version vs previous commit
python evals/ci.py \
  --skill .claude/skills/query-engines/spark/SDP.md \
  --old-version HEAD~1 \
  --new-version HEAD
```

### 4. Dry run (see what would execute)

```bash
python evals/ci.py \
  --skill .claude/skills/query-engines/spark/SDP.md \
  --dry-run
```

## CI/CD Integration

The GitHub Actions workflow (`.github/workflows/skill-eval.yml`) automatically:

1. **Triggers** on any change to `.claude/skills/**/*.md`
2. **Detects** which skills changed
3. **Runs** evaluations comparing HEAD vs HEAD~1
4. **Comments** on PRs with results
5. **Fails** the build if regressions are detected

### PR Comment Example

```
## Skill Evaluation: `SDP.md`

| Case | Delta | Status |
|------|-------|--------|
| basic_medallion | +5% | ✅ |
| streaming_kafka | +12% | ✅ |
| naming_gotcha | -3% | ❌ |

**Average: +4.7%**

⚠️ **Regression detected** - some test cases perform worse with this skill change.
```

## Structure

```
evals/
├── ci.py                 # Main CI pipeline script
├── runner/
│   ├── agent.py          # Claude API execution
│   └── compare.py        # A/B comparison logic
└── sdp/
    ├── cases/            # Test cases (YAML)
    │   ├── basic_medallion.yaml
    │   ├── streaming_kafka.yaml
    │   └── naming_gotcha.yaml
    ├── judges/
    │   └── pattern_judge.py
    └── run_eval.py       # Manual evaluation CLI
```

## Adding Test Cases for New Skills

1. Create test case YAML:

```yaml
# evals/kafka/cases/consumer_basic.yaml
skill: streaming/Kafka.md

prompt: |
  Write a Kafka consumer that reads from topic "events"
  and prints each message.

checks:
  required:
    - name: uses_confluent_kafka
      pattern: "confluent_kafka|confluent-kafka"
      required: true
      description: "Uses confluent-kafka library"

    - name: has_consumer_group
      pattern: "group\\.id"
      required: true
```

2. Map skill to cases in `ci.py`:

```python
SKILL_CASES = {
    "SDP.md": ["basic_medallion", "streaming_kafka", "naming_gotcha"],
    "Kafka.md": ["consumer_basic"],  # Add new mapping
}
```

3. Run locally to verify:

```bash
python evals/ci.py --skill .claude/skills/streaming/Kafka.md --baseline --dry-run
```

## What Makes Good Test Cases

### Good (concrete, verifiable)

```yaml
checks:
  - name: uses_correct_import
    pattern: "from pyspark import pipelines as dp"
    required: true

  - name: no_explicit_writes
    pattern: "\\.write\\."
    required: false  # Must NOT match
```

### Bad (vague, unmeasurable)

```yaml
checks:
  - name: code_quality
    llm_judge: "Rate code quality 1-10"  # NO - subjective
```

## Options

```bash
python evals/ci.py --help

Options:
  --skill PATH          Skill file to evaluate (required)
  --baseline            Compare skill vs no-skill
  --old-version REF     Git ref for old version (default: HEAD~1)
  --new-version REF     Git ref for new version (default: HEAD)
  --model MODEL         Model to use (default: claude-sonnet-4-20250514)
  --case NAME           Run specific case only
  --dry-run             Show what would run
  --json                Output JSON
  --fail-on-regression  Exit 1 if any regression
```

## Cost Considerations

Each evaluation run makes 2 API calls per test case (baseline + skill). With 3 cases:

- 6 API calls per skill evaluation
- ~$0.10-0.30 per run with Sonnet
- Use `--model claude-3-5-haiku-20241022` for cheaper testing

## Interpreting Results

| Delta | Meaning |
|-------|---------|
| +50% or more | Skill is highly effective |
| +10% to +50% | Skill helps meaningfully |
| -5% to +10% | Skill has minimal impact |
| Below -5% | Skill may be hurting (investigate) |

A good skill should show consistent positive delta across multiple test cases.
