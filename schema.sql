-- =====================================================================
-- Data Warehouse Schema: สหกรณ์การเกษตร (Agricultural Cooperative)
-- Amazon Redshift (columnar MPP).  Notes for the Redshift dialect:
--   * SERIAL -> IDENTITY(1,1); no CREATE INDEX (SORTKEY / DISTKEY instead)
--   * PRIMARY KEY / FOREIGN KEY are informational (the planner uses them, they are not enforced)
--   * VARCHAR(n) counts BYTES; Thai characters take 3 bytes, so lengths are 3x the logical size
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS data_warehouse;
SET search_path TO data_warehouse, public;

-- DIMENSION TABLES (small, replicated to every node: DISTSTYLE ALL)
-- dim_date  (SCD Type 0 - Insert Only, no updates)
CREATE TABLE IF NOT EXISTS dim_date (
    date_key        INTEGER PRIMARY KEY,
    date            DATE NOT NULL,
    day             INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    quarter         INTEGER NOT NULL,
    year            INTEGER NOT NULL,
    weekday         VARCHAR(45) NOT NULL
)
DISTSTYLE ALL
SORTKEY (date_key);

-- dim_crop  (SCD Type 1 - Overwrite)
CREATE TABLE IF NOT EXISTS dim_crop (
    crop_sk                 INTEGER IDENTITY(1,1) PRIMARY KEY,
    crop_id                 VARCHAR(60) NOT NULL,
    crop_name               VARCHAR(300) NOT NULL,
    category                VARCHAR(150),
    unit                    VARCHAR(60),
    standard_price_per_unit NUMERIC(12,2),
    season_months           VARCHAR(150),
    shelf_life_days         INTEGER
)
DISTSTYLE ALL;

-- dim_warehouse  (SCD Type 3 - keep current + previous value)
CREATE TABLE IF NOT EXISTS dim_warehouse (
    warehouse_sk             INTEGER IDENTITY(1,1) PRIMARY KEY,
    warehouse_id             VARCHAR(60) NOT NULL,
    previous_warehouse_name  VARCHAR(450),
    current_warehouse_name   VARCHAR(450) NOT NULL,
    province                 VARCHAR(300),
    region                   VARCHAR(300),
    capacity_ton             INTEGER,
    manager_name             VARCHAR(450)
)
DISTSTYLE ALL;

-- dim_farmer  (SCD Type 2 - track history)
CREATE TABLE IF NOT EXISTS dim_farmer (
    farmer_sk       INTEGER IDENTITY(1,1) PRIMARY KEY,
    farmer_id       VARCHAR(60) NOT NULL,
    farmer_name     VARCHAR(450) NOT NULL,
    province        VARCHAR(300),
    region          VARCHAR(300),
    cooperative     VARCHAR(450),
    farm_size_rai   NUMERIC(10,2),
    primary_crop    VARCHAR(300),
    valid_from      DATE NOT NULL,
    valid_to        DATE NOT NULL DEFAULT '9999-12-31',
    is_current      BOOLEAN NOT NULL DEFAULT TRUE
)
DISTSTYLE ALL;

-- dim_customer  (SCD Type 2 - track history)
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_sk       INTEGER IDENTITY(1,1) PRIMARY KEY,
    customer_id       VARCHAR(60) NOT NULL,
    customer_name     VARCHAR(450) NOT NULL,
    customer_type     VARCHAR(150),
    province          VARCHAR(300),
    region            VARCHAR(300),
    credit_limit_thb  NUMERIC(14,2),
    valid_from        DATE NOT NULL,
    valid_to          DATE NOT NULL DEFAULT '9999-12-31',
    is_current        BOOLEAN NOT NULL DEFAULT TRUE
)
DISTSTYLE ALL;

-- FACT TABLES (distributed by crop_sk so joins with dim_crop stay local, sorted by date)
-- fact_harvest  (grain: 1 row = 1 รายการรับซื้อ)
CREATE TABLE IF NOT EXISTS fact_harvest (
    harvest_id         VARCHAR(60) PRIMARY KEY,
    harvest_date_key   INTEGER NOT NULL REFERENCES dim_date(date_key),
    farmer_sk          INTEGER NOT NULL REFERENCES dim_farmer(farmer_sk),
    crop_sk            INTEGER NOT NULL REFERENCES dim_crop(crop_sk),
    warehouse_sk       INTEGER NOT NULL REFERENCES dim_warehouse(warehouse_sk),
    quantity_kg        NUMERIC(14,2) NOT NULL,
    price_per_kg       NUMERIC(12,2) NOT NULL,
    total_amount_thb   NUMERIC(16,2) NOT NULL,
    quality_grade      VARCHAR(15)
)
DISTSTYLE KEY DISTKEY (crop_sk)
SORTKEY (harvest_date_key);

-- fact_sales  (grain: 1 row = 1 รายการขาย)
CREATE TABLE IF NOT EXISTS fact_sales (
    sales_id          VARCHAR(60) PRIMARY KEY,
    sale_date_key     INTEGER NOT NULL REFERENCES dim_date(date_key),
    customer_sk       INTEGER NOT NULL REFERENCES dim_customer(customer_sk),
    crop_sk           INTEGER NOT NULL REFERENCES dim_crop(crop_sk),
    warehouse_sk      INTEGER NOT NULL REFERENCES dim_warehouse(warehouse_sk),
    quantity_kg       NUMERIC(14,2) NOT NULL,
    unit_price_thb    NUMERIC(12,2) NOT NULL,
    total_amount_thb  NUMERIC(16,2) NOT NULL,
    discount_pct      NUMERIC(5,2),
    sale_channel      VARCHAR(150)
)
DISTSTYLE KEY DISTKEY (crop_sk)
SORTKEY (sale_date_key);

-- fact_shipment  (grain: 1 row = 1 รอบการจัดส่ง)
CREATE TABLE IF NOT EXISTS fact_shipment (
    shipment_id         VARCHAR(60) PRIMARY KEY,
    shipment_date_key   INTEGER NOT NULL REFERENCES dim_date(date_key),
    delivery_date_key   INTEGER NOT NULL REFERENCES dim_date(date_key),
    customer_sk         INTEGER NOT NULL REFERENCES dim_customer(customer_sk),
    crop_sk             INTEGER NOT NULL REFERENCES dim_crop(crop_sk),
    warehouse_sk        INTEGER NOT NULL REFERENCES dim_warehouse(warehouse_sk),
    total_weight_kg     NUMERIC(14,2) NOT NULL,
    shipping_cost_thb   NUMERIC(14,2),
    status              VARCHAR(150),
    transport_mode      VARCHAR(150)
)
DISTSTYLE KEY DISTKEY (crop_sk)
SORTKEY (shipment_date_key);

-- fact_inventory  (grain: 1 row = 1 บันทึกยอดคงเหลือต่อคลัง)
CREATE TABLE IF NOT EXISTS fact_inventory (
    inventory_id        VARCHAR(60) PRIMARY KEY,
    snapshot_date_key   INTEGER NOT NULL REFERENCES dim_date(date_key),
    warehouse_sk        INTEGER NOT NULL REFERENCES dim_warehouse(warehouse_sk),
    crop_sk             INTEGER NOT NULL REFERENCES dim_crop(crop_sk),
    beginning_stock_kg  NUMERIC(14,2) NOT NULL,
    received_kg         NUMERIC(14,2) NOT NULL,
    sold_kg             NUMERIC(14,2) NOT NULL,
    ending_stock_kg     NUMERIC(14,2) NOT NULL,
    unit_cost_thb       NUMERIC(12,2)
)
DISTSTYLE KEY DISTKEY (crop_sk)
SORTKEY (snapshot_date_key)
