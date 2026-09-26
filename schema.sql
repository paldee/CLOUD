-- =====================================================================
-- Data Warehouse Schema: สหกรณ์การเกษตร (Agricultural Cooperative)
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS data_warehouse;
SET search_path TO data_warehouse, public;

-- DIMENSION TABLES
-- dim_date  (SCD Type 0 - Insert Only, no updates)
CREATE TABLE IF NOT EXISTS dim_date (
    date_key        INTEGER PRIMARY KEY,
    date            DATE NOT NULL,
    day             INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    quarter         INTEGER NOT NULL,
    year            INTEGER NOT NULL,
    weekday         VARCHAR(15) NOT NULL
);

-- dim_crop  (SCD Type 1 - Overwrite)
CREATE TABLE IF NOT EXISTS dim_crop (
    crop_sk                 SERIAL PRIMARY KEY,
    crop_id                 VARCHAR(20) NOT NULL,
    crop_name               VARCHAR(100) NOT NULL,
    category                VARCHAR(50),
    unit                    VARCHAR(20),
    standard_price_per_unit NUMERIC(12,2),
    season_months           VARCHAR(50),
    shelf_life_days         INTEGER
);

-- dim_warehouse  (SCD Type 3 - keep current + previous value)
CREATE TABLE IF NOT EXISTS dim_warehouse (
    warehouse_sk             SERIAL PRIMARY KEY,
    warehouse_id             VARCHAR(20) NOT NULL,
    previous_warehouse_name  VARCHAR(150),
    current_warehouse_name   VARCHAR(150) NOT NULL,
    province                 VARCHAR(100),
    region                   VARCHAR(100),
    capacity_ton             INTEGER,
    manager_name             VARCHAR(150)
);

-- dim_farmer  (SCD Type 2 - track history)
CREATE TABLE IF NOT EXISTS dim_farmer (
    farmer_sk       SERIAL PRIMARY KEY,
    farmer_id       VARCHAR(20) NOT NULL,
    farmer_name     VARCHAR(150) NOT NULL,
    province        VARCHAR(100),
    region          VARCHAR(100),
    cooperative     VARCHAR(150),
    farm_size_rai   NUMERIC(10,2),
    primary_crop    VARCHAR(100),
    valid_from      DATE NOT NULL,
    valid_to        DATE NOT NULL DEFAULT '9999-12-31',
    is_current      BOOLEAN NOT NULL DEFAULT TRUE
);

-- dim_customer  (SCD Type 2 - track history)
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_sk       SERIAL PRIMARY KEY,
    customer_id       VARCHAR(20) NOT NULL,
    customer_name     VARCHAR(150) NOT NULL,
    customer_type     VARCHAR(50),
    province          VARCHAR(100),
    region            VARCHAR(100),
    credit_limit_thb  NUMERIC(14,2),
    valid_from        DATE NOT NULL,
    valid_to          DATE NOT NULL DEFAULT '9999-12-31',
    is_current      BOOLEAN NOT NULL DEFAULT TRUE
);

-- FACT TABLES
-- fact_harvest  (grain: 1 row = 1 รายการรับซื้อ)
CREATE TABLE IF NOT EXISTS fact_harvest (
    harvest_id         VARCHAR(20) PRIMARY KEY,
    harvest_date_key   INTEGER NOT NULL REFERENCES dim_date(date_key),
    farmer_sk          INTEGER NOT NULL REFERENCES dim_farmer(farmer_sk),
    crop_sk            INTEGER NOT NULL REFERENCES dim_crop(crop_sk),
    warehouse_sk       INTEGER NOT NULL REFERENCES dim_warehouse(warehouse_sk),
    quantity_kg        NUMERIC(14,2) NOT NULL,
    price_per_kg       NUMERIC(12,2) NOT NULL,
    total_amount_thb   NUMERIC(16,2) NOT NULL,
    quality_grade      VARCHAR(5)
);

-- fact_sales  (grain: 1 row = 1 รายการขาย)
CREATE TABLE IF NOT EXISTS fact_sales (
    sales_id          VARCHAR(20) PRIMARY KEY,
    sale_date_key     INTEGER NOT NULL REFERENCES dim_date(date_key),
    customer_sk       INTEGER NOT NULL REFERENCES dim_customer(customer_sk),
    crop_sk           INTEGER NOT NULL REFERENCES dim_crop(crop_sk),
    warehouse_sk      INTEGER NOT NULL REFERENCES dim_warehouse(warehouse_sk),
    quantity_kg       NUMERIC(14,2) NOT NULL,
    unit_price_thb    NUMERIC(12,2) NOT NULL,
    total_amount_thb  NUMERIC(16,2) NOT NULL,
    discount_pct      NUMERIC(5,2),
    sale_channel      VARCHAR(50)
);

-- fact_shipment  (grain: 1 row = 1 รอบการจัดส่ง)
CREATE TABLE IF NOT EXISTS fact_shipment (
    shipment_id         VARCHAR(20) PRIMARY KEY,
    shipment_date_key   INTEGER NOT NULL REFERENCES dim_date(date_key),
    delivery_date_key   INTEGER NOT NULL REFERENCES dim_date(date_key),
    customer_sk         INTEGER NOT NULL REFERENCES dim_customer(customer_sk),
    crop_sk             INTEGER NOT NULL REFERENCES dim_crop(crop_sk),
    warehouse_sk        INTEGER NOT NULL REFERENCES dim_warehouse(warehouse_sk),
    total_weight_kg     NUMERIC(14,2) NOT NULL,
    shipping_cost_thb   NUMERIC(14,2),
    status              VARCHAR(50),
    transport_mode      VARCHAR(50)
);

-- fact_inventory  (grain: 1 row = 1 บันทึกยอดคงเหลือต่อคลัง)
CREATE TABLE IF NOT EXISTS fact_inventory (
    inventory_id       VARCHAR(20) PRIMARY KEY,
    snapshot_date_key  INTEGER NOT NULL REFERENCES dim_date(date_key),
    warehouse_sk       INTEGER NOT NULL REFERENCES dim_warehouse(warehouse_sk),
    crop_sk            INTEGER NOT NULL REFERENCES dim_crop(crop_sk),
    beginning_stock_kg NUMERIC(14,2) NOT NULL,
    received_kg        NUMERIC(14,2) NOT NULL,
    sold_kg             NUMERIC(14,2) NOT NULL,
    ending_stock_kg     NUMERIC(14,2) NOT NULL,
    unit_cost_thb       NUMERIC(12,2)
);

-- INDEXES (recommended for OLAP query performance)
CREATE INDEX IF NOT EXISTS idx_fact_harvest_date       ON fact_harvest(harvest_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_harvest_farmer     ON fact_harvest(farmer_sk);
CREATE INDEX IF NOT EXISTS idx_fact_harvest_crop       ON fact_harvest(crop_sk);
CREATE INDEX IF NOT EXISTS idx_fact_harvest_warehouse  ON fact_harvest(warehouse_sk);

CREATE INDEX IF NOT EXISTS idx_fact_sales_date         ON fact_sales(sale_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_customer     ON fact_sales(customer_sk);
CREATE INDEX IF NOT EXISTS idx_fact_sales_crop         ON fact_sales(crop_sk);
CREATE INDEX IF NOT EXISTS idx_fact_sales_warehouse    ON fact_sales(warehouse_sk);

CREATE INDEX IF NOT EXISTS idx_fact_shipment_shipdate  ON fact_shipment(shipment_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_shipment_delivdate ON fact_shipment(delivery_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_shipment_customer  ON fact_shipment(customer_sk);
CREATE INDEX IF NOT EXISTS idx_fact_shipment_crop      ON fact_shipment(crop_sk);
CREATE INDEX IF NOT EXISTS idx_fact_shipment_warehouse ON fact_shipment(warehouse_sk);

CREATE INDEX IF NOT EXISTS idx_fact_inventory_date       ON fact_inventory(snapshot_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_inventory_warehouse  ON fact_inventory(warehouse_sk);
CREATE INDEX IF NOT EXISTS idx_fact_inventory_crop       ON fact_inventory(crop_sk);

CREATE INDEX IF NOT EXISTS idx_dim_farmer_current    ON dim_farmer(farmer_id, is_current);
CREATE INDEX IF NOT EXISTS idx_dim_customer_current  ON dim_customer(customer_id, is_current);
