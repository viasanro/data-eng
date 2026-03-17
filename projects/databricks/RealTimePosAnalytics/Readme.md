**Este proyecto tratará sobre el Análisis de Punto de Venta en Tiempo Real.**<br><br>
>*Problemática:* 

La necesidad de datos en tiempo real en el segmento retail y como superar los desafíos del streaming de datos del punto de venta a escala con un datalakehouse.<br><br>
>*Enfoque Técnico:*  

El enfoque data lakehouse permite emplear múltiples modos de transmisión de datos en paralelo: streaming para datos de alta frecuencia e insert-oriented, y procesos por lotes o batch para eventos menos frecuentes y de mayor escala. Esto comunmente es referido como arquitecturas lambda.  
Se utilizará la arquitectura lambda junto con medallion con el patrón de diseño Bronze, Silver y Gold para aterrizar los datos en etapas.<br><br>
![Architecture](images/Architecture.png)<br><br>
Para ilustrar como la arquitectura lakehouse puede ser aplicada a los datos de un Punto de Venta, desarrollamos un workflow de demostracion dentro del cual calculamos un inventario Near Real Time. Para ello imaginamos 2 puntos de venta transmitiendo información relevante al inventario asociado, con ventas, reabastecimiento y perdidas, a través de transacciones de compras en linea y retiros en tiendas como parte de un inventario en streaming y por otro lado, un snapshot de las unidades de productos en piso que son capturadas por el POS y transmitidas por batch (lotes). Estos datos son simulados para un periodo de un mes y se muestran a una velocidad 10x mayor para una mejor visibilidad de los cambios de inventario.<br>
*El proyecto está diseñado para generar entradas en una ruta de almacenamiento (por ejemplo, DBFS/almacenamiento de objetos en la nube) y luego ingerirlas en tablas Delta utilizando un enfoque Lambda + Medallion.*

<br><br>

## Estructura del proyecto

- **`notebooks/`**: notebooks (exportados como `.py`) para correr en Databricks.
  - `00_Setup_And_Config.py`: config + creación de schemas (Bronze/Silver/Gold)
  - `01_Generate_Inputs_On_DBFS.py`: genera datos sintéticos directo en DBFS
  - `02_Bronze_Ingest.py`: ingesta Bronze (streaming + batch)
  - `03_Silver_Transform.py`: normalización a Silver
  - `04_Gold_Inventory_Near_Real_Time.py`: inventario Near Real Time (Gold)
  - `05_Inventory_SQL_Examples.sql`: queries SQL de ejemplo (Gold/Silver/Bronze)
- **`scripts/`**: generador local opcional de inputs (JSONL streaming + CSV batch).
- **`src/rtpa/`**: helpers (schemas/config/paths) instalables como paquete python.
- **`configs/`**: template de configuración.
- **`data/`**: opcional (si quieres generar inputs dentro del repo).

## Cómo ejecutar (Databricks)

### Opción A: generar inputs directamente en DBFS (más simple)

1) Importa este folder como Databricks Repo (o copia los notebooks a tu workspace).
2) Desde un cluster, instala el paquete del repo (para `import rtpa`):

```bash
%pip install -e .
```

3) Corre en orden:
- `notebooks/00_Setup_And_Config.py`
- `notebooks/01_Generate_Inputs_On_DBFS.py` (por defecto escribe en `dbfs:/tmp/rtpa`)
- `notebooks/02_Bronze_Ingest.py`
- `notebooks/03_Silver_Transform.py`
- `notebooks/04_Gold_Inventory_Near_Real_Time.py`

### Opción B: generar inputs localmente y luego subirlos a DBFS / cloud storage

Genera inputs en el repo:

```bash
python scripts/generate_synthetic_inputs.py --out data --start 2026-01-01T00:00:00Z --days 30 --stores 2 --skus 200
```

Luego copia `data/input/stream_pos_events` y `data/input/batch_floor_snapshots` a tus rutas de input en `dbfs:/tmp/rtpa/input/...` (o a un bucket y ajusta paths).

## Tablas resultantes (Delta)

- **Bronze**
  - `rtpa_bronze.pos_events_stream`
  - `rtpa_bronze.floor_snapshots_batch`
- **Silver**
  - `rtpa_silver.inventory_movements` (movimientos con signo)
  - `rtpa_silver.floor_snapshots`
- **Gold**
  - `rtpa_gold.inventory_nrt` (inventario NRT por tienda y SKU)
