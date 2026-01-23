# SDP Skill Evaluation

Measure whether the SDP skill actually helps AI produce correct code.

## Philosophy

No AI slop. Every check is:
- **Binary** - pass or fail, no 1-10 scores
- **Verifiable** - regex patterns you can inspect
- **Concrete** - tests specific skill requirements

## Structure

```
evals/sdp/
├── cases/              # Test cases (YAML)
│   ├── basic_medallion.yaml
│   ├── streaming_kafka.yaml
│   └── naming_gotcha.yaml
├── judges/             # Evaluation logic
│   └── pattern_judge.py
├── examples/           # Reference implementations
│   ├── good_basic.py   # Passes all checks
│   └── bad_basic.py    # Fails checks (common mistakes)
└── run_eval.py         # CLI runner
```

## Quick Start

```bash
# See what cases exist
python evals/sdp/run_eval.py --list

# See the prompt for a case
python evals/sdp/run_eval.py --case basic_medallion --show-prompt

# Evaluate a code file
python evals/sdp/run_eval.py --case basic_medallion --code examples/good_basic.py

# Evaluate inline code
python evals/sdp/run_eval.py --case basic_medallion --code-inline "from pyspark..."
```

## Test Cases

| Case | Tests |
|------|-------|
| `basic_medallion` | Core SDP: imports, spark:Any, naming conventions, no writes |
| `streaming_kafka` | @dp.table vs @dp.materialized_view, readStream, watermarks |
| `naming_gotcha` | The #1 confusion: decorator (no catalog) vs spark.table (has catalog) |

## What's Checked

### Syntax (must have)
- `from pyspark import pipelines as dp`
- `spark: Any` at module level
- `from typing import Any`

### Conventions (the key skill knowledge)
- Decorator: `@dp.materialized_view(name="silver.orders")` - NO catalog
- Read: `spark.table("iceberg.silver.orders")` - WITH catalog

### Anti-patterns (must NOT have)
- `.write.` or `saveAsTable` calls
- Catalog prefix in decorator names
- Short names in spark.table()

## Using with MLflow

```bash
# Install mlflow
pip install mlflow

# Run with tracking
python evals/sdp/run_eval.py --case basic_medallion --code output.py --mlflow

# View results
mlflow ui
```

MLflow logs:
- `overall_score` - % of checks passed
- `{category}_score` - score per check category
- `generated_code.py` - the evaluated code as artifact

## Adding New Cases

1. Create `cases/your_case.yaml`:

```yaml
skill: query-engines/spark/SDP.md

prompt: |
  Your prompt here...

checks:
  category_name:
    - name: check_name
      pattern: "regex pattern"
      required: true  # true = must match, false = must NOT match
      description: "What this checks"
```

2. Test it:
```bash
python run_eval.py --case your_case --show-prompt
python run_eval.py --case your_case --code examples/good_basic.py
```

## Interpreting Results

```
## syntax
  [PASS] has_dp_import
  [PASS] has_spark_any
  [PASS] has_typing_import

## conventions
  [PASS] decorator_no_catalog
  [FAIL] spark_table_has_catalog
         spark.table() uses catalog.database.table format

## Summary: 4/5 checks passed
Score: 80.0%
```

If a check fails, the description explains what's wrong. The pattern is visible in the YAML for debugging.

## Future Work

- [ ] Add syntax validation (does the code parse?)
- [ ] Add execution check (does it run in dry-run mode?)
- [ ] Add human feedback collection
- [ ] Compare skill versions (v1 vs v2)
