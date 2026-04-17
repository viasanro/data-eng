# Databricks notebook source
import pyspark.pandas as ps

# COMMAND ----------

current_catalog = spark.sql("SELECT current_catalog()").collect()[0][0]
current_schema = spark.sql("SELECT current_schema()").collect()[0][0]

# COMMAND ----------

spark.sql(f"USE CATALOG {current_catalog}");
spark.sql(f"USE SCHEMA {current_schema}");

# COMMAND ----------

# DBTITLE 1,Reset
# MAGIC %sql
# MAGIC -- Solo con fines didácticos para la ejecucion de la notebook.
# MAGIC DROP TABLE IF EXISTS brz_sellout_online_retail;
# MAGIC DROP TABLE IF EXISTS slv_sellout_online_retail;
# MAGIC DROP TABLE IF EXISTS gld_sellout_online_retail;
# MAGIC DROP TABLE IF EXISTS gld_rfm_online_retail;

# COMMAND ----------

# DBTITLE 1,Listing Volume files
# MAGIC %sql
# MAGIC LIST '/Volumes/workspace/opt/mnt/'

# COMMAND ----------

# DBTITLE 1,Creating Source table
# MAGIC %sql
# MAGIC DROP TABLE IF EXISTS src_sellout_online_retail;
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS src_sellout_online_retail AS
# MAGIC SELECT *,
# MAGIC _metadata.file_modification_time AS ModificationTime,
# MAGIC _metadata.file_name AS SourceFile
# MAGIC --current_timestamp() AS IngestionTimestamp
# MAGIC FROM read_files("/Volumes/workspace/opt/mnt/online_retail.csv",
# MAGIC                 format => "csv");
# MAGIC
# MAGIC SELECT * FROM src_sellout_online_retail limit 5;

# COMMAND ----------

# MAGIC %sql
# MAGIC select count(1) from src_sellout_online_retail where customerID is null

# COMMAND ----------

# DBTITLE 1,Creating Bronze layer table
spark.sql("""
            SELECT 
            sha2(concat_ws('||', 
                COALESCE(InvoiceNo,''), 
                COALESCE(StockCode,''),
                COALESCE(Quantity,0),
                COALESCE(InvoiceDate,''),
                COALESCE(CustomerID,0)), 256) AS pk,
            *,
            current_timestamp() AS IngestionTimestamp
            FROM src_sellout_online_retail
        """).write.mode("append").saveAsTable("brz_sellout_online_retail")

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from brz_sellout_online_retail limit 5;

# COMMAND ----------

# DBTITLE 1,Creating Silver layer table
# MAGIC %sql
# MAGIC     
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS slv_sellout_online_retail AS
# MAGIC WITH deduped_data AS (
# MAGIC   SELECT 
# MAGIC     *,
# MAGIC     cast(InvoiceDate AS DATE) AS InvoiceDt,
# MAGIC     row_number() OVER (PARTITION BY pk
# MAGIC                                   ORDER BY InvoiceNo) AS rn
# MAGIC   FROM brz_sellout_online_retail
# MAGIC   WHERE CustomerID IS NOT NULL
# MAGIC   QUALIFY rn = 1
# MAGIC )
# MAGIC SELECT * EXCEPT(InvoiceDate, rn)
# MAGIC FROM deduped_data;
# MAGIC
# MAGIC -- Validamos la inexistencia de duplicados
# MAGIC SELECT pk,
# MAGIC row_number() OVER (PARTITION BY pk ORDER BY pk) AS rn
# MAGIC FROM slv_sellout_online_retail 
# MAGIC QUALIFY rn > 1;

# COMMAND ----------

# DBTITLE 1,Ingesta en Silver
# MAGIC %sql
# MAGIC WITH brz_dedup AS (
# MAGIC   SELECT *,
# MAGIC          ROW_NUMBER() OVER (PARTITION BY pk ORDER BY InvoiceDate DESC) as rn
# MAGIC   FROM brz_sellout_online_retail
# MAGIC   WHERE CustomerID IS NOT NULL
# MAGIC )
# MAGIC
# MAGIC MERGE INTO slv_sellout_online_retail t
# MAGIC USING (
# MAGIC   SELECT * EXCEPT(InvoiceDate), 
# MAGIC   CAST(InvoiceDate AS DATE) AS InvoiceDt
# MAGIC   FROM brz_dedup WHERE rn = 1
# MAGIC ) s
# MAGIC ON t.pk = s.pk
# MAGIC
# MAGIC WHEN MATCHED THEN UPDATE SET *
# MAGIC WHEN NOT MATCHED THEN INSERT *
# MAGIC ;

# COMMAND ----------

# MAGIC %md
# MAGIC #### EDA

# COMMAND ----------

# DBTITLE 1,Valores unicos
# MAGIC %sql
# MAGIC SELECT COUNT(DISTINCT InvoiceNo) TotalTickets,
# MAGIC COUNT(DISTINCT StockCode) TotalPRoductos,
# MAGIC count(DISTINCT CustomerID) TotalClientes,
# MAGIC MIN(InvoiceDt) AS FechaMinima,
# MAGIC MAX(InvoiceDt) AS FechaMaxima
# MAGIC  FROM slv_sellout_online_retail limit 5

# COMMAND ----------

# DBTITLE 1,Tickets por mes
# MAGIC %sql
# MAGIC SELECT substring(InvoiceDt,1,7) AS mes, 
# MAGIC count(1) AS registros, 
# MAGIC count(DISTINCT InvoiceNo) AS tickets
# MAGIC FROM slv_sellout_online_retail
# MAGIC GROUP BY substring(InvoiceDt,1,7)
# MAGIC ORDER BY 1

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC #### A continuación creamos nuestra tabla en la gold según los siguientes criterios:<br> 
# MAGIC 1) Tomamos como fecha de creación del reporte el 2011-12-10 debido a que contamos con datos hasta el 2011-12-09.<br> 
# MAGIC 2) **Recency** se define como la cantidad de días transcurridos desde la última compra.<br>
# MAGIC 3) **frequency** se define como la cantidad de compras realizadas por un determinado cliente. 
# MAGIC 4) **Monetary** es lo que consideramos de valor total para el ejercicio, en este caso la suma total de lo gastado por el cliente. 
# MAGIC 5) **Ticket Promedio**, representa el gasto promedio del cliente por ticket.
# MAGIC 6) **Unidades por Ticket**, representa cuantos productos compra el cliente en promedio por cada ticket.

# COMMAND ----------

# DBTITLE 1,Creating gold layer table
# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS gld_sellout_online_retail AS
# MAGIC SELECT CustomerID as customerId,
# MAGIC MIN(InvoiceDt) AS primeraCompra,
# MAGIC MAX(InvoiceDt) AS ultimaCompra,
# MAGIC DATEDIFF(to_date('2011-12-10', 'yyyy-MM-dd'), MAX(InvoiceDt)) AS recency,
# MAGIC COUNT(DISTINCT InvoiceNo) AS frequency,
# MAGIC ROUND(SUM(Quantity * UnitPrice),2) AS monetary,
# MAGIC ROUND(SUM(Quantity * UnitPrice)/COUNT(DISTINCT InvoiceNo),2) AS ticketPromedio,
# MAGIC ROUND(SUM(Quantity)/COUNT(DISTINCT InvoiceNo),1) AS unidadesPorTicket,
# MAGIC current_date() AS ingestionDate
# MAGIC FROM slv_sellout_online_retail
# MAGIC GROUP BY CustomerID
# MAGIC ;
# MAGIC
# MAGIC SELECT * FROM gld_sellout_online_retail limit 5;

# COMMAND ----------

# DBTITLE 1,Ingesta en gold
# MAGIC %sql
# MAGIC WITH slv_dedup AS (
# MAGIC     SELECT CustomerID as customerId,
# MAGIC     MIN(InvoiceDt) AS primeraCompra,
# MAGIC     MAX(InvoiceDt) AS ultimaCompra,
# MAGIC     DATEDIFF(to_date('2011-12-10', 'yyyy-MM-dd'), MAX(InvoiceDt)) AS recency,
# MAGIC     COUNT(DISTINCT InvoiceNo) AS frequency,
# MAGIC     ROUND(SUM(Quantity * UnitPrice),2) AS monetary,
# MAGIC     ROUND(SUM(Quantity * UnitPrice)/COUNT(DISTINCT InvoiceNo),2) AS ticketPromedio,
# MAGIC     ROUND(SUM(Quantity)/COUNT(DISTINCT InvoiceNo),1) AS unidadesPorTicket,
# MAGIC     current_date() AS ingestionDate
# MAGIC     FROM slv_sellout_online_retail
# MAGIC     GROUP BY CustomerID
# MAGIC )
# MAGIC MERGE INTO gld_sellout_online_retail t
# MAGIC USING slv_dedup s
# MAGIC ON t.customerId = s.customerId
# MAGIC WHEN MATCHED THEN UPDATE SET *
# MAGIC WHEN NOT MATCHED THEN INSERT *
# MAGIC ;
# MAGIC

# COMMAND ----------

# DBTITLE 1,Cantidad clientes por frecuencia
spark.sql("""SELECT frequency, count(DISTINCT CustomerId) AS clientes 
          FROM gld_sellout_online_retail
          GROUP BY frequency
          ORDER BY 2 DESC""").display()

# COMMAND ----------

# DBTITLE 1,Cantidad clientes por recencia
spark.sql("""SELECT recency, count(DISTINCT CustomerId) AS clientes 
          FROM gld_sellout_online_retail
          GROUP BY recency
          ORDER BY 2 DESC""").display()

# COMMAND ----------

# MAGIC %md
# MAGIC Creamos un nuevo Koalas Dataframe a partir de nuestro Spark Dataframe estableciendo el customer_id como indice. Esto nos permitirá luego poder segmentar los clientes en base a los tres valores (RFM)

# COMMAND ----------

rfmDF = spark.sql("select * from gld_sellout_online_retail")

rfmTable = ps.DataFrame(
    rfmDF[['customerId', 'recency', 'frequency', 'monetary']]
).set_index('customerId').dropna()

# COMMAND ----------

rfmTable.head()

# COMMAND ----------

# MAGIC %md
# MAGIC <b>TRATAMIENTO DE OUTLIERS</b>.
# MAGIC Nuestros límites inferior y superior se definen como <b>Q1-1.5\*IQR</b> y <b>Q3+1.5\*IQR</b> respectivamente, esto por convención.

# COMMAND ----------

rq3= rfmTable.recency.quantile(q=0.75)
rq1= rfmTable.recency.quantile(q=0.25)
riqr = rq3 - rq1
rlwr_bound = max(0, rq1 - (1.5*riqr))
rupr_bound = rq3 + (1.5*riqr)
print(rlwr_bound, rupr_bound)

def r_outliers(valor):
    return True if(valor < rlwr_bound or valor > rupr_bound) else False


fq3= rfmTable.frequency.quantile(q=0.75)
fq1= rfmTable.frequency.quantile(q=0.25)
fiqr = fq3 - fq1
flwr_bound = max(0, fq1 - (1.5*fiqr))
fupr_bound = fq3 + (1.5*fiqr)
print(flwr_bound, fupr_bound)

def f_outliers(valor):
    return True if(valor < flwr_bound or valor > fupr_bound) else False

mq3= rfmTable.monetary.quantile(q=0.75)
mq1= rfmTable.monetary.quantile(q=0.25)
miqr = mq3 - mq1
mlwr_bound = max(0,mq1 - (1.5*miqr))
mupr_bound = mq3 + (1.5*miqr)
print(mlwr_bound, mupr_bound)

def m_outliers(valor):
    return True if(valor < mlwr_bound or valor > mupr_bound) else False


# COMMAND ----------

rfmTable = rfmTable[rfmTable.recency.apply(lambda z: r_outliers(z))==False]
rfmTable = rfmTable[rfmTable.frequency.apply(lambda z: f_outliers(z))==False]
rfmTable = rfmTable[rfmTable.monetary.apply(lambda z: m_outliers(z))==False]

# COMMAND ----------

# MAGIC %md
# MAGIC #### Segmentación de Clientes <br>
# MAGIC En este método de segmentación utilizamos los Cuartiles de cada variable (RFM)<br> Q1=0.25, Q2=0.5 y Q3=0.75 para segmentar los clientes en base a la distribución de nuestros datos.<br>
# MAGIC _La tabla resultado representa los valores de corte para cada variable para segmentar._<br>
# MAGIC **Recency**
# MAGIC * El 25% de clientes compró hace ≤22 días, el 50% hace ≤55 días, el 75% hace ≤144 días.<br>
# MAGIC **frequency**
# MAGIC * El 25% hizo 1 compra, el 50% hizo ≤2 compras, el 75% hizo ≤4 compras.<br>
# MAGIC **Monetary**
# MAGIC * El 25% gastó ≤$275.64, el 50% gastó ≤$570.40, el 75% gastó ≤$1140.21

# COMMAND ----------

# DBTITLE 1,Cuartiles de cada Columna
quantiles = rfmTable.quantile(q=[0.25, 0.5, 0.75])
quantiles

# COMMAND ----------

# DBTITLE 1,Pasamos a un dict
quantiles = quantiles.to_dict()
quantiles

# COMMAND ----------

rfmSegment =  rfmTable
rfmSegment.head()

# COMMAND ----------

# MAGIC %md
# MAGIC #### Criterios de Clasificación
# MAGIC Creamos la función para la segmentacion RFM, asumiendo que: 
# MAGIC - Alta Recencia es mala
# MAGIC - Alta Frecuencia y Monetización son buenas.

# COMMAND ----------

# DBTITLE 1,Funciones de Clasificacion
#Argumentos (x= valor, p = recency, monetary, frequency, d = quartiles dict )
def RClassification(x, p, d):
    if x <= d[p][0.25]:
        return 4
    elif x <= d[p][0.50]:
        return 3
    elif x <= d[p][0.75]:
        return 2
    else:
        return 1

def FMClassification(x, p, d):
    if x <= d[p][0.25]:
        return 1
    elif x <= d[p][0.50]:
        return 2
    elif x <= d[p][0.75]:
        return 3
    else:
        return 4

# COMMAND ----------

quantiles

# COMMAND ----------

# DBTITLE 1,Llamada a las funciones de Clasificacion
rfmSegment['R_Cuartil'] = rfmSegment['recency'].apply(RClassification, args=('recency', quantiles,))
rfmSegment['F_Cuartil'] = rfmSegment['frequency'].apply(FMClassification, args=('frequency', quantiles,))
rfmSegment['M_Cuartil'] = rfmSegment['monetary'].apply(FMClassification, args=('monetary', quantiles,))

# COMMAND ----------

# DBTITLE 1,Creamos el campo de segmentacion
rfmSegment['rfmClass'] = rfmSegment.R_Cuartil.map(str) + rfmSegment.F_Cuartil.map(str) + rfmSegment.M_Cuartil.map(str)

# COMMAND ----------

rfmSegment.head()

# COMMAND ----------

rfmSegment = rfmSegment.reset_index()

# COMMAND ----------

rfmSegment.head()

# COMMAND ----------

# DBTITLE 1,Creamos los segmentos
from pyspark.sql import functions as F

rfmSegmentdf = rfmSegment.to_spark() \
                .withColumn("segment",
                    F.when((F.col("R_Cuartil") == 4) & (F.col("F_Cuartil") >= 3) & (F.col("M_Cuartil") >= 3), "Champions")
                    .when((F.col("F_Cuartil") == 4) & (F.col("R_Cuartil") >= 2) & (F.col("M_Cuartil") >= 2), "LoyalCustomers")
                    .when((F.col("R_Cuartil") >= 3) & (F.col("F_Cuartil") >= 2) & (F.col("M_Cuartil") >= 2), "PotentialLoyalists")
                    .when((F.col("R_Cuartil") == 4) & (F.col("F_Cuartil") == 1), "NewCustomers")
                    .when((F.col("R_Cuartil") <= 2) & (F.col("F_Cuartil") >= 3) & (F.col("M_Cuartil") >= 3), "AtRisk")
                    .otherwise("Hibernating")) \
                .withColumn("ingestionDt", F.lit(F.current_date()))

rfmSegmentdf.select("customerId", "recency", "frequency", "monetary", "rfmClass", "segment", "ingestionDt").createOrReplaceTempView("v_rfmSegment")

# COMMAND ----------

# DBTITLE 1,Ingesta final capa gold
try:
  spark.sql("""
            WITH rfmSegmentation AS(
                SELECT r.*,
                    g.primeraCompra,
                    g.ultimaCompra,
                    g.ticketPromedio,
                    g.unidadesPorTicket
                FROM v_rfmSegment r
                LEFT JOIN gld_sellout_online_retail g
                ON r.customerId = g.customerId) 
            MERGE INTO gld_rfm_online_retail t
            USING rfmSegmentation s
              ON t.customerId = s.customerId
              WHEN MATCHED THEN UPDATE SET *
              WHEN NOT MATCHED THEN INSERT *
             """)
  
  print("Ingreso al try")
except Exception as e:
  spark.sql("""
            CREATE TABLE gld_rfm_online_retail AS
             SELECT r.*,
                    g.primeraCompra,
                    g.ultimaCompra,
                    g.ticketPromedio,
                    g.unidadesPorTicket
            FROM v_rfmSegment r
            LEFT JOIN gld_sellout_online_retail g
            ON r.customerId = g.customerId
            """)

# COMMAND ----------

# DBTITLE 1,Reporting
# MAGIC %sql
# MAGIC SELECT * FROM gld_rfm_online_retail limit 5;

# COMMAND ----------

# MAGIC %md
# MAGIC #### Conclusiones
# MAGIC * La hipótesis principal es que los clientes que tienen el valores más **alto en el rfmClass son nuestros mejores clientes**. Debido a que compraron recientemente, varias veces y gastaron mas que otros clientes con rfmClass con un valor menor.
# MAGIC * En base a este campo rfmClass podemos segmentar nuestros clientes.
# MAGIC * Además se agregan a la capa gold atributos calculados que represetan el **ticket promedio** (_Cuanto gasta en promedio un cliente_) y **unidades por ticket** (_Cuantos productos compra en promedio un cliente_), las cuales nos permiten realizar otro tipo de analisis y segmentacion de ser necesario. 