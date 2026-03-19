## **Análisis de Punto de Venta en Tiempo Real.**<br><br>
> *Metodología:*

Este proyecto fué desarrollado bajo un enfoque de **Ingeniría de Datos Mederna** priorizando la arquitectura y la eficiencia mediante el uso de herramientas de IA (**AI-Augmented Engineering**).<br>
Diseñe la arquitectura del sistema, los contratos de datos y la lógica de Medallion, aprovechando Cursor AI para la generación de código repetitivo y su optimización.<br>
Esto me permitió centrarme en los desafíos de ingeniería de alto nivel y la calidad de datos.<br><br>

>*Problemática:* 

La necesidad de datos en tiempo real en el segmento retail y como superar los desafíos del streaming de datos del punto de venta a escala con un datalakehouse.<br><br>
>*Enfoque Técnico:*  

El enfoque data lakehouse permite emplear múltiples modos de transmisión de datos en paralelo: streaming para datos de alta frecuencia e insert-oriented, y procesos por lotes o batch para eventos menos frecuentes y de mayor escala. Esto comunmente es referido como arquitecturas lambda.  
Se utilizará la arquitectura lambda junto con medallion con el patrón de diseño Bronze, Silver y Gold para aterrizar los datos en etapas.<br><br>
![Architecture](images/Architecture.png)<br><br>
Para ilustrar como la arquitectura lakehouse puede ser aplicada a los datos de un Punto de Venta, desarrollamos un workflow de demostracion dentro del cual calculamos un inventario Near Real Time.
Para ello imaginamos 2 puntos de venta transmitiendo información relevante al inventario asociado, con ventas, reabastecimiento y perdidas, a través de transacciones de compras en linea y retiros en tiendas como parte de un inventario en streaming y por otro lado, un snapshot de las unidades de productos en piso que son capturadas por el POS y transmitidas por batch (lotes).
Estos datos son simulados para un periodo de un mes y se muestran a una velocidad 10x mayor para una mejor visibilidad de los cambios de inventario.
*El proyecto está diseñado para generar entradas directamente en tablas Delta gestionadas, evitando dependencias de DBFS para garantizar compatibilidad total con Databricks Serverless Free Edition.*
<br><br>
## Estructura del proyecto

- **`notebooks/`**: notebooks (exportados como `.py`/`.sql`) para correr en Databricks Serverless.
  - `rtpa_lib.py`: librería compartida (Serverless-friendly). Los demás notebooks hacen `%run ./rtpa_lib`.
  - `00_Setup_And_Config.py`: config + creación de schemas (Bronze/Silver/Gold)
  - `01_Generate_Inputs_On_DBFS.py`: genera datos sintéticos directo en tablas Delta gestionadas (Serverless-compatible)
  - `02_Bronze_Ingest.py`: validación y procesamiento de datos Bronze (Serverless-compatible)
  - `03_Silver_Transform.py`: normalización a Silver
  - `04_Gold_Inventory_Near_Real_Time.py`: inventario Near Real Time (Gold)
  - `05_Inventory_SQL_Examples.sql`: queries SQL de ejemplo (Gold/Silver/Bronze)
- **`scripts/`**: generador local opcional de inputs (JSONL streaming + CSV batch).
- **`configs/`**: template de configuración (opcional).
- **`data/`**: opcional (si quieres generar inputs dentro del repo).

## Cómo ejecutar (Databricks Serverless Free Edition)

### Flujo principal recomendado (Serverless-compatible)

1) Importa este folder como Databricks Repo (o copia los notebooks a tu workspace, puedes comprimir la carpeta a .zip y luego importarla desde Databricks👌).<br>
**Nota:** todos usan `%run ./rtpa_lib` para compartir código; no necesitas instalar paquetes):
2) Ejecución secuencial:
- `notebooks/00_Setup_And_Config.py` (crea schemas y configura la base de datos)
- `notebooks/01_Generate_Inputs_On_DBFS.py` (genera datos sintéticos directamente en tablas Bronze gestionadas)
- `notebooks/02_Bronze_Ingest.py` (valida y procesa datos Bronze existentes)
- `notebooks/03_Silver_Transform.py` (transforma datos a capa Silver)
- `notebooks/04_Gold_Inventory_Near_Real_Time.py` (calcula inventario NRT en capa Gold)
- *Bonus:* `notebook/05_Inventory_SQL_Examples.sql` (para realizar consultas de pruebas sobre el dataset final generado) 

### Características Serverless

✅ **Sin dependencias de DBFS**: Todas las operaciones usan tablas Delta gestionadas  
✅ **Sin checkpoints externos**: No requiere rutas de almacenamiento externas  
✅ **Streaming seguro**: Evita operaciones de streaming que requieren DBFS  
✅ **Validación de datos**: Incluye verificación de calidad y limpieza de datos  
✅ **Compatible con Serverless Free Edition**: Funciona completamente en entornos serverless

### Opción avanzada: generar inputs localmente (solo para entornos con DBFS habilitado)

> **Nota**: Esta opción requiere acceso a DBFS y no es compatible con Databricks Serverless Free Edition.

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
 
## 🧠 Desafíos y Aprendizajes
1. Desarrollo Asistido y Curación Técnica (AI-Augmented Engineering)<br>
- Ajuste y Refinamiento: Capacidad para identificar fallos en el código generado por IA, ajustando la lógica hasta lograr una solución end-to-end funcional.<br>
- Prompt Engineering de Arquitectura: Definición clara de contratos de datos y estructuras de directorios desde el README.md para guiar a la IA hacia resultados precisos.<br>
2. Resolución de Aislamiento en Entornos Cloud (Databricks Serverless)<br>
Uno de los mayores desafíos fue la gestión de dependencias y rutas dinámicas en un entorno de Databricks Community Edition. Aprendí a:<br>
- Implementar un sistema de inyección de rutas dinámicas mediante sys.path y dbutils, permitiendo que el proyecto sea 100% portátil sin hardcoding.<br>
3. Visión End-to-End
- El proyecto reforzó mi capacidad para ver el flujo completo: desde la necesidad de negocio (KPIs de logística y retail) hasta la implementación técnica de un simulador de eventos en tiempo real con integridad de datos (Delta Lake).
