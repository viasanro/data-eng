/* Creamos nuestra SCD Type2 para gestionar
 * el control de cambio en los registros y 
 * poder trackear la historia. El mismo se divide en 3 etapas
 * a) Insertar registros nuevos (no existian previamente).
 * b) Insertar registros "nuevos" (existentes que fueron modificados).
 * c) Actualizar registros existentes que sufrieron modificaciones.
 * */

USE BD_DWH;


INSERT INTO dim.audit_dimensionales(modulo, tabla, inicio, estado) 
SELECT 'Comercial Ventas', 'dim_productos', GETDATE(), 'P';


IF NOT EXISTS (SELECT pk_producto FROM dim.dim_productos WHERE pk_producto = -1)
BEGIN
	SET IDENTITY_INSERT dim.dim_productos ON;

	INSERT INTO dim.dim_productos(pk_producto, id_empresa, id_producto, prd_codigo, prd_descripcion, prd_tipo, prd_clase
								,prd_estado, prd_grupo, prd_seccion, prd_categoria, prd_unidad, prd_proveedor, prd_color
								,check_sum, last_updated, updated_by, fecha_efectiva, fecha_fin, registro_actual)
	VALUES(-1, -1, -1, 'DESCONOCIDO', 'DESCONOCIDO', 'DESCONOCIDO', 'DESCONOCIDO'
			, 'DESCONOCIDO', 'DESCONOCIDO', 'DESCONOCIDO', 'DESCONOCIDO', 'DESCONOCIDO', 'DESCONOCIDO', 'DESCONOCIDO'
			,-1, getdate(), suser_sname(), CAST(getdate() AS DATE), '9999-12-31', 'Y');

	SET IDENTITY_INSERT dim.dim_productos OFF;
END;


--Registros NUEVOS a INSERTAR en la dim usando where not exists
INSERT INTO dim.dim_productos 
SELECT sp.id_empresa 
		,sp.id_producto  
		,sp.prd_codigo 
		,sp.prd_descripcion
		,sp.prd_tipo
		,sp.prd_clase
		,sp.prd_estado 
		,sp.prd_grupo 
		,sp.prd_seccion 
		,sp.prd_categoria 
		,sp.prd_unidad 
		,sp.prd_razon_social 
		,sp.prd_color 
		,sp.prd_checksum 
		,sp.prd_lastupdate 
		,sp.prd_updatedby 
		,CAST(getdate() AS DATE) EffectiveDate
		,'9999-12-31' EndDate
		,'Y' CurrentRecord
FROM stg.stg_productos sp
WHERE NOT EXISTS (SELECT * FROM dim.dim_productos dp
				  	WHERE dp.id_empresa = sp.id_empresa and dp.id_producto = sp.id_producto);
				  	

--Registros a INSERTAR. EXISTENTES en el target pero que sufrieron alguna modificacion.
INSERT INTO dim.dim_productos
SELECT sp.id_empresa 
		,sp.id_producto  
		,sp.prd_codigo 
		,sp.prd_descripcion
		,sp.prd_tipo
		,sp.prd_clase
		,sp.prd_estado 
		,sp.prd_grupo 
		,sp.prd_seccion 
		,sp.prd_categoria 
		,sp.prd_unidad 
		,sp.prd_razon_social 
		,sp.prd_color 
		,sp.prd_checksum 
		,sp.prd_lastupdate 
		,sp.prd_updatedby 
		,CAST(getdate() AS DATE) EffectiveDate
		,'9999-12-31' EndDate
		,'Y' CurrentRecord 
FROM dim.dim_productos dp
JOIN stg.stg_productos sp
ON dp.id_empresa = sp.id_empresa
AND dp.id_producto = sp.id_producto 
AND dp.check_sum != sp.prd_checksum 
AND dp.registro_actual = 'Y';


--Registros a ACTUALIZAR. EXISTENTES en el target pero que sufrieron alguna modificacion.
UPDATE dim.dim_productos
SET
	dim.dim_productos.fecha_fin = getdate()-1, 
    dim.dim_productos.registro_actual = 'N', 
    dim.dim_productos.last_updated = getdate(), 
    dim.dim_productos.updated_by = suser_sname()
FROM dim.dim_productos dp
JOIN stg.stg_productos sp
ON dp.id_empresa = sp.id_empresa 
AND dp.id_producto = sp.id_producto 
AND dp.check_sum != sp.prd_checksum 
AND dp.registro_actual = 'Y';


UPDATE dim.audit_dimensionales
SET fin = GETDATE(), estado = 'F'
WHERE id_ejecucion = (SELECT MAX(id_ejecucion) FROM dim.audit_dimensionales WHERE tabla = 'dim_productos');
