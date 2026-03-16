# Databricks notebook source
# DBTITLE 1,Create Catalog
# MAGIC %sql
# MAGIC CREATE CATALOG IF NOT EXISTS dbacad;

# COMMAND ----------

# DBTITLE 1,Create Schema
# MAGIC %sql
# MAGIC USE CATALOG dbacad;
# MAGIC CREATE SCHEMA IF NOT EXISTS
# MAGIC IDENTIFIER(split(current_user(), '@')[0]);
# MAGIC

# COMMAND ----------

# DBTITLE 1,Get current user
user = spark.sql("SELECT current_user()").collect()[0][0]
username = user.split("@")[0]
spark.sql(f'USE SCHEMA {username};')
print(username)

# COMMAND ----------

# DBTITLE 1,Verify current catalog and schema
# MAGIC %sql
# MAGIC SELECT current_catalog(), current_schema();

# COMMAND ----------

# DBTITLE 1,Reset
spark.sql(f'DROP TABLE IF EXISTS dbacad.{username}.main_users_target;')
spark.sql(f'DROP TABLE IF EXISTS dbacad.{username}.update_users_source;')
spark.sql(f'DROP TABLE IF EXISTS dbacad.{username}.new_users_source;')

# COMMAND ----------

# DBTITLE 1,Create target table
spark.sql(f"""
          CREATE OR REPLACE TABLE dbacad.{username}.main_users_target
          SELECT * 
          FROM VALUES
            (1, 'lucy', 'lucy@example.com', '2026-03-11', 'current'),
            (2, 'chris', 'chris@example.com', '2026-02-03', 'current'),
            (3, 'jhon', 'jhon@example.com', '2025-03-30', 'current'),
            (4, 'mel', 'mel@example.com', '2025-12-21', 'current')
          AS t(id, first_name, email, sign_up_date, status);
        """)    

# COMMAND ----------

# DBTITLE 1,View target table
spark.sql(f'SELECT * FROM dbacad.{username}.main_users_target ORDER BY id').display()

# COMMAND ----------

# DBTITLE 1,Create source table
# Cambiamos el correo el usuario con id=2
# Agregamos 2 nuevos usuarios
spark.sql(f"""
          CREATE OR REPLACE TABLE dbacad.{username}.update_users_source
          SELECT * 
          FROM VALUES
            (1, 'lucy', 'lucy@example.com', '2026-03-11', 'delete'),
            (2, 'chris', 'chris123@example.com', '2026-02-03', 'update'),
            (5, 'ayrton', 'ayrton@example.com', '2026-08-06', 'new'),
            (6, 'bass', 'bass@example.com', '2025-06-14', 'new')
          AS t(id, first_name, email, sign_up_date, status);
        """) 

# COMMAND ----------

# DBTITLE 1,View source table
spark.sql(f'SELECT * FROM dbacad.{username}.update_users_source ORDER BY id').display()

# COMMAND ----------

# DBTITLE 1,Merge the updates into the target table
# MAGIC %sql
# MAGIC MERGE INTO main_users_target target
# MAGIC USING update_users_source source
# MAGIC ON target.id = source.id
# MAGIC WHEN MATCHED AND source.status='update' THEN
# MAGIC UPDATE SET
# MAGIC   target.email = source.email,
# MAGIC   target.status = source.status
# MAGIC WHEN MATCHED AND source.status = 'delete' THEN
# MAGIC DELETE
# MAGIC WHEN NOT MATCHED THEN
# MAGIC INSERT (id, first_name, email, sign_up_date, status)
# MAGIC VALUES (source.id, source.first_name, source.email, source.sign_up_date, source.status)

# COMMAND ----------

# DBTITLE 1,View the updated table
spark.sql(f'SELECT * FROM dbacad.{username}.main_users_target ORDER BY id').display()

# COMMAND ----------

# DBTITLE 1,View the history of the updated table
# MAGIC %sql
# MAGIC DESCRIBE HISTORY main_users_target;

# COMMAND ----------

# DBTITLE 1,Use time travel to view the original table
# MAGIC %sql
# MAGIC SELECT * FROM main_users_target
# MAGIC VERSION AS OF 0;

# COMMAND ----------

# MAGIC %md 
# MAGIC **Schema Enforcement and Schema Evolution with MERGE INTO**

# COMMAND ----------

# DBTITLE 1,New data to merge into the main table
# Creamos la nueva tabla de origen con un campo adicional.
spark.sql(f"""
          CREATE OR REPLACE TABLE dbacad.{username}.new_users_source
          SELECT * 
          FROM VALUES
            (7, 'richard', 'richard@example.com', '2025-10-29', 'new', 'PY'),
            (8, 'alisson', 'alisson@example.com', '2025-08-06', 'new', 'CL'),
            (9, 'sebas', 'sebas@example.com', '2025-04-10', 'new', 'BR')
          AS t(id, first_name, email, sign_up_date, status, country);
        """) 

# COMMAND ----------

# DBTITLE 1,Try to merge a table with an additional column
# Esto dara un error
# simplemente lo vamos a capturar e imprimir 
# para que pueda continuarse con la ejecucion de la siguiente celda.
try:
    spark.sql("""MERGE INTO main_users_target target
                USING new_users_source source
                ON target.id = source.id
                WHEN MATCHED AND source.status='update' THEN
                UPDATE SET
                target.email = source.email,
                target.status = source.status
                WHEN MATCHED AND source.status = 'delete' THEN
                DELETE
                WHEN NOT MATCHED THEN
                INSERT (id, first_name, email, sign_up_date, status, country)
                VALUES (source.id, source.first_name, source.email, source.sign_up_date, source.status, source.country)""")
except Exception as e:
    print(e)
    pass

# COMMAND ----------

# DBTITLE 1,Use MERGE WITH SCHEMA EVOLUTION INTO statement
# MAGIC %sql
# MAGIC MERGE WITH SCHEMA EVOLUTION INTO main_users_target target
# MAGIC USING new_users_source source
# MAGIC ON target.id = source.id
# MAGIC WHEN MATCHED AND source.status='update' THEN
# MAGIC UPDATE SET
# MAGIC target.email = source.email,
# MAGIC target.status = source.status
# MAGIC WHEN MATCHED AND source.status = 'delete' THEN
# MAGIC DELETE
# MAGIC WHEN NOT MATCHED AND source.status = 'new' THEN
# MAGIC INSERT (id, first_name, email, sign_up_date, status, country)
# MAGIC VALUES (source.id, source.first_name, source.email, source.sign_up_date, source.status, source.country)

# COMMAND ----------

# DBTITLE 1,View the updated table with the new column country
spark.sql(f'select * from dbacad.{username}.main_users_target order by id').display()

# COMMAND ----------

# DBTITLE 1,View the history of the main table
# MAGIC %sql
# MAGIC -- Appearing new operation MERGE
# MAGIC DESCRIBE HISTORY main_users_target;