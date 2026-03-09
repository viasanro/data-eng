import duckdb
import re
import os

# Creamos una nueva base de datos llamada etl
# Esto cambia la carpeta de trabajo de la terminal a la carpeta donde está el script
os.chdir(os.path.dirname(os.path.abspath(__file__)))
con = duckdb.connect("..\\outputs\\etl.duckdb")

# Paso 1: Carga Local (L)
con.execute("""
            CREATE OR REPLACE TABLE service_requests AS
            SELECT * FROM read_csv_auto('..\\data\\311_Elevator_Service_Requests_.csv', header=True);
            """)

# Paso 2: Transformación Local (T)
# Creamos una nueva tabla con los datos del campo "Complaint Type" normalizados en minusculas.
con.execute("""
  CREATE OR REPLACE TABLE clean_requests AS
  SELECT * REPLACE (LOWER("Complaint Type") AS "Complaint Type")
  FROM service_requests;
""")

# Paso 3: Normalizamos los nombres de las columnas de la tabla clean_requests
cols = con.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'clean_requests'
    ORDER BY ordinal_position;
""").fetchall()

def normalize_colname(name: str) -> str:
    s = name.strip().lower().replace(" ", "_")
    s = re.sub(r'[^a-z0-9_]', '_', s)
    s = re.sub(r'_+', '_', s)
    return s

for (col,) in cols:
    new = normalize_colname(col)
    if new != col:  # Solo renombrar si cambio.
        sql = f'ALTER TABLE clean_requests RENAME COLUMN "{col}" TO {new};'
        print("Executing:", sql)
        con.execute(sql)
        
# Paso 4: Verificación
df = con.execute("DESCRIBE clean_requests;").fetchdf()
print(df)

# Paso 5: Agregamos la columna closed_in_days a la tabla de dimensiones
con.execute("""
  ALTER TABLE clean_requests
  ADD COLUMN closed_in_days INTEGER
""")
# con.execute("COMMIT;")

# Paso 6: Poblamos la columna closed_in_days con la diferencia en días entre created_date y closed_date
con.execute("""
  UPDATE clean_requests
  SET closed_in_days = DATEDIFF('day', created_date, closed_date)
""")

# Paso 7: Verificación
print(con.execute("""
    SELECT created_date, closed_date, closed_in_days
    FROM clean_requests
    WHERE closed_date IS NOT NULL
    LIMIT 10;
""").fetchdf())

# Commiteamos todos los cambios para asegurarnos de que se guarden en la base de datos.
con.commit()

# Exportamos los datos a CSV
csv_path = "..\\outputs\\clean_requests.csv"
con.execute(f"""
    COPY clean_requests TO '{csv_path}' (HEADER, DELIMITER ',');
""")
print(f"Exported clean_requests to {csv_path}")

# Exportamos los datos a Parquet
parquet_path = "..\\outputs\\clean_requests.parquet"
con.execute(f"""
    COPY clean_requests TO '{parquet_path}' (FORMAT PARQUET);
""")
print(f"Exported clean_requests to {parquet_path}")


# Podemos consultar el parquet de la siguiente forma:
df = con.execute("""
    SELECT complaint_type, COUNT(*) AS issues
    FROM read_parquet('..\\outputs\\clean_requests.parquet')
    GROUP BY complaint_type
    ORDER BY issues DESC
    LIMIT 10;
""").fetchdf()
print(df)

# Cerramos la conexión a la base de datos.
con.close()
print("Conexión cerrada y cambios persistidos.")