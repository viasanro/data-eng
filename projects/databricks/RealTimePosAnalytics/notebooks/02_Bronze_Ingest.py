# Databricks notebook source
# Bronze layer data validation and processing for Serverless environments.
#
# This notebook assumes you have already run `01_Generate_Inputs_On_DBFS.py` which
# creates managed Delta tables directly. This notebook validates and processes
# the existing bronze tables without using DBFS paths (Serverless-compatible).

from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %run ./rtpa_lib

# COMMAND ----------

# Configuration for Serverless-compatible processing
dbutils.widgets.text("db_name_bronze", "rtpa_bronze", "Bronze schema/database")
dbutils.widgets.dropdown("validate_data", "true", ["true", "false"], "Validate bronze data quality")
dbutils.widgets.dropdown("reprocess_data", "false", ["true", "false"], "Reprocess/clean existing data")

db_bronze = dbutils.widgets.get("db_name_bronze").strip()
validate_data = dbutils.widgets.get("validate_data").strip().lower() == "true"
reprocess_data = dbutils.widgets.get("reprocess_data").strip().lower() == "true"

bronze_events_table = f"{db_bronze}.pos_events_stream"
bronze_snapshots_table = f"{db_bronze}.floor_snapshots_batch"

print(f"Working with bronze tables:")
print(f"  Events: {bronze_events_table}")
print(f"  Snapshots: {bronze_snapshots_table}")
print(f"  Validate: {validate_data}")
print(f"  Reprocess: {reprocess_data}")

# COMMAND ----------

# Check if bronze tables exist from notebook 01
try:
    events_count = spark.sql(f"SELECT COUNT(*) as cnt FROM {bronze_events_table}").collect()[0]["cnt"]
    snapshots_count = spark.sql(f"SELECT COUNT(*) as cnt FROM {bronze_snapshots_table}").collect()[0]["cnt"]
    print(f"✓ Bronze tables found:")
    print(f"  Events: {events_count:,} rows")
    print(f"  Snapshots: {snapshots_count:,} rows")
except Exception as e:
    print(f"❌ Bronze tables not found. Please run notebook 01 first: {e}")
    # Stop execution if tables don't exist
    dbutils.notebook.exit("Please run 01_Generate_Inputs_On_DBFS.py first")

# COMMAND ----------

# Data validation and quality checks
if validate_data:
    print("Validating bronze data quality...")
    
    # Check events table
    events_validation = spark.sql(f"""
        SELECT 
            'events' as table_name,
            COUNT(*) as total_rows,
            COUNT(DISTINCT event_id) as unique_events,
            COUNT(DISTINCT store_id) as unique_stores,
            COUNT(DISTINCT sku) as unique_skus,
            MIN(event_date) as min_date,
            MAX(event_date) as max_date,
            COUNT(*) - COUNT(DISTINCT event_id) as duplicate_events
        FROM {bronze_events_table}
    """)
    
    # Check snapshots table  
    snapshots_validation = spark.sql(f"""
        SELECT 
            'snapshots' as table_name,
            COUNT(*) as total_rows,
            COUNT(DISTINCT store_id) as unique_stores,
            COUNT(DISTINCT sku) as unique_skus,
            MIN(snapshot_date) as min_date,
            MAX(snapshot_date) as max_date,
            COUNT(*) - COUNT(DISTINCT CONCAT(store_id, sku, snapshot_date)) as duplicate_snapshots
        FROM {bronze_snapshots_table}
    """)
    
    print("Events validation:")
    events_validation.show()
    
    print("Snapshots validation:")
    snapshots_validation.show()
    
    # Check for data quality issues
    duplicate_events = events_validation.collect()[0]["duplicate_events"]
    duplicate_snapshots = snapshots_validation.collect()[0]["duplicate_snapshots"]
    
    if duplicate_events > 0 or duplicate_snapshots > 0:
        print(f"⚠️ Found data quality issues:")
        if duplicate_events > 0:
            print(f"  - {duplicate_events} duplicate events")
        if duplicate_snapshots > 0:
            print(f"  - {duplicate_snapshots} duplicate snapshots")
    else:
        print("✓ No data quality issues found")

# COMMAND ----------

# Data reprocessing/cleaning (optional)
if reprocess_data:
    print("Reprocessing bronze data...")
    
    # Remove duplicate events if any
    spark.sql(f"""
        CREATE OR REPLACE TEMP VIEW deduped_events AS
        SELECT * FROM (
            SELECT 
                *,
                ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY _ingest_time DESC) as rn
            FROM {bronze_events_table}
        ) WHERE rn = 1
    """)
    
    spark.sql(f"""
        INSERT OVERWRITE {bronze_events_table}
        SELECT * FROM deduped_events
    """)
    
    # Remove duplicate snapshots if any
    spark.sql(f"""
        CREATE OR REPLACE TEMP VIEW deduped_snapshots AS
        SELECT * FROM (
            SELECT 
                *,
                ROW_NUMBER() OVER (PARTITION BY store_id, sku, snapshot_date ORDER BY _ingest_time DESC) as rn
            FROM {bronze_snapshots_table}
        ) WHERE rn = 1
    """)
    
    spark.sql(f"""
        INSERT OVERWRITE {bronze_snapshots_table}
        SELECT * FROM deduped_snapshots
    """)
    
    print("✓ Data reprocessing completed")

# COMMAND ----------

# Display sample data from bronze tables
print("Sample events data:")
display(spark.table(bronze_events_table).limit(10))

print("Sample snapshots data:")
display(spark.table(bronze_snapshots_table).limit(10))

# COMMAND ----------

# Summary statistics
print("Bronze layer summary:")
spark.sql(f"""
    SELECT 'events' as table_type, COUNT(*) as row_count, 
           COUNT(DISTINCT store_id) as stores, 
           COUNT(DISTINCT sku) as skus,
           MIN(event_date) as min_date,
           MAX(event_date) as max_date
    FROM {bronze_events_table}
    UNION ALL
    SELECT 'snapshots' as table_type, COUNT(*) as row_count,
           COUNT(DISTINCT store_id) as stores,
           COUNT(DISTINCT sku) as skus, 
           MIN(snapshot_date) as min_date,
           MAX(snapshot_date) as max_date
    FROM {bronze_snapshots_table}
""").show()

print("✓ Bronze layer processing completed successfully!")
print("You can now proceed to notebook 03_Silver_Transform.py")

