import os
import duckdb
import pyspark.sql.functions as F
from pyspark.sql import SparkSession
from faker import Faker
import random
import pandas as pd

# spark = SparkSession.builder.appName("SCD_Type2_Dim").getOrCreate()

# Esto cambia la carpeta de trabajo de la terminal a la carpeta donde está el script
# Creamos una nueva base de datos llamada catalogo
os.chdir(os.path.dirname(os.path.abspath(__file__)))
con = duckdb.connect("..\\outputs\\catalogo.duckdb")

# Generamos los datos falsos para la tabla de catálogo.
# Configuramos Faker para que hable español (es-ES)
fake = Faker(['es_ES'])

holdings = ["Cencosud", "Tottus", "Walmart", "Smu"]

cadenas_por_holding = {
    "Cencosud": ["Jumbo", "Disco", "Santa Isabel"],
    "Tottus": ["Carrefour", "Market", "Tottus"],
    "Walmart": ["Acuenta", "Supercenter", "Lider"],
    "Smu": ["Smu", "Mayorista10", "Unimarc"]
}

rows = []

tiendas_por_cadena = 5
skus_por_tienda = 20

for holding in holdings:

    for cadena in cadenas_por_holding[holding]:

        for _ in range(tiendas_por_cadena):

            tienda = f"T-{fake.city()}"

            for _ in range(skus_por_tienda):

                sku = f"{fake.random_int(100,999)}"
                catalogado = random.choice([True, False])

                rows.append({
                    "holding": holding,
                    "cadena": cadena,
                    "tienda": tienda,
                    "sku": sku,
                    "catalogado": catalogado
                })

# Creamos el DataFrame de Pandas y lo registramos como una tabla temporal en DuckDB
# Esta tabla temporal simula la fuente de datos que se usaría para alimentar la dimensión de catálogo.
df_catalogo = pd.DataFrame(rows)
con.register("source_catalogo", df_catalogo)
con.execute("""
            CREATE OR REPLACE TABLE AuxSourceCatalogo AS
            SELECT DISTINCT
                concat(holding, cadena, tienda, sku) AS key_catalogo,
                holding,
                cadena,
                tienda,
                sku,
                catalogado,
                md5(concat(holding, cadena, tienda, sku, catalogado)) AS checksum,
                cast(cast(current_timestamp AS date) AS varchar) AS fecha_ini,
                '9999-12-31' AS fecha_fin,
                'S' AS status
            FROM source_catalogo;
            """)

print(con.execute("SELECT * FROM AuxSourceCatalogo LIMIT 5;").fetchdf())
print("Filas generadas:", len(df_catalogo))

# Exportamos los datos a Parquet
parquet_path = "..\\sources\\source_catalog.parquet"
con.execute(f"""
    COPY AuxSourceCatalogo TO '{parquet_path}' (FORMAT PARQUET);
""")
print(f"Exported AuxSourceCatalogo to {parquet_path}")

# Implementamos la logica de SCD Tipo 2 para la dimension de catalogo.
try:
    con.execute("SELECT * FROM DimCatalogo LIMIT 1;")
    # Si existe la DimCatalogo, procedemos con la logica de SCD Tipo 2.
    # -- Registros nuevos a insertar
    # -- Registros modificados a insertar
    # -- Registros a actualizar y sobreescribir en la Dim
    con.execute("""
                CREATE OR REPLACE TABLE SourceCatalogo AS

                SELECT c.* 
                FROM AuxSourceCatalogo c
                WHERE NOT EXISTS (
                    SELECT 1 
                    FROM DimCatalogo d 
                    WHERE d.key_catalogo = c.key_catalogo
                )

                UNION

                SELECT c.* 
                FROM AuxSourceCatalogo c
                JOIN DimCatalogo d 
                ON d.key_catalogo = c.key_catalogo
                WHERE d.checksum != c.checksum
                AND d.status = 'S'

                UNION

                SELECT 
                    d.key_catalogo,
                    d.holding,
                    d.cadena,
                    d.tienda,
                    d.sku,
                    d.catalogado,
                    d.checksum,
                    d.fecha_ini,
                    c.fecha_ini AS fecha_fin,
                    'N' AS status
                FROM AuxSourceCatalogo c
                JOIN DimCatalogo d 
                ON d.key_catalogo = c.key_catalogo
                WHERE d.checksum != c.checksum
                AND d.status = 'S'
                """)

except duckdb.CatalogException:
    # Si la DimCatalogo no existe, simplemente insertamos todos los registros de la fuente.
    con.execute("""
                CREATE OR REPLACE TABLE SourceCatalogo AS
                SELECT * FROM AuxSourceCatalogo;
                """)
    print("SourceCatalogo table created.")

# Nueva Dim sin PK
try:
    con.execute("SELECT * FROM DimCatalogo LIMIT 1;")
    # Si existe la DimCatalogo, actualizamos los registros existentes y luego insertamos los nuevos.
    con.execute(""" 
                CREATE OR REPLACE TABLE DimCatalogoSinPK AS
                SELECT 
                    COALESCE(c.key_catalogo, d.key_catalogo)    AS key_catalogo,
                    COALESCE(c.holding, d.holding)              AS holding,
                    COALESCE(c.cadena, d.cadena)                AS cadena,
                    COALESCE(c.tienda, d.tienda)                AS tienda,
                    COALESCE(c.sku, d.sku)                      AS sku,
                    COALESCE(c.catalogado, d.catalogado)        AS catalogado,
                    COALESCE(c.checksum, d.checksum)            AS checksum,
                    COALESCE(c.fecha_ini, d.fecha_ini)          AS fecha_ini,
                    COALESCE(c.fecha_fin, d.fecha_fin)          AS fecha_fin,
                    COALESCE(c.status, d.status)                AS status
                FROM SourceCatalogo c
                FULL JOIN DimCatalogo d ON d.key_catalogo = c.key_catalogo
    """)
except duckdb.CatalogException:
    # Si la DimCatalogo no existe, simplemente insertamos todos los registros de la fuente.
    con.execute("""
                CREATE OR REPLACE TABLE DimCatalogoSinPK AS
                SELECT * FROM SourceCatalogo;
                """)
    print("DimCatalogoSinPK table created.")

# Agregamos la PK a la Dim
try:
    con.execute(""" 
                CREATE OR REPLACE TABLE DimCatalogo AS
                SELECT
                    CAST(COALESCE(dim.pk_catalogo, ROW_NUMBER() OVER (ORDER BY dim.key_catalogo) + cntrl.maxid) AS INTEGER) AS pk_catalogo
                    ,csk.key_catalogo
                    ,csk.holding
                    ,csk.cadena
                    ,csk.tienda
                    ,csk.sku
                    ,csk.catalogado
                    ,csk.checksum
                    ,csk.fecha_ini
                    ,csk.fecha_fin
                    ,csk.status
                    ,CAST(current_timestamp AS datetime) AS last_update
                FROM DimCatalogoSinPK csk
                CROSS JOIN (SELECT COALESCE(MAX(CAST(pk_catalogo AS INTEGER)), 0) AS maxid FROM DimCatalogo) cntrl
                LEFT JOIN DimCatalogo dim ON dim.key_catalogo = csk.key_catalogo
                WHERE dim.key_catalogo != 'DESCONOCIDO'
                UNION
                SELECT -1           AS pk_catalogo
                    ,'DESCONOCIDO'  AS key_catalogo 
                    ,'-1'           AS holding
                    ,'DESCONOCIDO'  AS cadena
                    ,'DESCONOCIDO'  AS tienda
                    ,'-1'           AS sku
                    ,'-1'           AS catalogado
                    ,'DESCONOCIDO'  AS checksum
                    ,'DESCONOCIDO'  AS fecha_ini
                    ,'DESCONOCIDO'  AS fecha_fin
                    ,'S'            AS status
                    ,CAST(current_timestamp AS datetime) AS last_update
                """)
except Exception as e:
    print("DimCatalogo no existe, sera creada...", e)
    con.execute(""" 
                CREATE OR REPLACE TABLE DimCatalogo AS
                SELECT
                    CAST(ROW_NUMBER() OVER (ORDER BY key_catalogo) AS INTEGER) AS pk_catalogo
                    ,key_catalogo
                    ,holding
                    ,cadena
                    ,tienda
                    ,sku
                    ,catalogado
                    ,checksum
                    ,fecha_ini
                    ,fecha_fin
                    ,status
                    ,CAST(current_timestamp AS datetime) AS last_update
                FROM DimCatalogoSinPK
                UNION
                SELECT -1           AS pk_catalogo
                    ,'DESCONOCIDO'  AS key_catalogo 
                    ,'-1'           AS holding
                    ,'DESCONOCIDO'  AS cadena
                    ,'DESCONOCIDO'  AS tienda
                    ,'-1'           AS sku
                    ,'-1'           AS catalogado
                    ,'DESCONOCIDO'  AS checksum
                    ,'DESCONOCIDO'  AS fecha_ini
                    ,'DESCONOCIDO'  AS fecha_fin
                    ,'S'            AS status
                    ,CAST(current_timestamp AS datetime) AS last_update
                """)
    print("DimCatalogo table created.")

# Exportamos los datos a Parquet
parquet_path = "..\\outputs\\DimCatalogo.parquet"
con.execute(f"""
    COPY DimCatalogo TO '{parquet_path}' (FORMAT PARQUET);
""")
print(f"Exported DimCatalogo to {parquet_path}")

# Consultamos el parquet de la siguiente forma:
df = con.execute("""
    SELECT *
    FROM read_parquet('..\\outputs\\DimCatalogo.parquet')
    LIMIT 5;
""").fetchdf()
print(df)