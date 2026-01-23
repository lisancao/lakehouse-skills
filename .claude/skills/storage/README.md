# Storage

Skills for object storage and data lake storage layers.

## Available Skills

*None yet - contributions welcome!*

## Planned Skills

| Skill | Storage | Focus |
|-------|---------|-------|
| SeaweedFS.md | SeaweedFS | Local S3-compatible setup |
| MinIO.md | MinIO | Production object storage |
| S3.md | AWS S3 | IAM, encryption, lifecycle policies |
| ADLS.md | Azure Data Lake | Gen2 configuration, access patterns |
| GCS.md | Google Cloud Storage | Uniform bucket access, IAM |

## Conventions

```python
# S3/SeaweedFS configuration
spark = (SparkSession.builder
    .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:8333")
    .config("spark.hadoop.fs.s3a.access.key", "${AWS_ACCESS_KEY_ID}")
    .config("spark.hadoop.fs.s3a.secret.key", "${AWS_SECRET_ACCESS_KEY}")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .getOrCreate())
```

## Key Concepts

- **Object Storage** - Flat namespace, HTTP access, eventual consistency
- **Path Style vs Virtual Host** - URL formats for bucket access
- **Multipart Upload** - Large file handling
- **Lifecycle Policies** - Automatic tiering and expiration

## Storage Layout

```
s3://lakehouse/
├── warehouse/
│   ├── bronze/          # Raw ingestion
│   ├── silver/          # Cleaned data
│   └── gold/            # Aggregated data
├── checkpoints/         # Streaming state
└── tmp/                 # Temporary files
```
