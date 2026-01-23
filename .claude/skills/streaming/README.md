# Streaming

Skills for real-time data ingestion and stream processing.

## Available Skills

| Skill | Technology | Focus |
|-------|------------|-------|
| [Kafka.md](Kafka.md) | Apache Kafka | Topics, producers, consumers, Spark integration |

## Planned Skills

| Skill | Technology | Focus |
|-------|------------|-------|
| Kafka-Connect.md | Kafka Connect | Connectors, transforms, sink/source |
| Flink.md | Apache Flink | Stateful stream processing |

## Conventions

```python
# Spark Structured Streaming from Kafka
df_stream = (spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("subscribe", "events")
    .option("startingOffsets", "earliest")
    .load())

# Parse and write to Iceberg
(df_stream
    .selectExpr("CAST(value AS STRING) as json")
    .select(f.from_json("json", schema).alias("data"))
    .select("data.*")
    .writeStream
    .format("iceberg")
    .outputMode("append")
    .option("checkpointLocation", "/checkpoints/events")
    .toTable("iceberg.bronze.events"))
```

## Key Concepts

- **Watermarks** - Handle late-arriving data
- **Triggers** - Control micro-batch frequency
- **Checkpoints** - Enable exactly-once processing
- **Backpressure** - Manage consumer lag
