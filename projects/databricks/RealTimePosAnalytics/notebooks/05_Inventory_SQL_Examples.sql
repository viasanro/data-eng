-- Databricks notebook source
-- Simple example queries over the RealTime POS Analytics model.

-- COMMAND ----------
-- Resumen de inventario por tienda (usando la mejor estimación por SKU)

SELECT
  store_id,
  COUNT(*) AS sku_count,
  SUM(best_qty)              AS total_units_best,
  SUM(computed_qty)          AS total_units_computed,
  SUM(latest_snapshot_qty)   AS total_units_snapshot
FROM rtpa_gold.inventory_nrt
GROUP BY store_id
ORDER BY store_id;

-- COMMAND ----------
-- Top 20 SKUs por unidades disponibles (best_qty) a nivel cadena

SELECT
  sku,
  SUM(best_qty) AS total_units_best
FROM rtpa_gold.inventory_nrt
GROUP BY sku
ORDER BY total_units_best DESC
LIMIT 20;

-- COMMAND ----------
-- Comparación entre inventario computado vs snapshot para una tienda concreta
-- (ajusta el store_id según tus datos)

SELECT
  store_id,
  sku,
  computed_qty,
  latest_snapshot_qty,
  best_qty,
  (computed_qty - latest_snapshot_qty) AS delta_computed_vs_snapshot,
  as_of_time,
  _updated_at
FROM rtpa_gold.inventory_nrt
WHERE store_id = 'S001'
ORDER BY ABS(computed_qty - latest_snapshot_qty) DESC
LIMIT 50;

-- COMMAND ----------
-- Evolución temporal del stock (agregado) por día usando movimientos Silver

SELECT
  event_date,
  store_id,
  SUM(movement_qty)        AS net_movement_qty,
  SUM(SUM(movement_qty)) OVER (
    PARTITION BY store_id
    ORDER BY event_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  )                        AS cumulative_movement_qty
FROM rtpa_silver.inventory_movements
GROUP BY store_id, event_date
ORDER BY store_id, event_date;

-- COMMAND ----------
-- Detalle de eventos de POS (Bronze) para un SKU específico
-- (útil para debugging / trazabilidad).

SELECT
  event_date,
  event_time,
  store_id,
  sku,
  event_type,
  qty,
  source,
  channel
FROM rtpa_bronze.pos_events_stream
WHERE sku = 'SKU00001'
ORDER BY event_time
LIMIT 200;

