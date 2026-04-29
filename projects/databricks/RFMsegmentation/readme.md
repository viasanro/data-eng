### RFM Segmentation
> Problematica<br>

En contextos de negocio con bases de clientes activas, tratar a todos los clientes de forma homogénea tiene un costo real:<br>
- presupuesto de marketing mal asignado
- acciones de retención aplicadas a clientes que ya se fueron
- y oportunidades de upsell perdidas en clientes de alto potencial que nunca fueron identificados como tales.<br>
El punto de partida fue una tabla transaccional sin ningún tipo de segmentación.<br> 
[dataset_de_kaggle](https://www.kaggle.com/datasets/luisrenterialezano/retail-sales-dataset?utm_source=chatgpt.com) <br>
Cada cliente era solo un customerId con compras asociadas. La pregunta concreta era: **¿cómo pasar de datos de transacciones crudos a un output accionable para el negocio?** <br><br>

> Solución propuesta<br>

Construir un pipeline reproducible, idempotente y capaz de actualizarse con cada nueva carga de datos sin regenerar todo el historial desde cero.<br>
El pipeline toma como input datos transaccionales con customerId, fecha de compra, cantidad, precios unitarios, y produce un dataset enriquecido, el output es una tabla plana, una fila por cliente, lista para consumo directo en herramientas de CRM, campañas de email o dashboards de retención.<br><br>

> Lógica de Segmentación<br>

```
    SI (R == 4) Y (F >= 3) Y (M >= 3)
    ENTONCES segmento = "Champions"

SINO SI (F == 4) Y (R >= 2) Y (M >= 2)
    ENTONCES segmento = "LoyalCustomers"

SINO SI (R >= 3) Y (F >= 2) Y (M >= 2)
    ENTONCES segmento = "PotentialLoyalists"

SINO SI (R == 4) Y (F == 1)
    ENTONCES segmento = "NewCustomers"

SINO SI (R <= 2) Y (F >= 3) Y (M >= 3)
    ENTONCES segmento = "AtRisk"

SINO
    segmento = "Hibernating"
```
<br>

> Por qué RFM y no otro metodo de segmentación?<br>

Existen múltiples enfoques para segmentar clientes.<br>
La ventaja central de RFM es que sus tres dimensiones tienen correlato directo con el comportamiento económico del cliente:<br>
- cuándo compró por última vez (urgencia de reactivación)
- con qué frecuencia lo hace (lealtad operativa)
- y cuánto dinero dejó (valor real para el negocio)<br>
**Ningún otro método genera esa información de forma tan limpia y accionable con solo datos transaccionales. Además:**<br>
- Interpretable sin conocimiento técnico.
- Cada segmento tiene acción de negocio directa.
- No requiere etiquetas ni datos de entrenamiento.
- Deterministico y reproducible.<br><br>

> Aprendizaje<br>

- Idempotencia y control de upserts.<br>
Se abordó la necesidad de actualizaciones reproducibles mediante la construcción de una clave primaria lógica determinística (hash sobre campos), combinada con una estrategia de MERGE (upsert) sobre la tabla de salida. Esto garantiza que cada ejecución del pipeline con los mismos datos de entrada produce exactamente el mismo resultado, sin duplicados ni inconsistencias entre cargas.<br>
- Enriquecimiento de métricas más allá del RFM base<br>
El output estándar de RFM se extendió con **ticket promedio** (monetary / frequency) y **unidades por ticket**. Esto permitió identificar patrones que el score RFM solo no captura: un cliente At Risk con bajo rfmClass puede tener un altísimo volumen por transacción, lo que cambia completamente la decisión de reactivación.
- Además algunas cuestiones interesantes sobre el uso de estadísticos como cuartiles y su utilización en la segmentación.
