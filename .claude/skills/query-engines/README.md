# Query Engines

Skills for distributed query and compute engines.

## Available Skills

| Skill | Engine | Focus |
|-------|--------|-------|
| [SDP.md](SDP.md) | Spark | Declarative Pipelines - YAML-driven ETL |

## Planned Skills

| Skill | Engine | Focus |
|-------|--------|-------|
| Spark-SQL.md | Spark | SQL patterns, window functions, optimization |
| Spark-Streaming.md | Spark | Structured streaming, watermarks, triggers |
| DuckDB.md | DuckDB | Local analytics, Iceberg integration |
| Trino.md | Trino | Federated queries, catalog connectors |
| Flink-SQL.md | Flink | Stream processing, CDC patterns |

## Conventions

```python
# PySpark imports
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as f
from pyspark.sql import types as t

# SparkSession creation
spark = (SparkSession.builder
    .appName("job-name")
    .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
    .getOrCreate())
```
