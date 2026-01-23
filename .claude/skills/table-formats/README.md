# Table Formats

Skills for open table formats enabling ACID transactions, time travel, and schema evolution.

## Available Skills

| Skill | Format | Focus |
|-------|--------|-------|
| [Iceberg.md](Iceberg.md) | Apache Iceberg | Tables, time travel, schema evolution, maintenance |

## Planned Skills

| Skill | Format | Focus |
|-------|--------|-------|
| Delta.md | Delta Lake | Unity Catalog integration, change data feed |
| Hudi.md | Apache Hudi | Incremental processing, record-level updates |

## Conventions

```python
# Iceberg table creation
spark.sql("""
    CREATE TABLE iceberg.bronze.events (
        event_id STRING,
        event_time TIMESTAMP,
        payload STRING
    )
    USING iceberg
    PARTITIONED BY (days(event_time))
""")

# Time travel
spark.read.option("as-of-timestamp", "2024-01-01 00:00:00").table("iceberg.bronze.events")
spark.read.option("snapshot-id", 123456789).table("iceberg.bronze.events")
```

## Key Concepts

- **Snapshots** - Immutable point-in-time views of table data
- **Manifests** - Metadata files tracking data files per partition
- **Schema Evolution** - Add/rename/drop columns without rewriting data
- **Partition Evolution** - Change partitioning without data migration
