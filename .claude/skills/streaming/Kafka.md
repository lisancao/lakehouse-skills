# Apache Kafka

> Distributed event streaming platform for high-throughput, fault-tolerant messaging.
>
> **Validated against Kafka 3.6** | [Documentation](https://kafka.apache.org/36/documentation/)

## When to Use This Skill

- Setting up Kafka topics and configurations
- Producing and consuming messages
- Integrating Kafka with Spark Structured Streaming
- Schema management and serialization
- Monitoring and troubleshooting Kafka

## Quick Start

```bash
# Create topic
docker exec kafka kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --create \
    --topic events \
    --partitions 6 \
    --replication-factor 1

# Produce test message
echo '{"event_id": "1", "type": "click"}' | docker exec -i kafka \
    kafka-console-producer.sh \
    --bootstrap-server localhost:9092 \
    --topic events

# Consume messages
docker exec kafka kafka-console-consumer.sh \
    --bootstrap-server localhost:9092 \
    --topic events \
    --from-beginning
```

## Topic Management

### Create Topic
```bash
kafka-topics.sh --bootstrap-server localhost:9092 \
    --create \
    --topic orders \
    --partitions 12 \
    --replication-factor 3 \
    --config retention.ms=604800000 \
    --config cleanup.policy=delete
```

### List Topics
```bash
kafka-topics.sh --bootstrap-server localhost:9092 --list
```

### Describe Topic
```bash
kafka-topics.sh --bootstrap-server localhost:9092 \
    --describe \
    --topic orders
```

### Modify Topic
```bash
# Add partitions (cannot decrease)
kafka-topics.sh --bootstrap-server localhost:9092 \
    --alter \
    --topic orders \
    --partitions 24

# Change config
kafka-configs.sh --bootstrap-server localhost:9092 \
    --alter \
    --entity-type topics \
    --entity-name orders \
    --add-config retention.ms=259200000
```

### Delete Topic
```bash
kafka-topics.sh --bootstrap-server localhost:9092 \
    --delete \
    --topic orders
```

## Topic Configuration

| Config | Default | Description |
|--------|---------|-------------|
| `retention.ms` | 604800000 (7d) | How long to keep messages |
| `retention.bytes` | -1 (unlimited) | Max size before deletion |
| `cleanup.policy` | delete | `delete` or `compact` |
| `max.message.bytes` | 1048576 (1MB) | Max message size |
| `min.insync.replicas` | 1 | Min replicas for acks=all |

### Compacted Topics (for CDC/state)
```bash
kafka-topics.sh --bootstrap-server localhost:9092 \
    --create \
    --topic customer-state \
    --partitions 6 \
    --config cleanup.policy=compact \
    --config min.cleanable.dirty.ratio=0.1
```

## Python Producer

```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    key_serializer=lambda k: k.encode('utf-8') if k else None,
    acks='all',  # Wait for all replicas
    retries=3,
    linger_ms=10,  # Batch for 10ms
    batch_size=16384
)

# Send message
producer.send(
    'orders',
    key='customer-123',
    value={'order_id': 'ord-456', 'amount': 99.99}
)

# Flush and close
producer.flush()
producer.close()
```

### Async with Callbacks
```python
def on_success(metadata):
    print(f"Sent to {metadata.topic}:{metadata.partition}@{metadata.offset}")

def on_error(e):
    print(f"Error: {e}")

future = producer.send('orders', value={'order_id': '123'})
future.add_callback(on_success)
future.add_errback(on_error)
```

## Python Consumer

```python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'orders',
    bootstrap_servers=['localhost:9092'],
    group_id='order-processor',
    auto_offset_reset='earliest',  # or 'latest'
    enable_auto_commit=True,
    auto_commit_interval_ms=5000,
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    print(f"Topic: {message.topic}")
    print(f"Partition: {message.partition}")
    print(f"Offset: {message.offset}")
    print(f"Key: {message.key}")
    print(f"Value: {message.value}")
```

### Manual Commit
```python
consumer = KafkaConsumer(
    'orders',
    bootstrap_servers=['localhost:9092'],
    group_id='order-processor',
    enable_auto_commit=False
)

for message in consumer:
    process(message)
    consumer.commit()  # Commit after processing
```

### Assign Specific Partitions
```python
from kafka import TopicPartition

consumer = KafkaConsumer(bootstrap_servers=['localhost:9092'])
partition = TopicPartition('orders', 0)
consumer.assign([partition])
consumer.seek(partition, 0)  # Start from offset 0
```

## Spark Streaming Integration

### Read from Kafka
```python
df = (spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("subscribe", "orders")  # or "subscribePattern" for regex
    .option("startingOffsets", "earliest")  # or "latest", or JSON
    .option("maxOffsetsPerTrigger", 10000)  # Rate limit
    .option("kafka.group.id", "spark-consumer")
    .load())

# Kafka DataFrame columns:
# key (binary), value (binary), topic, partition, offset, timestamp, timestampType
```

### Parse Messages
```python
from pyspark.sql import functions as f
from pyspark.sql.types import StructType, StringType, DoubleType

schema = StructType() \
    .add("order_id", StringType()) \
    .add("customer_id", StringType()) \
    .add("amount", DoubleType())

df_parsed = (df
    .selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")
    .select(
        f.col("key"),
        f.from_json(f.col("value"), schema).alias("data")
    )
    .select("key", "data.*"))
```

### Write to Kafka
```python
(df
    .selectExpr(
        "CAST(order_id AS STRING) AS key",
        "to_json(struct(*)) AS value"
    )
    .writeStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("topic", "processed-orders")
    .option("checkpointLocation", "/checkpoints/kafka-sink")
    .start())
```

### Starting Offsets
```python
# From beginning
.option("startingOffsets", "earliest")

# From end (new messages only)
.option("startingOffsets", "latest")

# From specific offsets (JSON)
.option("startingOffsets", '{"orders":{"0":100,"1":200}}')

# From timestamp
.option("startingOffsetsByTimestamp", '{"orders":{"0":1609459200000}}')
```

## Consumer Groups

### List Groups
```bash
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list
```

### Describe Group
```bash
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
    --describe \
    --group order-processor
```

### Reset Offsets
```bash
# To earliest
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
    --group order-processor \
    --topic orders \
    --reset-offsets \
    --to-earliest \
    --execute

# To specific offset
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
    --group order-processor \
    --topic orders:0 \
    --reset-offsets \
    --to-offset 1000 \
    --execute

# To timestamp
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
    --group order-processor \
    --topic orders \
    --reset-offsets \
    --to-datetime 2024-01-15T00:00:00.000 \
    --execute
```

### Delete Group
```bash
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
    --delete \
    --group order-processor
```

## Monitoring

### Check Lag
```bash
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
    --describe \
    --group order-processor

# Output: TOPIC, PARTITION, CURRENT-OFFSET, LOG-END-OFFSET, LAG
```

### Get Topic Offsets
```bash
# Earliest offsets
kafka-run-class.sh kafka.tools.GetOffsetShell \
    --broker-list localhost:9092 \
    --topic orders \
    --time -2

# Latest offsets
kafka-run-class.sh kafka.tools.GetOffsetShell \
    --broker-list localhost:9092 \
    --topic orders \
    --time -1
```

### Describe Cluster
```bash
kafka-broker-api-versions.sh --bootstrap-server localhost:9092
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `LEADER_NOT_AVAILABLE` | New topic, leader not elected | Wait and retry, check broker health |
| `NOT_ENOUGH_REPLICAS` | Brokers down | Check `min.insync.replicas`, broker status |
| `OFFSET_OUT_OF_RANGE` | Offset deleted (retention) | Reset to `earliest` or `latest` |
| `GROUP_COORDINATOR_NOT_AVAILABLE` | Coordinator starting | Wait and retry |
| `REBALANCE_IN_PROGRESS` | Consumer group rebalancing | Wait for rebalance to complete |
| `MESSAGE_TOO_LARGE` | Message exceeds `max.message.bytes` | Increase limit or chunk messages |

## Performance Tuning

### Producer
```python
KafkaProducer(
    # Batching
    linger_ms=20,           # Wait up to 20ms to batch
    batch_size=32768,       # 32KB batch size

    # Compression
    compression_type='lz4', # or 'gzip', 'snappy', 'zstd'

    # Reliability vs throughput
    acks='all',             # 'all' for durability, '1' for speed
    retries=5,

    # Memory
    buffer_memory=67108864  # 64MB buffer
)
```

### Consumer
```python
KafkaConsumer(
    # Batching
    fetch_min_bytes=1024,       # Min data per fetch
    fetch_max_wait_ms=500,      # Max wait for min bytes
    max_partition_fetch_bytes=1048576,  # 1MB per partition

    # Parallelism
    max_poll_records=500,       # Max records per poll

    # Session management
    session_timeout_ms=45000,
    heartbeat_interval_ms=15000
)
```

## Docker Compose (lakehouse-stack)

```yaml
# From docker-compose-kafka.yml
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

## See Also

- [../query-engines/spark/Structured-Streaming.md](../query-engines/spark/Structured-Streaming.md) - Spark streaming patterns
- [../table-formats/Iceberg.md](../table-formats/Iceberg.md) - Streaming to Iceberg tables
