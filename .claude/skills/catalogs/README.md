# Catalogs

Skills for metadata catalogs that manage table definitions, schemas, and access control.

## Available Skills

*None yet - contributions welcome!*

## Planned Skills

| Skill | Catalog | Focus |
|-------|---------|-------|
| Unity-Catalog.md | Unity Catalog OSS | REST API setup, multi-engine access |
| Hive-Metastore.md | Hive Metastore | Legacy integration, migration paths |

## Conventions

```python
# Unity Catalog configuration
spark = (SparkSession.builder
    .config("spark.sql.catalog.unity", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.unity.type", "rest")
    .config("spark.sql.catalog.unity.uri", "http://localhost:8080/api/2.1/unity-catalog/iceberg")
    .config("spark.sql.catalog.unity.warehouse", "lakehouse")
    .getOrCreate())

# JDBC Catalog (PostgreSQL)
spark = (SparkSession.builder
    .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.iceberg.type", "jdbc")
    .config("spark.sql.catalog.iceberg.uri", "jdbc:postgresql://localhost:5432/iceberg")
    .getOrCreate())
```

## Catalog Comparison

| Feature | Unity Catalog | Hive Metastore |
|---------|---------------|----------------|
| Protocol | REST | Thrift |
| Multi-engine | Yes | Limited |
| Open source | Yes | Yes |
| Access control | Built-in | External |
