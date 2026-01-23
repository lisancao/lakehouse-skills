# Contributing to lakehouse-skills

Thank you for your interest in contributing! This guide explains how to create and improve skills for AI assistants working with data engineering tools.

## What are Skills?

Skills are structured reference documents that help AI assistants generate accurate, production-ready code. Unlike generic documentation, skills are:

- **Context-aware** - Activated automatically based on user requests
- **Pattern-focused** - Emphasize working examples over theory
- **Error-aware** - Include common pitfalls and solutions
- **Project-specific** - Tailored to lakehouse-stack patterns

## Skill File Structure

Skills live in `.claude/skills/` and follow this format:

```markdown
# [Technology] - [Scope]

> One-line description of what this skill enables

## When to Use This Skill

Bullet list of scenarios that should trigger this skill.

## Quick Start

Minimal working example (copy-paste ready).

## Core Concepts

### [Concept 1]
Explanation with code example.

### [Concept 2]
Explanation with code example.

## Common Patterns

### [Pattern Name]
```python
# Complete, tested code
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| ... | ... | ... |

## Configuration

Project-specific settings and environment variables.

## See Also

- Links to related skills
- Links to official documentation
```

## Skill Quality Standards

### Code Examples Must Be

- **Complete** - Runnable without modification
- **Tested** - Verified against current library versions
- **Commented** - Explain non-obvious lines
- **Consistent** - Follow project conventions (see below)

### Data Engineering Conventions

```python
# PySpark imports
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as f
from pyspark.sql import types as t

# Naming
df_raw = ...      # DataFrames prefixed with df_
col_name = ...    # Column references are snake_case

# Medallion layers
iceberg.bronze.*  # Raw ingestion
iceberg.silver.*  # Cleaned/validated
iceberg.gold.*    # Aggregated/serving
```

### Documentation Style

- Use active voice ("Create a table" not "A table is created")
- Be concise - developers scan, not read
- Show, don't tell - code over prose
- Include version info for APIs that change frequently

## Creating a New Skill

### 1. Identify the Gap

Good skill candidates:

- Complex setup procedures (Unity Catalog, multi-cluster)
- Patterns that require multiple files/configs
- Common workflows with subtle gotchas
- Integration points between systems

### 2. Research Thoroughly

- Read official documentation
- Test all code examples yourself
- Note version-specific behavior
- Collect real error messages

### 3. Structure for Scanning

AI assistants (and humans) scan documents. Structure accordingly:

```markdown
## Section Header          ← Scannable
Brief context sentence.

### Subsection             ← More specific
`code snippet`             ← Immediate example

Detailed explanation...
```

### 4. Include Error Patterns

Real-world debugging context is invaluable:

```markdown
## Common Errors

### ClassNotFoundException: org.apache.iceberg.spark.SparkCatalog

**Cause:** Missing Iceberg JARs in Spark classpath.

**Solution:**
```bash
./scripts/download-jars.sh
```

Verify JARs exist:
```bash
ls jars/ | grep iceberg
```
```

### 5. Cross-Reference Related Skills

Skills work together. Link them:

```markdown
## See Also

- [SDP.md](SDP.md) - Declarative pipelines using these tables
- [Streaming.md](Streaming.md) - Kafka integration patterns
```

## Skill Ideas for lakehouse-stack

| Skill | Description | Priority |
|-------|-------------|----------|
| `Iceberg.md` | Table operations, time travel, maintenance | High |
| `Streaming.md` | Kafka → Spark structured streaming | High |
| `Unity-Catalog.md` | REST catalog setup and migration | Medium |
| `Testing.md` | pytest patterns for Spark jobs | Medium |
| `Medallion.md` | Bronze/Silver/Gold architecture | Medium |
| `Performance.md` | Tuning Spark for local dev | Low |

## Submitting Changes

### For Small Fixes

1. Fork the repository
2. Edit skill files directly
3. Submit a pull request

### For New Skills

1. Open an issue describing the skill scope
2. Get feedback on structure/approach
3. Submit PR with complete skill

### PR Checklist

- [ ] All code examples tested locally
- [ ] Follows project conventions
- [ ] Includes common errors section
- [ ] Cross-references related skills
- [ ] Version numbers are current

## Version Compatibility

Skills should target current stable versions:

| Technology | Version | Notes |
|------------|---------|-------|
| Spark | 4.0 / 4.1 | Test both |
| Iceberg | 1.10 | |
| Kafka | 3.6 | |
| Python | 3.10+ | |

When APIs differ between versions, document both:

```python
# Spark 4.0
df.write.format("iceberg").save("table")

# Spark 4.1+ (preferred)
df.writeTo("catalog.db.table").using("iceberg").create()
```

## License

By contributing, you agree that your contributions will be licensed under MIT.
