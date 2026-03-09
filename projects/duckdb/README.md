### **DuckDB Essentials**<br>
> Motivación:<br>

Este proyecto es un ejercicio de aprendizaje enfocado en la implementación de un flujo ELT (Extract, Load, Transform) utilizando DuckDB.<br>
El objetivo es demostrar la capacidad de procesar grandes volúmenes de datos de manera local, eficiente y con una sintaxis SQL amigable, transformando datos crudos en formatos listos para el análisis (Analytics Ready).<br><br>

**Por qué DuckDB:**<br>
- *OLAP In-Process:* No requiere de un servidor externo (Como Postgres o SQL Server), lo que facilita el desarrollo local y la integración en contenedores o funciones serverless.<br>
- *Rendimiento Vectorizado:* Optimizado para consultas analíticas sobre grandes conjuntos de datos.<br>
- *Interoperabilidad:* Capacidad nativa para leer y escribir directamente en Parquet, CSV y Pandas sin sobrecarga de memoria.<br>
- *Sintaxis SQL Moderna:* Soporte para funciones avanzadas como REPLACE en SELECT *, PIVOT, y lectura automática de esquemas.<br><br>

> Estructura del Proyecto:<br>

projects-duckdb/<br>
├── data/                   # Datos crudos (CSV) a ser utilizados como source<br>
├── images/                 # Imagenes utilizadas para clarificar el cometido.<br> 
├── scripts/                # Lógica del ELT en Python.<br>
├── outputs/                # Salidas o sinks generados.<br>
└── README.md<br><br>

> Flujo ELT<br>

El pipeline realiza las siguientes etapas:<br>
1. **Extract & Load:** Carga de datos crudos desde un CSV de más de 22.5k filas (311 Service Requests) directamente a una tabla persistente en DuckDB.<br>
2. **Transform (T):** 
&nbsp;&nbsp;&nbsp;&nbsp; - Normalización de categorías de texto.<br><br>
![Falta Normalizar](images/ComplaintTypeCount.png)<br><br>
&nbsp;&nbsp;&nbsp;&nbsp; - Limpieza de Schema: Normalización programática de nombres de columnas (snake_case) usando Python + SQL.<br><br>
![Nombres de Columnas Conflictivos](images/DescribeElevatorRequests.png)<br><br>
&nbsp;&nbsp;&nbsp;&nbsp; - Feature Engineering: Cálculo de closed_in_days utilizando funciones de fecha nativas de DuckDB.<br>
3. **Output Multi-formato:** Exportación de los datos procesados a tres destinos:<br>
&nbsp;&nbsp;&nbsp;&nbsp; - Relacional: Tabla persistente en el archivo .duckdb.<br>
&nbsp;&nbsp;&nbsp;&nbsp; - Intercambio: Archivo .csv normalizado.<br>
&nbsp;&nbsp;&nbsp;&nbsp; - Analítico: Archivo .parquet (comprimido y eficiente para Big Data).<br><br>

> Aprendizaje<br><br>

- **Eficiencia:** El procesamiento de limpieza y cálculo de columnas se realiza en milisegundos gracias al motor columnar.<br>
- **Simplicidad:** Se reemplazaron múltiples pasos de manipulación en Pandas por sentencias SQL directas, reduciendo la complejidad del código.<br>
- **Portabilidad:** El resultado final en formato Parquet redujo el tamaño del archivo original considerablemente, manteniendo la tipificación de los datos.<br><br>
![Compresión Parquet File](images/CompressParquet.png)<br>