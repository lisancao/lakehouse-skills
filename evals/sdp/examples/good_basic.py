"""Example: Correct SDP pipeline for basic_medallion test case."""

from typing import Any

from pyspark import pipelines as dp
from pyspark.sql import functions as f

spark: Any


@dp.materialized_view(name="bronze.orders")
def bronze_orders():
    """Load raw orders from parquet."""
    return spark.read.parquet("/data/orders.parquet")


@dp.materialized_view(name="silver.orders_clean")
def silver_orders_clean():
    """Filter out null order_ids."""
    return spark.table("iceberg.bronze.orders").filter(f.col("order_id").isNotNull())
