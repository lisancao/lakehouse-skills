# Apache Iceberg

> Open table format for huge analytic datasets with ACID transactions, time travel, and schema evolution.
>
> **Validated against Iceberg 1.10** | [Documentation](https://iceberg.apache.org/docs/1.10.0/)

## When to Use This Skill

- Creating and managing Iceberg tables
- Time travel queries and rollback
- Schema and partition evolution
- Table maintenance (compaction, snapshot expiry)
- Migrating from Hive/Parquet tables

## Quick Start

```python
from pyspark.sql import SparkSession

spark = (SparkSession.builder
    .appName("iceberg")
    .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.iceberg.type", "jdbc")
    .config("spark.sql.catalog.iceberg.uri", "jdbc:postgresql://localhost:5432/iceberg")
    .config("spark.sql.catalog.iceberg.warehouse", "s3a://lakehouse/warehouse")
    .getOrCreate())

# Create table
spark.sql("""
    CREATE TABLE iceberg.bronze.events (
        event_id STRING,
        event_type STRING,
        event_time TIMESTAMP,
        payload STRING
    )
    USING iceberg
    PARTITIONED BY (days(event_time))
""")

# Write data
df.writeTo("iceberg.bronze.events").append()

# Read data
spark.read.table("iceberg.bronze.events")
```

## Table Creation

### Basic Table
```sql
CREATE TABLE iceberg.bronze.orders (
    order_id STRING,
    customer_id STRING,
    amount DECIMAL(10,2),
    status STRING,
    created_at TIMESTAMP
)
USING iceberg;
```

### Partitioned Table
```sql
-- Partition by transformed column
CREATE TABLE iceberg.bronze.events (
    event_id STRING,
    event_time TIMESTAMP,
    event_type STRING
)
USING iceberg
PARTITIONED BY (days(event_time), event_type);

-- Partition transforms available:
-- years(ts), months(ts), days(ts), hours(ts)
-- bucket(N, col), truncate(N, col)
```

### With Table Properties
```sql
CREATE TABLE iceberg.silver.customers (
    customer_id STRING,
    name STRING,
    email STRING
)
USING iceberg
TBLPROPERTIES (
    'write.format.default' = 'parquet',
    'write.parquet.compression-codec' = 'zstd',
    'write.metadata.delete-after-commit.enabled' = 'true',
    'write.metadata.previous-versions-max' = '100'
);
```

## Writing Data

### Append
```python
# DataFrame API
df.writeTo("iceberg.bronze.events").append()

# SQL
spark.sql("INSERT INTO iceberg.bronze.events SELECT * FROM staging")
```

### Overwrite
```python
# Overwrite entire table
df.writeTo("iceberg.bronze.events").overwritePartitions()

# Overwrite with filter (dynamic overwrite)
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
df.writeTo("iceberg.bronze.events").overwritePartitions()
```

### Merge (Upsert)
```sql
MERGE INTO iceberg.silver.customers AS target
USING staging_customers AS source
ON target.customer_id = source.customer_id
WHEN MATCHED THEN
    UPDATE SET
        name = source.name,
        email = source.email,
        updated_at = current_timestamp()
WHEN NOT MATCHED THEN
    INSERT (customer_id, name, email, created_at, updated_at)
    VALUES (source.customer_id, source.name, source.email,
            current_timestamp(), current_timestamp());
```

### Delete
```sql
DELETE FROM iceberg.bronze.events
WHERE event_time < '2024-01-01';
```

### Update
```sql
UPDATE iceberg.silver.customers
SET status = 'inactive'
WHERE last_order_date < '2023-01-01';
```

## Time Travel

### Query by Timestamp
```sql
-- SQL
SELECT * FROM iceberg.bronze.events
TIMESTAMP AS OF '2024-01-15 10:00:00';

-- DataFrame
spark.read.option("as-of-timestamp", "1705312800000").table("iceberg.bronze.events")
```

### Query by Snapshot ID
```sql
-- SQL
SELECT * FROM iceberg.bronze.events
VERSION AS OF 5765873298573946583;

-- DataFrame
spark.read.option("snapshot-id", 5765873298573946583).table("iceberg.bronze.events")
```

### View Snapshots
```sql
SELECT * FROM iceberg.bronze.events.snapshots;

-- Output: snapshot_id, parent_id, operation, manifest_list, summary
```

### Rollback
```sql
-- Rollback to specific snapshot
CALL iceberg.system.rollback_to_snapshot('iceberg.bronze.events', 5765873298573946583);

-- Rollback to timestamp
CALL iceberg.system.rollback_to_timestamp('iceberg.bronze.events', TIMESTAMP '2024-01-15 10:00:00');
```

## Schema Evolution

### Add Column
```sql
ALTER TABLE iceberg.bronze.events
ADD COLUMN processed_at TIMESTAMP;

-- With position
ALTER TABLE iceberg.bronze.events
ADD COLUMN priority INT AFTER event_type;
```

### Rename Column
```sql
ALTER TABLE iceberg.bronze.events
RENAME COLUMN payload TO event_payload;
```

### Change Column Type
```sql
-- Widening only (int -> bigint, float -> double)
ALTER TABLE iceberg.bronze.events
ALTER COLUMN amount TYPE DECIMAL(12,2);
```

### Drop Column
```sql
ALTER TABLE iceberg.bronze.events
DROP COLUMN deprecated_field;
```

### Reorder Columns
```sql
ALTER TABLE iceberg.bronze.events
ALTER COLUMN status AFTER customer_id;
```

## Partition Evolution

```sql
-- Add new partition field (no data rewrite needed)
ALTER TABLE iceberg.bronze.events
ADD PARTITION FIELD bucket(16, customer_id);

-- Remove partition field
ALTER TABLE iceberg.bronze.events
DROP PARTITION FIELD days(event_time);

-- Replace partition scheme
ALTER TABLE iceberg.bronze.events
REPLACE PARTITION FIELD days(event_time) WITH hours(event_time);
```

## Table Maintenance

### Expire Snapshots
```sql
-- Remove snapshots older than timestamp
CALL iceberg.system.expire_snapshots(
    table => 'iceberg.bronze.events',
    older_than => TIMESTAMP '2024-01-01 00:00:00',
    retain_last => 10
);
```

### Remove Orphan Files
```sql
-- Clean up files not referenced by any snapshot
CALL iceberg.system.remove_orphan_files(
    table => 'iceberg.bronze.events',
    older_than => TIMESTAMP '2024-01-01 00:00:00'
);
```

### Rewrite Data Files (Compaction)
```sql
-- Compact small files
CALL iceberg.system.rewrite_data_files(
    table => 'iceberg.bronze.events',
    options => map('target-file-size-bytes', '134217728')  -- 128MB
);

-- With filter
CALL iceberg.system.rewrite_data_files(
    table => 'iceberg.bronze.events',
    where => 'event_date >= "2024-01-01"'
);
```

### Rewrite Manifests
```sql
-- Optimize manifest files
CALL iceberg.system.rewrite_manifests('iceberg.bronze.events');
```

## Metadata Queries

```sql
-- Snapshots
SELECT * FROM iceberg.bronze.events.snapshots;

-- History (shows table changes)
SELECT * FROM iceberg.bronze.events.history;

-- Data files
SELECT * FROM iceberg.bronze.events.files;

-- Manifests
SELECT * FROM iceberg.bronze.events.manifests;

-- Partitions
SELECT * FROM iceberg.bronze.events.partitions;

-- All metadata files
SELECT * FROM iceberg.bronze.events.all_data_files;
```

## Branching & Tagging

### Create Branch
```sql
-- Create branch from current state
ALTER TABLE iceberg.bronze.events
CREATE BRANCH audit_2024;

-- Create branch from snapshot
ALTER TABLE iceberg.bronze.events
CREATE BRANCH audit_2024
AS OF VERSION 5765873298573946583;
```

### Create Tag
```sql
-- Tag a snapshot (immutable reference)
ALTER TABLE iceberg.bronze.events
CREATE TAG release_v1
AS OF VERSION 5765873298573946583;
```

### Query Branch/Tag
```sql
SELECT * FROM iceberg.bronze.events VERSION AS OF 'audit_2024';
SELECT * FROM iceberg.bronze.events VERSION AS OF 'release_v1';
```

## Configuration

### Spark Session Config
```python
spark = (SparkSession.builder
    .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.iceberg.type", "jdbc")
    .config("spark.sql.catalog.iceberg.uri", "jdbc:postgresql://localhost:5432/iceberg")
    .config("spark.sql.catalog.iceberg.warehouse", "s3a://lakehouse/warehouse")
    .config("spark.sql.catalog.iceberg.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
    .getOrCreate())
```

### Table Properties
```sql
-- Write settings
ALTER TABLE iceberg.bronze.events SET TBLPROPERTIES (
    'write.format.default' = 'parquet',
    'write.parquet.compression-codec' = 'zstd',
    'write.target-file-size-bytes' = '134217728',  -- 128MB
    'write.distribution-mode' = 'hash'  -- or 'none', 'range'
);

-- Read settings
ALTER TABLE iceberg.bronze.events SET TBLPROPERTIES (
    'read.split.target-size' = '134217728'
);

-- Maintenance settings
ALTER TABLE iceberg.bronze.events SET TBLPROPERTIES (
    'history.expire.max-snapshot-age-ms' = '432000000',  -- 5 days
    'history.expire.min-snapshots-to-keep' = '10'
);
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `NoSuchTableException` | Table doesn't exist in catalog | Check `SHOW TABLES IN iceberg.bronze` |
| `ValidationException: Cannot find field` | Column doesn't exist | Schema mismatch, check `DESCRIBE TABLE` |
| `IllegalArgumentException: Cannot safely cast` | Incompatible schema evolution | Only widening casts allowed |
| `FileNotFoundException` | Orphan file deleted or missing | Run `remove_orphan_files`, check storage |
| `CommitFailedException` | Concurrent write conflict | Retry operation, check isolation level |

## Performance Tips

```sql
-- 1. Use hidden partitioning (no partition column in data)
PARTITIONED BY (days(event_time))  -- NOT PARTITIONED BY (event_date)

-- 2. Right-size files (default 128MB-512MB)
ALTER TABLE t SET TBLPROPERTIES ('write.target-file-size-bytes' = '268435456');

-- 3. Use sorted writes for better compression
ALTER TABLE t SET TBLPROPERTIES ('write.distribution-mode' = 'hash');

-- 4. Regular maintenance
CALL iceberg.system.expire_snapshots(...);
CALL iceberg.system.rewrite_data_files(...);

-- 5. Use incremental reads for streaming
spark.readStream.format("iceberg").load("iceberg.bronze.events")
```

## Medallion Architecture

```sql
-- Bronze: Raw ingestion
CREATE TABLE iceberg.bronze.raw_events (...) USING iceberg;

-- Silver: Cleaned & validated
CREATE TABLE iceberg.silver.events (...) USING iceberg
PARTITIONED BY (days(event_time));

-- Gold: Aggregated for serving
CREATE TABLE iceberg.gold.daily_metrics (...) USING iceberg
PARTITIONED BY (metric_date);
```

## See Also

- [../query-engines/spark/PySpark.md](../query-engines/spark/PySpark.md) - DataFrame operations
- [../query-engines/spark/Spark-SQL.md](../query-engines/spark/Spark-SQL.md) - SQL syntax
- [../catalogs/Unity-Catalog.md](../catalogs/Unity-Catalog.md) - REST catalog setup
