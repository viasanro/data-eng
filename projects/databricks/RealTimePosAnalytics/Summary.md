# RealTimePosAnalytics Project Summary

## **Project Purpose**
Real-time Point of Sale (POS) analytics for retail inventory management using **Lakehouse architecture** with **Lambda + Medallion patterns** to calculate **Near Real-Time (NRT) inventory**.

## **Workflow Overview (Files 00-05)**

### **00_Setup_And_Config.py**
- **Purpose**: Database setup and configuration
- **Creates**: Bronze/Silver/Gold schemas
- **Tables**: No data tables, just schema preparation
- **Logic**: Centralized configuration management for the entire pipeline

### **01_Generate_Inputs_On_DBFS.py**
- **Purpose**: Synthetic data generation
- **Creates**: 
  - `rtpa_bronze.pos_events_stream` (POS transactions)
  - `rtpa_bronze.floor_snapshots_batch` (inventory snapshots)
  - `rtpa_bronze.starting_stock_seed` (initial inventory)
  - `rtpa_bronze.stores_seed` (store metadata)
  - `rtpa_bronze.products_seed` (product metadata)
- **Logic**: Simulates 30 days of retail operations with:
  - **Events**: Sales, restock, shrinkage, online orders, store pickups
  - **Snapshots**: Periodic floor inventory counts (every 24 hours)

### **02_Bronze_Ingest.py**
- **Purpose**: Data validation and quality checks
- **Processes**: Validates Bronze layer data
- **Tables**: Works with existing Bronze tables (no new tables)
- **Logic**: 
  - Checks for duplicate events/snapshots
  - Data quality validation
  - Optional data cleaning/deduplication

### **03_Silver_Transform.py**
- **Purpose**: Data normalization and transformation
- **Creates**:
  - `rtpa_silver.inventory_movements` (signed inventory movements)
  - `rtpa_silver.floor_snapshots` (cleaned snapshots)
- **Core Logic**:
  - **Movement calculation**: `restock = +qty`, `sale/shrink = -qty`
  - **Event normalization**: Converts raw POS events to standardized inventory movements
  - **Data cleaning**: Ensures consistent schema and data types

### **04_Gold_Inventory_Near_Real_Time.py**
- **Purpose**: NRT inventory calculation
- **Creates**: `rtpa_gold.inventory_nrt`
- **Core Calculations**:
  ```python
  # Movement-based inventory
  computed_qty = starting_qty + net_movement_qty
  
  # Best quantity logic
  best_qty = latest_snapshot_qty (if available) 
           OR computed_qty (if no snapshot)
  
  # As-of timestamp
  as_of_time = max(last_movement_time, latest_snapshot_time)
  ```
- **Logic**: Combines starting stock + cumulative movements + latest snapshots

### **05_Inventory_SQL_Examples.sql**
- **Purpose**: Sample queries and analytics
- **Tables**: Queries existing Gold/Silver/Bronze tables
- **Analytics Examples**:
  - Store-level inventory summaries
  - Top SKUs by availability
  - Movement vs snapshot comparisons
  - Temporal inventory trends

## **Data Flow Architecture**

```
Bronze Layer (Raw)
├── pos_events_stream → Silver: inventory_movements
└── floor_snapshots_batch → Silver: floor_snapshots

Silver Layer (Processed)
├── inventory_movements + starting_stock → Gold: computed_qty
└── floor_snapshots → Gold: latest_snapshot_qty

Gold Layer (Business Ready)
└── inventory_nrt (best_qty, as_of_time, computed_qty, latest_snapshot_qty)
```

## **Key Business Logic**

1. **Inventory Movement Tracking**: Every POS event affects inventory (+/-)
2. **Snapshot Corrections**: Periodic physical counts adjust computed inventory
3. **Best Quantity Logic**: Prioritizes actual snapshots over calculated values
4. **Temporal Accuracy**: Tracks "as-of" timestamps for NRT visibility

## **Final Output**
`rtpa_gold.inventory_nrt` provides **per-store, per-SKU** inventory with:
- **best_qty**: Most accurate inventory amount
- **computed_qty**: Movement-based calculation  
- **latest_snapshot_qty**: Last physical count
- **as_of_time**: Data freshness timestamp

This enables **real-time inventory visibility** for retail operations while maintaining data accuracy through periodic physical counts.
