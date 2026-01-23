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

## Skills by Category

### Query Engines
Distributed compute and SQL engines.

**[Spark](.claude/skills/query-engines/spark/)**

| Skill | Focus |
|-------|-------|
| [SDP.md](.claude/skills/query-engines/spark/SDP.md) | Declarative Pipelines - YAML-driven ETL |
| [PySpark.md](.claude/skills/query-engines/spark/PySpark.md) | DataFrame API, transformations, actions |
| [Structured-Streaming.md](.claude/skills/query-engines/spark/Structured-Streaming.md) | Real-time processing, watermarks |
| [Spark-SQL.md](.claude/skills/query-engines/spark/Spark-SQL.md) | SQL patterns, window functions, CTEs |

### Table Formats
Open table formats for ACID transactions and time travel.

| Skill | Focus |
|-------|-------|
| *Iceberg.md* | Table operations, snapshots, maintenance (planned) |

### Catalogs
Metadata management and multi-engine access.

| Skill | Focus |
|-------|-------|
| *Unity-Catalog.md* | REST API setup, multi-engine access (planned) |

### Orchestrators
Workflow scheduling and pipeline management.

| Skill | Focus |
|-------|-------|
| *Airflow.md* | DAGs, operators, Spark integration (planned) |

### Streaming
Real-time ingestion and stream processing.

| Skill | Focus |
|-------|-------|
| *Kafka.md* | Topics, producers, consumers (planned) |

### Storage
Object storage and data lake layers.

| Skill | Focus |
|-------|-------|
| *SeaweedFS.md* | Local S3-compatible setup (planned) |

## Structure

```
.claude/skills/
├── query-engines/
│   ├── README.md
│   └── spark/
│       ├── README.md
│       ├── SDP.md
│       ├── PySpark.md
│       ├── Structured-Streaming.md
│       └── Spark-SQL.md
├── table-formats/
│   └── README.md
├── catalogs/
│   └── README.md
├── orchestrators/
│   └── README.md
├── streaming/
│   └── README.md
└── storage/
    └── README.md
```

## How Skills Activate

Skills load automatically based on request context when working with Claude Code.

| Request | Skills Loaded |
|---------|---------------|
| "Write a declarative pipeline" | query-engines/spark/SDP.md |
| "PySpark DataFrame transformations" | query-engines/spark/PySpark.md |
| "Stream Kafka data to Iceberg" | query-engines/spark/Structured-Streaming.md |
| "Set up Unity Catalog" | catalogs/Unity-Catalog.md |

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Skill file structure and standards
- Data engineering conventions
- Code example requirements

### Quick Start

1. Fork and clone this repository
2. Create or modify skills in `.claude/skills/<category>/`
3. Test all code examples against lakehouse-stack
4. Submit a pull request

## Related

- [lakehouse-stack](https://github.com/lisancao/lakehouse-at-home) - Main project repository
- [Spark Documentation](https://spark.apache.org/docs/latest/)
- [Iceberg Documentation](https://iceberg.apache.org/docs/latest/)

## License

MIT - See [LICENSE](LICENSE) for details.
