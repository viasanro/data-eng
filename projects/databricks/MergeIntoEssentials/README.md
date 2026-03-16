# Ingesta de datos con MERGE INTO

> Motivación

MERGE INTO en databricks es una poderosa herramienta para ingesta de datos. Permite realizar de manera eficiente, atómica y escalable operaciones de upsert y delete.

> Objetivos:

* Utilizar MERGE INTO para realizar updates, inserts y deletes sobre tablas Delta.
* Aplicar MERGE INTO con schema enforcement para gestionar la integridad de los datos.
* Aplicar MERGE INTO con schema evolution para evolucionar la tabla destino.

**Nota:** Si bien aqui creamos pequeñas tablas para simular los datos entrantes, la idea es entender la utilidad de la herramienta y los casos de usos a los que esta podría aplicar.

> Componentes principales:

* **Catalog:** dbacad
* **Schema:** Creado dinámicamente por usuario
* **Target Table:** main_users_target
* **Source Tables:** 
&nbsp;&nbsp;&nbsp;&nbsp; update_users_source
&nbsp;&nbsp;&nbsp;&nbsp; new_users_source

> MERGE INTO

Como parte de la ingesta puedes realizar inserts, updates y deletes usando una tabla, vista o dataframe de origen y una tabla Delta de destino usand la operación MERGE de SQL. Además Databricks soporta una sintaxis extendida para facilitar casos de usos avanzados.

```
MERGE [WITH SCHEMA EVOLUTION] INTO target t
USING source s
ON {merge_condition}
WHEN MATCHED THEN {matched_action}
WHEN NOT MATCHED THEN {not_matched_action}
```

> Aprendizajes

* Podemos usar MERGE INTO para realizar una ingesta a partir de un sistema CDC.
* El SCHEMA ENFORCEMENT está habilitado por default en las tablas Delta.
Es decir, se validan los datos entrantes contra el esquema existente, sino coincide la operación falla.
&nbsp;&nbsp;&nbsp;&nbsp; 1. Esto genera pipelines predecibles
&nbsp;&nbsp;&nbsp;&nbsp; 2. Asegura la consistencia de los datos
&nbsp;&nbsp;&nbsp;&nbsp; 3. Nos protege contra cambios accidentales de esquema
* Que ocurre si tu origen de datos evoluciona y agrega nuevas columnas?
Podemos usar **MERGE INTO WITH SCHEMA EVOLUTION target_table** para actualizar el esquema en la tabla destino. (Requiere del Runtime 15.2 para arriba).
Tambien se puede setear a el valor de la variable *spark.databricks.delta.schema.AutoMerge.enable* a true
* La sentencia **DESCRIBE HISTORY table_name** nos permite inspeccionar el historial de las operaciones realizadas sobre la tabla en cuestión.
* La sentencia **SELECT * FROM VERSION AS OF version_number** nos permite realizar el llamado *Time Travel* y visualizar los datos de una versión particular de la tabla en un momento determinado.

> Cómo ejecutarlo

1. Abre la notebook en databricks
2. Corre todas las celdas secuencialmente

*La notebook hará lo siguiente*
* Creará el esquema.
* Generará datos sintéticos de origen.
* Creara la tabla Delta de destino.
* Ejecutará operaciones de MERGE.
* Demostrará Schema Enforcement y Schema  Evolution.


