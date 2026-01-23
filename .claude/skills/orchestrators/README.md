# Orchestrators

Skills for workflow orchestration and pipeline scheduling.

## Available Skills

*None yet - contributions welcome!*

## Planned Skills

| Skill | Orchestrator | Focus |
|-------|--------------|-------|
| Airflow.md | Apache Airflow | DAGs, operators, Spark integration |
| Dagster.md | Dagster | Software-defined assets, partitions |
| Prefect.md | Prefect | Flow deployment, async execution |
| Mage.md | Mage | Data pipeline IDE, blocks |

## Conventions

```python
# Airflow DAG pattern
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime

with DAG(
    "lakehouse_etl",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
) as dag:

    bronze_load = SparkSubmitOperator(
        task_id="bronze_load",
        application="/scripts/bronze_load.py",
        conn_id="spark_default",
    )
```

## Key Concepts

- **DAG** - Directed Acyclic Graph defining task dependencies
- **Idempotency** - Tasks produce same result on re-run
- **Backfill** - Processing historical data for missed runs
- **Sensors** - Wait for external conditions before proceeding
