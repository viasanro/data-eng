# Implementación de Slowly Changing Dimension (SCD Type 2) con DuckDB

## Contexto / Problemática

En los sistemas analíticos es común que ciertos atributos de negocio cambien a lo largo del tiempo.
Un ejemplo típico es el catálogo de productos de una cadena de retail, donde un SKU puede cambiar su estado de catalogación, su asociación con una tienda o incluso su jerarquía organizacional.

En un **Data Warehouse**, es necesario mantener el historial de estos cambios para poder responder preguntas como:

* ¿Qué productos estaban catalogados en una tienda en una fecha determinada?
* ¿Cuándo cambió el estado de catalogación de un SKU?
* ¿Cómo evolucionó el catálogo en el tiempo?

Para resolver este problema se utiliza el patrón **Slowly Changing Dimension Type 2 (SCD Type 2)**, que permite conservar el historial completo de los cambios insertando nuevas versiones del registro en lugar de sobrescribir los datos.

Este proyecto implementa una **dimensión tipo 2 para un catálogo jerárquico de retail** utilizando:

* generación de datos sintéticos
* procesamiento SQL
* almacenamiento analítico local

---

# Arquitectura

El flujo del proceso sigue las siguientes etapas:

```
Faker (generación de datos)
        │
        ▼
Pandas DataFrame
        │
        ▼
DuckDB (tabla staging)
 AuxSourceCatalogo
        │
        ▼
Transformación SCD Type 2
        │
        ▼
SourceCatalogo
        │
        ▼
DimCatalogoSinPK
        │
        ▼
DimCatalogo (Dimensión final con PK)
        │
        ▼
Export Parquet
```

### Componentes principales

**1. Generación de datos**

Se utiliza la librería **Faker** para generar una estructura jerárquica simulada:

```
Holding
   └── Cadena
          └── Tienda
                 └── SKU
```

Cada registro contiene:

* holding
* cadena
* tienda
* sku
* catalogado (boolean)

Esto permite simular cambios de catálogo para probar la lógica de SCD.

---

**2. Staging Table**

Los datos generados se cargan en:

```
AuxSourceCatalogo
```

En esta etapa se generan:

* **key_catalogo** → clave natural concatenada
* **checksum** → hash MD5 para detectar cambios
* **fecha_ini / fecha_fin**
* **status** (S/N)

Esto facilita detectar modificaciones en los atributos.

---

**3. Detección de cambios**

Se crea la tabla **SourceCatalogo**, que contiene tres tipos de registros:

1️ **Registros nuevos**

```sql
WHERE NOT EXISTS (...)
```

2️ **Registros modificados**

Se detectan usando el `checksum`.

3️ **Registros a cerrar**

Cuando un registro cambia:

```
status = 'S' → 'N'
fecha_fin = nueva fecha
```

Esto permite preservar el historial.

---

**4. Reconstrucción de la dimensión**

Se genera una tabla intermedia:

```
DimCatalogoSinPK
```

Mediante un **FULL JOIN** entre:

* registros actuales
* registros históricos

Esto permite mantener tanto las versiones activas como las cerradas.

---

**5. Generación de Primary Key**

La dimensión final:

```
DimCatalogo
```

genera una **surrogate key incremental**:

```sql
ROW_NUMBER() OVER (ORDER BY key_catalogo) + maxid
```

Esto permite:

* mantener continuidad de claves
* evitar colisiones entre cargas

Además se agrega un registro especial:

```
pk = -1
key = DESCONOCIDO
```

Práctica común en modelos dimensionales.

---

# Decisiones Técnicas

### Uso de DuckDB

Se eligió **DuckDB** por:

* motor OLAP embebido
* alto rendimiento en consultas analíticas
* integración nativa con **Parquet**
* ideal para prototipos de pipelines analíticos

Permite simular un **Data Warehouse local sin infraestructura cloud**.

---

### Uso de checksum para detectar cambios

En lugar de comparar campo por campo:

```
holding
cadena
tienda
sku
catalogado
```

se utiliza un **MD5 hash**:

```
md5(concat(...))
```

Ventajas:

* comparación rápida
* SQL más limpio
* escalable cuando la dimensión tiene muchas columnas

---

### Generación de datos sintéticos

Se utiliza **Faker** para:

* simular datos realistas
* evitar dependencia de datos productivos
* facilitar reproducibilidad del proyecto

---

### Exportación a Parquet

La dimensión final se exporta a:

```
DimCatalogo.parquet
```

Esto permite:

* consumo por motores analíticos
* integración con data lakes
* compatibilidad con Spark, DuckDB, Pandas, etc.

---

# Impacto

Este proyecto demuestra cómo implementar un **patrón fundamental de modelado dimensional** en un pipeline de datos moderno.

Beneficios del enfoque:

* preservación completa del historial
* detección eficiente de cambios
* diseño reproducible
* arquitectura portable (local o cloud)

El pipeline puede adaptarse fácilmente para integrarse en:

* Spark
* Databricks
* dbt
* pipelines ELT

---

# Aprendizajes

Durante la implementación surgieron varios aprendizajes relevantes:

### Modelado dimensional

* cómo estructurar una **SCD Tipo 2**
* manejo de **claves naturales vs surrogate keys**
* control de versiones con fechas y status

---

### SQL analítico avanzado

Uso de:

* `ROW_NUMBER()`
* `FULL JOIN`
* `NOT EXISTS`
* `CHECKSUM / HASH`
* `WINDOW FUNCTIONS`

---

### Ingeniería de datos práctica

Este ejercicio permitió experimentar con:

* generación de datos sintéticos
* pipelines reproducibles
* staging tables
* exportación a formatos analíticos

---

# Tecnologías utilizadas

* Python
* DuckDB
* Pandas
* Faker
* SQL
* Parquet

---

# Posibles mejoras

* agregar **tests de calidad de datos**
* versionar cargas incrementales
* implementar el pipeline en **dbt**
* ejecutar sobre **Spark / Databricks**
* automatizar con **Airflow**

---

# Ejecución

Instalar dependencias:

```bash
pip install duckdb pandas faker
```

Ejecutar:

```bash
python Dim_Tipo2.py
```

Esto generará:

```
sources/source_catalog.parquet
outputs/DimCatalogo.parquet
outputs/catalogo.duckdb
```
