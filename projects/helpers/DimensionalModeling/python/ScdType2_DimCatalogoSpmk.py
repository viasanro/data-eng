# Databricks notebook source
from pyspark.sql.functions import md5, concat, col

# COMMAND ----------

# MAGIC %sql
# MAGIC refresh table schemax.tbl_catalogo_instock;
# MAGIC refresh table schemax.tmp_catalogo_instock;

# COMMAND ----------

df_catalogo_spmk = spark.sql("""
                          select distinct concat(lower(trim(bandera)), '-', lower(trim(cadena)), '-', codcadena, '-', codigoabi) as key_catalogo
                            ,activocodigoabi as activo_cod_abi
                            ,bandera
                            ,cadena
                            ,codcadena as codigo_cadena
                            ,codigoabi as codigo_abi
                            ,catalogado
                            ,cast(getdate() as date) as fecha_ini
                            ,'9999-12-31' as fecha_fin
                            ,'S' as status
                          from schemax.tbl_catalogo_instock
                        """)
df_catalogo_spmk = df_catalogo_spmk.withColumn("checksum", md5(concat(df_catalogo_spmk.bandera, df_catalogo_spmk.cadena, df_catalogo_spmk.codigo_cadena, df_catalogo_spmk.codigo_abi, df_catalogo_spmk.activo_cod_abi, df_catalogo_spmk.catalogado)))
df_catalogo_spmk.createOrReplaceTempView('AuxSourceCatalogoSpmk')

# COMMAND ----------

# DBTITLE 1,Change Data Capture
try:
  path_dim_catalogo = '/mnt/zone/Country/Domain/SubDomain/DimCatalogoSpmk'
  df_dim_catalogo = spark.read.format('parquet').load(path_dim_catalogo)
  df_dim_catalogo.createOrReplaceTempView('DimCatalogoSpmk')

  source_catalogo_spmk = spark.sql("""
                                     -- Registros nuevos a insertar
                                        select c.* 
                                        from AuxSourceCatalogoSpmk c
                                        where not exists (select * from DimCatalogoSpmk d where c.key_catalogo = d.key_catalogo)
                                        union
                                    -- Registros modificados a insertar
                                        select c.* 
                                        from AuxSourceCatalogoSpmk c
                                        join DimCatalogoSpmk d on c.key_catalogo = d.key_catalogo
                                        and c.checksum != d.checksum
                                        and d.status = 'S'
                                        union
                                    -- Registros a actualizar y sobreescribir en la Dim
                                        select d.key_catalogo
                                              ,d.activo_cod_abi 
                                              ,d.bandera 
                                              ,d.cadena 
                                              ,d.codigo_cadena 
                                              ,d.codigo_abi
                                              ,d.catalogado 
                                              ,d.fecha_ini
                                              ,c.fecha_ini as fecha_fin
                                              ,'N' as status
                                              ,d.checksum
                                        from AuxSourceCatalogoSpmk c
                                        join DimCatalogoSpmk d on c.key_catalogo = d.key_catalogo
                                        and c.checksum != d.checksum
                                        and d.status = 'S'
                                    """)
except Exception as e:
  if 'Path does not exist' in str(e):
    source_catalogo_spmk = df_catalogo_spmk.select("*")

source_catalogo_spmk.createOrReplaceTempView('SourceCatalogoSpmk')

# COMMAND ----------

# DBTITLE 1,Nueva Dim Sin PK
try:
  path_dim_catalogo = '/mnt/zone/Country/Domain/SubDomain/DimCatalogoSpmk'
  df_dim_catalogo = spark.read.format('parquet').load(path_dim_catalogo)
  df_dim_catalogo.createOrReplaceTempView('DimCatalogoSpmk')

  df_dim_catalogo_sin_pk = spark.sql("""
                                     select coalesce(c.key_catalogo, d.key_catalogo)      as key_catalogo
                                            ,coalesce(c.activo_cod_abi, d.activo_cod_abi) as activo_cod_abi
                                            ,coalesce(c.bandera, d.bandera)               as bandera
                                            ,coalesce(c.cadena, d.cadena)                 as cadena
                                            ,coalesce(c.codigo_cadena, d.codigo_cadena)   as codigo_cadena 
                                            ,coalesce(c.codigo_abi, d.codigo_abi)         as codigo_abi
                                            ,coalesce(c.catalogado, d.catalogado)         as catalogado
                                            ,coalesce(c.fecha_ini, d.fecha_ini)           as fecha_ini
                                            ,coalesce(c.fecha_fin, d.fecha_fin)           as fecha_fin
                                            ,coalesce(c.status, d.status)                 as status   
                                            ,coalesce(c.checksum, d.checksum)             as checksum
                                        from SourceCatalogoSpmk c
                                        full join DimCatalogoSpmk d 
                                        on c.key_catalogo = d.key_catalogo
                                    """)
except Exception as e:
  if 'Path does not exist' in str(e):
    df_dim_catalogo_sin_pk = df_catalogo_spmk.select("*")

df_dim_catalogo_sin_pk.createOrReplaceTempView('DimCatalogoSpmkSinPk')

# COMMAND ----------

# DBTITLE 1,Agregamos la PK a la Dim
try:
  dim_catalogo_spmk = spark.sql("""
                            SELECT CAST(coalesce(dim.pk_catalogo, sum(1) OVER (ORDER BY dim.key_catalogo ROWS UNBOUNDED PRECEDING ) + cntrl.maxid) AS int) AS pk_catalogo
                                  ,csk.key_catalogo
                                  ,csk.activo_cod_abi
                                  ,csk.bandera
                                  ,csk.cadena
                                  ,csk.codigo_cadena
                                  ,csk.codigo_abi
                                  ,csk.catalogado
                                  ,csk.fecha_ini
                                  ,csk.fecha_fin
                                  ,csk.status
                                  ,csk.checksum
                                  ,CAST(getdate() AS date) AS last_update
                            FROM DimCatalogoSpmkSinPk csk
                            CROSS JOIN (SELECT coalesce(max(cast(pk_catalogo as int)), 0) AS maxid FROM DimCatalogoSpmk) cntrl
                            LEFT JOIN DimCatalogoSpmk dim
                            ON csk.key_catalogo = dim.key_catalogo
                            WHERE dim.key_catalogo != 'DESCONOCIDO'
                            UNION
                            SELECT -1 AS pk_catalogo
                                  ,'DESCONOCIDO' AS key_catalogo
                                  ,'-1' AS activo_cod_abi
                                  ,'DESCONOCIDO' AS bandera
                                  ,'DESCONOCIDO' AS cadena
                                  ,'-1' AS codigo_cadena
                                  ,'-1' AS codigo_abi
                                  ,'-1' AS catalogado
                                  ,CAST(getdate() AS date) AS fecha_ini
                                  ,'9999-12-31' AS fecha_fin
                                  ,'S' AS status
                                  ,'DESCONOCIDO' AS checksum
                                  ,CAST(getdate() AS date) AS last_update """)
except Exception as e:
  dim_catalogo_spmk = spark.sql("""
                            SELECT CAST(sum(1) OVER (ORDER BY csk.key_catalogo ROWS UNBOUNDED PRECEDING ) AS int) AS pk_catalogo
                                  ,csk.key_catalogo
                                  ,csk.activo_cod_abi
                                  ,csk.bandera
                                  ,csk.cadena
                                  ,csk.codigo_cadena
                                  ,csk.codigo_abi
                                  ,csk.catalogado
                                  ,csk.fecha_ini
                                  ,csk.fecha_fin
                                  ,csk.status
                                  ,csk.checksum
                                  ,CAST(getdate() AS date) AS last_update
                            FROM DimCatalogoSpmkSinPk csk
                            UNION
                            SELECT -1 AS pk_catalogo
                                  ,'DESCONOCIDO' AS key_catalogo
                                  ,'-1' AS activo_cod_abi
                                  ,'DESCONOCIDO' AS bandera
                                  ,'DESCONOCIDO' AS cadena
                                  ,'-1' AS codigo_cadena
                                  ,'-1' AS codigo_abi
                                  ,'-1' AS catalogado
                                  ,CAST(getdate() AS date) AS fecha_ini
                                  ,'9999-12-31' AS fecha_fin
                                  ,'S' AS status
                                  ,'DESCONOCIDO' AS checksum
                                  ,CAST(getdate() AS date) AS last_update """)

# COMMAND ----------

dim_catalogo_spmk.display()

# COMMAND ----------

try:
  # Saving on DL
  cz_path = '/mnt/zonoe/country/Domain/SubDomain/DimCatalogoSpmk'
  dim_catalogo_spmk.write.mode('overwrite').format('parquet').save(cz_path)
except Exception as e:
  raise e

# COMMAND ----------

spark.read.format('parquet').load('/mnt/zone/Country/Domain/SubDomain/DimCatalogoSpmk').display()
