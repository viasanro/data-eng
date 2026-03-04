## Creacion de una SCD Type2.

Para este ejemplo utilizamos un motor SQL SEVER en el cual creamos una base de datos BD_DWH.

En el ejemplo asumimos que tenemos creada nuestra tabla dim_productos en el esquema dim. Esta tabla tiene 
una pk_producto INT IDENTITY(1,1) PRIMARY KEY.

Ademas los datos son insertados desde un area de staging donde existe una tabla stg_productos en el esquema stg.

Tambien logueamos el estado de ejecucion en una tabla de auditoria llamada audit_dimensionales en el esquema dim.

El proceso se divide en 3 pasos:
1) Insertar los registros nuevos (Que no existian previamente)
2) Insertar registros actualizados (Ya existian previamente en la tabla target pero sufrieron cambios)
3) Actualizar los registros existentes en el target que sufrieron alguna modificacion y fueron reemplazados por los del punto 2
