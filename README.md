# lakehouse-skills

AI assistant skills for modern data engineering with [lakehouse-stack](https://github.com/lisancao/lakehouse-at-home).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Spark](https://img.shields.io/badge/Spark-4.0%20%7C%204.1-E25A1C?logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![Iceberg](https://img.shields.io/badge/Iceberg-1.10-blue)](https://iceberg.apache.org/)

## Overview

Skills are structured reference documents that enable AI assistants (Claude Code, Cursor, etc.) to generate accurate, production-ready data engineering code. Unlike generic documentation, skills provide:

- **Working examples** tested against current library versions
- **Common error patterns** with solutions
- **Project-specific conventions** for consistency
- **Cross-references** between related concepts

## Available Skills

| Skill | Focus |
|-------|-------|
| [SDP.md](.claude/skills/SDP.md) | Spark Declarative Pipelines - YAML-driven ETL with validation |

### Planned Skills

| Skill | Focus | Status |
|-------|-------|--------|
| Iceberg.md | Table operations, time travel, maintenance | Planned |
| Streaming.md | Kafka → Spark structured streaming | Planned |
| Unity-Catalog.md | REST catalog setup and multi-engine access | Planned |
| Medallion.md | Bronze/Silver/Gold architecture patterns | Planned |

## How Skills Activate

Skills load automatically based on request context when working with Claude Code in the lakehouse-stack repository.

| Request | Skills Loaded |
|---------|---------------|
| "Write a declarative pipeline" | SDP.md |
| "Stream Kafka data to Iceberg" | Streaming.md, Iceberg.md |
| "Set up Unity Catalog" | Unity-Catalog.md |

You can also reference skills explicitly:

```
Read the SDP skill and help me write a pipeline for customer data
```

## Structure

```
.claude/
└── skills/
    └── SDP.md              # Spark Declarative Pipelines
CLAUDE.md                   # Project reference for AI assistants
CONTRIBUTING.md             # Skill authoring guide
```

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Skill file structure and standards
- Data engineering conventions
- Code example requirements
- Submission process

### Quick Start

1. Fork and clone this repository
2. Create or modify skills in `.claude/skills/`
3. Test all code examples against lakehouse-stack
4. Submit a pull request

## Quality Assurance

All skills are:

- Tested against Spark 4.0/4.1 and Iceberg 1.10
- Verified with real error messages and solutions
- Reviewed for consistency with project conventions
- Cross-referenced with official documentation

## Related

- [lakehouse-stack](https://github.com/lisancao/lakehouse-at-home) - Main project repository
- [Spark Documentation](https://spark.apache.org/docs/latest/)
- [Iceberg Documentation](https://iceberg.apache.org/docs/latest/)

## License

MIT - See [LICENSE](LICENSE) for details.
