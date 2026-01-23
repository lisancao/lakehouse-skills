"""Example: INCORRECT SDP pipeline - common mistakes.

This shows what an AI might produce without proper skill guidance.
"""

from pyspark.sql import SparkSession, functions as f

# WRONG: Creating SparkSession instead of using injected spark
spark = SparkSession.builder.getOrCreate()


def bronze_orders():
    """Load raw orders from parquet."""
    df = spark.read.parquet("/data/orders.parquet")
    # WRONG: Writing explicitly instead of returning
    df.write.mode("overwrite").saveAsTable("iceberg.bronze.orders")
    return df


def silver_orders_clean():
    """Filter out null order_ids."""
    # WRONG: Missing catalog in spark.table()
    df = spark.table("bronze.orders").filter(f.col("order_id").isNotNull())
    df.write.mode("overwrite").saveAsTable("iceberg.silver.orders_clean")
    return df


if __name__ == "__main__":
    bronze_orders()
    silver_orders_clean()
