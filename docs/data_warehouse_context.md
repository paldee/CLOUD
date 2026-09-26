# AI Schema Context: Agricultural Cooperative Data Warehouse

เอกสารนี้เป็น schema context สำหรับระบบ Text-to-SQL โดยสกัดจาก `รายละเอียดระบบ.pdf`
ส่วน Data Warehouse Design, Data Dictionary และ ETL Mapping (หน้า 14-37) และตรวจชื่อ
คอลัมน์ต้นทางเทียบกับไฟล์ CSV ทั้ง 8 ชุดใน `dataset/`

> สถานะความน่าเชื่อถือ: เป็น schema ที่ได้จากเอกสารออกแบบ ยังไม่ใช่ DDL จาก Amazon RDS
> เมื่อมี `schema.sql` หรือเข้าถึง RDS จริง ให้ถือ DDL ที่ deploy แล้วเป็น source of truth และ
> ปรับทั้งเอกสารนี้กับ `app/db/schema_catalog.py` ให้ตรงกัน

## Database scope

- Engine/dialect: PostgreSQL บน Amazon RDS
- Schema: `data_warehouse`
- Model: Star Schema
- Fact tables: `fact_harvest`, `fact_sales`, `fact_shipment`, `fact_inventory`
- Dimension tables: `dim_date`, `dim_crop`, `dim_warehouse`, `dim_farmer`, `dim_customer`
- Date key format: `YYYYMMDD` เช่น `20250428`
- Query policy: read-only และใช้เฉพาะตาราง/คอลัมน์ในเอกสารนี้

## Relationships

```text
dim_date.date_key       <- fact_harvest.harvest_date_key
dim_farmer.farmer_sk    <- fact_harvest.farmer_sk
dim_crop.crop_sk        <- fact_harvest.crop_sk
dim_warehouse.warehouse_sk <- fact_harvest.warehouse_sk

dim_date.date_key       <- fact_sales.sale_date_key
dim_customer.customer_sk <- fact_sales.customer_sk
dim_crop.crop_sk        <- fact_sales.crop_sk
dim_warehouse.warehouse_sk <- fact_sales.warehouse_sk

dim_date.date_key       <- fact_shipment.shipment_date_key
dim_date.date_key       <- fact_shipment.delivery_date_key
dim_customer.customer_sk <- fact_shipment.customer_sk
dim_crop.crop_sk        <- fact_shipment.crop_sk
dim_warehouse.warehouse_sk <- fact_shipment.warehouse_sk

dim_date.date_key       <- fact_inventory.snapshot_date_key
dim_crop.crop_sk        <- fact_inventory.crop_sk
dim_warehouse.warehouse_sk <- fact_inventory.warehouse_sk
```

## Dimension tables

### `data_warehouse.dim_date`

Purpose: ปฏิทินเวลามาตรฐานสำหรับเชื่อมวันที่ของทุก business process

- Grain: 1 แถว = 1 วัน
- Primary key: `date_key`
- SCD: Type 0, static / insert only
- Source: สร้างจากวันที่ในไฟล์ธุรกรรม

| Column | Type | Meaning |
| --- | --- | --- |
| `date_key` | INTEGER | คีย์วันที่รูปแบบ `YYYYMMDD` |
| `date` | DATE | วันที่เต็มรูปแบบ `YYYY-MM-DD` |
| `day` | INTEGER | วันในเดือน |
| `month` | INTEGER | เดือน 1-12 |
| `quarter` | INTEGER | ไตรมาส 1-4 |
| `year` | INTEGER | ปี ค.ศ. |
| `weekday` | VARCHAR | ชื่อวันในสัปดาห์ |

Rules:

- สร้าง `date_key` จากวันที่ธุรกรรมในรูปแบบ `YYYYMMDD`
- โหลดแบบ insert-only และไม่แก้ไขข้อมูลย้อนหลัง
- `delivery_date_key = 99991231` ใช้แทน shipment ที่ยังไม่มีวันส่งมอบ

### `data_warehouse.dim_crop`

Purpose: ข้อมูลมิติผลผลิตทางการเกษตร

- Grain: 1 แถว = 1 ผลผลิตจากระบบต้นทาง
- Primary key: `crop_sk` (surrogate key)
- Business key: `crop_id`
- SCD: Type 1, overwrite
- Source: `Crop.csv`

| Column | Type | Meaning |
| --- | --- | --- |
| `crop_sk` | INTEGER | Surrogate key ของผลผลิต |
| `crop_id` | VARCHAR | รหัสผลผลิตจากระบบต้นทาง |
| `crop_name` | VARCHAR | ชื่อผลผลิต |
| `category` | VARCHAR | หมวดหมู่ผลผลิต |
| `unit` | VARCHAR | หน่วยบรรจุภัณฑ์ |
| `standard_price_per_unit` | NUMERIC | ราคามาตรฐานอ้างอิงต่อหน่วย |
| `season_months` | VARCHAR | เดือนที่เป็นฤดูกาลเก็บเกี่ยว |
| `shelf_life_days` | INTEGER | อายุการเก็บรักษาสูงสุดเป็นวัน |

Rules:

- สร้าง `crop_sk` อัตโนมัติ
- Trim `crop_name`
- `standard_price_per_unit` ต้องไม่ติดลบ และแทน NULL ด้วย `0.00`
- เมื่อข้อมูลเปลี่ยนให้เขียนทับแถวเดิมตาม SCD Type 1

### `data_warehouse.dim_warehouse`

Purpose: ข้อมูลมิติคลังสินค้าและไซโลแบบเก็บชื่อก่อนหน้า 1 ค่า

- Grain: 1 แถว = 1 คลังสินค้าจากระบบต้นทาง
- Primary key: `warehouse_sk` (surrogate key)
- Business key: `warehouse_id`
- SCD: Type 3, current and previous value
- Source: `Warehouse.csv`

| Column | Type | Meaning |
| --- | --- | --- |
| `warehouse_sk` | INTEGER | Surrogate key ของคลังสินค้า |
| `warehouse_id` | VARCHAR | รหัสคลังสินค้าจากระบบต้นทาง |
| `previous_warehouse_name` | VARCHAR | ชื่อคลังสินค้าก่อนหน้า |
| `current_warehouse_name` | VARCHAR | ชื่อคลังสินค้าปัจจุบัน |
| `province` | VARCHAR | จังหวัดที่ตั้งคลังสินค้า |
| `region` | VARCHAR | ภูมิภาค |
| `capacity_ton` | INTEGER | ความจุสูงสุดของคลังเป็นตัน |
| `manager_name` | VARCHAR | ชื่อผู้จัดการคลังสินค้า |

Rules:

- สร้าง `warehouse_sk` อัตโนมัติ
- เมื่อชื่อคลังเปลี่ยน ให้ย้ายชื่อเดิมไป `previous_warehouse_name` และเก็บชื่อใหม่ใน `current_warehouse_name`
- `capacity_ton` ต้องไม่เป็น NULL และต้องไม่ติดลบ
- Trim `manager_name`

### `data_warehouse.dim_farmer`

Purpose: ข้อมูลมิติเกษตรกรแบบเก็บประวัติการเปลี่ยนแปลง

- Grain: 1 แถว = 1 เวอร์ชันของเกษตรกรในช่วง `valid_from` ถึง `valid_to`
- Primary key: `farmer_sk` (surrogate key)
- Business key: `farmer_id`
- SCD: Type 2, full history
- Source: `Farmer.csv`

| Column | Type | Meaning |
| --- | --- | --- |
| `farmer_sk` | INTEGER | Surrogate key ของเวอร์ชันเกษตรกร |
| `farmer_id` | VARCHAR | รหัสเกษตรกรจากระบบต้นทาง |
| `farmer_name` | VARCHAR | ชื่อและนามสกุลเกษตรกร |
| `province` | VARCHAR | จังหวัดภูมิลำเนา |
| `region` | VARCHAR | ภูมิภาค |
| `cooperative` | VARCHAR | สหกรณ์ต้นสังกัด |
| `farm_size_rai` | NUMERIC | ขนาดพื้นที่เพาะปลูกเป็นไร่ |
| `primary_crop` | VARCHAR | ผลผลิตหลักที่เพาะปลูก |
| `valid_from` | DATE | วันที่เริ่มใช้ข้อมูลเวอร์ชันนี้ |
| `valid_to` | DATE | วันที่สิ้นสุดการใช้ข้อมูลเวอร์ชันนี้ |
| `is_current` | BOOLEAN | ระบุว่าเป็นเวอร์ชันปัจจุบันหรือไม่ |

Rules:

- สร้าง `farmer_sk` อัตโนมัติ และ Trim `farmer_name`
- `farm_size_rai` ต้องไม่เป็น NULL
- แถวใหม่ใช้ `valid_from` เป็นวันที่รัน, `valid_to = 9999-12-31`, `is_current = true`
- เมื่อข้อมูลเปลี่ยนให้ปิดเวอร์ชันเดิมและสร้างแถวใหม่ตาม SCD Type 2
- เวลา lookup fact ให้เลือกเวอร์ชันที่มีผล ณ วันที่ธุรกรรม ไม่ใช้ `is_current = true` อย่างเดียวสำหรับข้อมูลย้อนหลัง

### `data_warehouse.dim_customer`

Purpose: ข้อมูลมิติลูกค้าและคู่ค้าแบบเก็บประวัติการเปลี่ยนแปลง

- Grain: 1 แถว = 1 เวอร์ชันของลูกค้าในช่วง `valid_from` ถึง `valid_to`
- Primary key: `customer_sk` (surrogate key)
- Business key: `customer_id`
- SCD: Type 2, full history
- Source: `Customer.csv`

| Column | Type | Meaning |
| --- | --- | --- |
| `customer_sk` | INTEGER | Surrogate key ของเวอร์ชันลูกค้า |
| `customer_id` | VARCHAR | รหัสลูกค้าจากระบบต้นทาง |
| `customer_name` | VARCHAR | ชื่อบริษัทหรือชื่อลูกค้า |
| `customer_type` | VARCHAR | ประเภทลูกค้า |
| `province` | VARCHAR | จังหวัดที่ตั้งลูกค้า |
| `region` | VARCHAR | ภูมิภาค |
| `credit_limit_thb` | NUMERIC | วงเงินเครดิตที่อนุมัติเป็นบาท |
| `valid_from` | DATE | วันที่เริ่มใช้ข้อมูลเวอร์ชันนี้ |
| `valid_to` | DATE | วันที่สิ้นสุดการใช้ข้อมูลเวอร์ชันนี้ |
| `is_current` | BOOLEAN | ระบุว่าเป็นเวอร์ชันปัจจุบันหรือไม่ |

Rules:

- สร้าง `customer_sk` อัตโนมัติ และ Trim `customer_name`
- แทน `credit_limit_thb` ที่เป็น NULL ด้วย `0.00`
- แถวใหม่ใช้ `valid_from` เป็นวันที่รัน, `valid_to = 9999-12-31`, `is_current = true`
- เมื่อข้อมูลเปลี่ยนให้ปิดเวอร์ชันเดิมและสร้างแถวใหม่ตาม SCD Type 2

## Fact tables

### `data_warehouse.fact_harvest`

Purpose: รายการรับซื้อผลผลิตจากเกษตรกรเข้าคลัง

- Grain: 1 แถว = 1 รายการรับซื้อผลผลิต
- Primary key: `harvest_id`
- Source: `Harvest.csv`

| Column | Type | Key / Meaning |
| --- | --- | --- |
| `harvest_id` | VARCHAR | PK, รหัสรายการรับซื้อ |
| `harvest_date_key` | INTEGER | FK -> `dim_date.date_key` |
| `farmer_sk` | INTEGER | FK -> `dim_farmer.farmer_sk` |
| `crop_sk` | INTEGER | FK -> `dim_crop.crop_sk` |
| `warehouse_sk` | INTEGER | FK -> `dim_warehouse.warehouse_sk` |
| `quantity_kg` | NUMERIC | ปริมาณที่รับซื้อเป็นกิโลกรัม |
| `price_per_kg` | NUMERIC | ราคารับซื้อต่อกิโลกรัม |
| `total_amount_thb` | NUMERIC | ยอดเงินที่จ่ายให้เกษตรกร |
| `quality_grade` | VARCHAR | เกรดคุณภาพ A, B หรือ C |

Rules:

- แปลง `harvest_date` เป็น `harvest_date_key` รูปแบบ `YYYYMMDD`
- Lookup `farmer_sk` จากเวอร์ชันที่มีผล ณ วันที่รับซื้อ
- `quantity_kg` และ `price_per_kg` ต้องไม่เป็น NULL และต้องไม่ติดลบ
- ตรวจสอบ `total_amount_thb` เทียบกับ `quantity_kg * price_per_kg`

### `data_warehouse.fact_sales`

Purpose: รายการขายผลผลิตให้ลูกค้าหรือคู่ค้า

- Grain: 1 แถว = 1 รายการขาย
- Primary key: `sales_id`
- Source: `Sales.csv`

| Column | Type | Key / Meaning |
| --- | --- | --- |
| `sales_id` | VARCHAR | PK, รหัสรายการขาย |
| `sale_date_key` | INTEGER | FK -> `dim_date.date_key` |
| `customer_sk` | INTEGER | FK -> `dim_customer.customer_sk` |
| `crop_sk` | INTEGER | FK -> `dim_crop.crop_sk` |
| `warehouse_sk` | INTEGER | FK -> `dim_warehouse.warehouse_sk` |
| `quantity_kg` | NUMERIC | ปริมาณที่ขายเป็นกิโลกรัม |
| `unit_price_thb` | NUMERIC | ราคาขายต่อหน่วย |
| `total_amount_thb` | NUMERIC | ยอดขายรวมก่อนหักส่วนลด |
| `discount_pct` | NUMERIC | เปอร์เซ็นต์ส่วนลด |
| `sale_channel` | VARCHAR | ช่องทางการขาย |

Rules:

- แปลง `sale_date` เป็น `sale_date_key` รูปแบบ `YYYYMMDD`
- Lookup `customer_sk` โดยให้วันขายอยู่ในช่วง `valid_from` ถึง `valid_to`
- `quantity_kg` และ `unit_price_thb` ต้องไม่ติดลบ
- แทน `discount_pct` ที่เป็น NULL ด้วย `0`
- ยอดขายสุทธิ: `total_amount_thb * (1 - COALESCE(discount_pct, 0) / 100.0)`

### `data_warehouse.fact_shipment`

Purpose: รายการจัดส่งผลผลิตจากคลังไปยังลูกค้า

- Grain: 1 แถว = 1 รอบการจัดส่ง
- Primary key: `shipment_id`
- Source: `Shipment.csv`

| Column | Type | Key / Meaning |
| --- | --- | --- |
| `shipment_id` | VARCHAR | PK, รหัสรายการจัดส่ง |
| `shipment_date_key` | INTEGER | FK -> `dim_date.date_key` |
| `delivery_date_key` | INTEGER | FK -> `dim_date.date_key` |
| `customer_sk` | INTEGER | FK -> `dim_customer.customer_sk` |
| `crop_sk` | INTEGER | FK -> `dim_crop.crop_sk` |
| `warehouse_sk` | INTEGER | FK -> `dim_warehouse.warehouse_sk` |
| `total_weight_kg` | NUMERIC | น้ำหนักรวมที่จัดส่งเป็นกิโลกรัม |
| `shipping_cost_thb` | NUMERIC | ค่าใช้จ่ายในการจัดส่ง |
| `status` | VARCHAR | สถานะการจัดส่ง |
| `transport_mode` | VARCHAR | รูปแบบการขนส่ง |

Rules:

- แปลง `shipment_date` เป็น `shipment_date_key` รูปแบบ `YYYYMMDD`
- ถ้า `delivery_date` เป็น NULL ให้ใช้ `delivery_date_key = 99991231`; มิฉะนั้นแปลงเป็น `YYYYMMDD`
- `delivery_date` ต้องไม่เกิดก่อน `shipment_date`
- `total_weight_kg` และ `shipping_cost_thb` ต้องไม่ติดลบ

### `data_warehouse.fact_inventory`

Purpose: บันทึกสถานะสินค้าคงคลังรายรอบ

- Grain: 1 แถว = 1 inventory snapshot ต่อคลังและผลผลิต
- Primary key: `inventory_id`
- Source: `Inventory.csv`

| Column | Type | Key / Meaning |
| --- | --- | --- |
| `inventory_id` | VARCHAR | PK, รหัสบันทึกคลังสินค้า |
| `snapshot_date_key` | INTEGER | FK -> `dim_date.date_key` |
| `warehouse_sk` | INTEGER | FK -> `dim_warehouse.warehouse_sk` |
| `crop_sk` | INTEGER | FK -> `dim_crop.crop_sk` |
| `beginning_stock_kg` | NUMERIC | ยอดสต็อกยกมาต้นรอบ |
| `received_kg` | NUMERIC | ปริมาณที่รับเข้าคลัง |
| `sold_kg` | NUMERIC | ปริมาณที่เบิกหรือขายออก |
| `ending_stock_kg` | NUMERIC | ยอดสต็อกคงเหลือสิ้นรอบ |
| `unit_cost_thb` | NUMERIC | ต้นทุนเฉลี่ยต่อหน่วย |

Rules:

- แปลง `snapshot_date` เป็น `snapshot_date_key` รูปแบบ `YYYYMMDD`
- `beginning_stock_kg` และ `ending_stock_kg` ต้องไม่ติดลบ
- แทน `received_kg` และ `sold_kg` ที่เป็น NULL ด้วย `0`
- `unit_cost_thb` ต้องไม่เป็น NULL และต้องไม่ติดลบ

## Business metrics

| Metric | Definition |
| --- | --- |
| Total Harvest Amount | `SUM(fact_harvest.total_amount_thb)` |
| Total Quantity Harvested | `SUM(fact_harvest.quantity_kg)` |
| Average Price per Kg | `AVG(fact_harvest.price_per_kg)` |
| Gross Sales Amount | `SUM(fact_sales.total_amount_thb)` |
| Net Sales Amount | `SUM(total_amount_thb * (1 - COALESCE(discount_pct, 0) / 100.0))` |
| Total Quantity Sold | `SUM(fact_sales.quantity_kg)` |
| Total Shipping Cost | `SUM(fact_shipment.shipping_cost_thb)` |
| Total Ending Stock | `SUM(fact_inventory.ending_stock_kg)` โดยควรเลือก snapshot ที่ต้องการก่อน aggregate |

## Source-only columns excluded from AI SQL

คอลัมน์ต่อไปนี้มีอยู่ใน CSV แต่ไม่อยู่ใน Data Warehouse target dictionary จึงห้าม Text-to-SQL
นำไปใช้จนกว่า DDL จริงจะยืนยันว่ามีอยู่ใน RDS

| Source | Excluded columns |
| --- | --- |
| `Crop.csv` | `is_active` |
| `Warehouse.csv` | `address`, `current_utilization_pct`, `contact_phone`, `is_active` |
| `Farmer.csv` | `national_id`, `district`, `registration_date`, `status`, `phone` |
| `Customer.csv` | `contact_person`, `phone`, `email`, `is_active` |
| `Harvest.csv` | `inspector_note` |
| `Sales.csv` | `order_id`, `payment_status` |
| `Shipment.csv` | `driver_name`, `vehicle_plate` |
| `Inventory.csv` | `stock_status` |

PII ที่ตั้งใจไม่ expose ให้ SQL generation ได้แก่ `national_id`, `phone`, `email` และ
`contact_person` การไม่มีคอลัมน์เหล่านี้ใน allowlist เป็น guardrail ชั้นแรก และ database user
สำหรับ Agent ควรมีสิทธิ์ read-only เป็น guardrail อีกชั้นหนึ่ง

## Documentation decisions and open verification

- ใช้ `current_warehouse_name` และ `previous_warehouse_name` ตาม Data Dictionary และ ETL Mapping ของ `dim_warehouse`; ไม่ใช้ `warehouse_name` จากตารางสรุประดับสูง
- ใช้ `province` ใน `dim_farmer` และ `dim_customer` เพราะมีระบุใน Data Dictionary แม้รายการ mapping จะวางต่อเนื่องข้ามหน้า
- `dim_date` มี `day` และ `weekday` ตาม Data Dictionary แม้ ETL Mapping ฉบับย่อจะไม่ได้แจกแจงสองคอลัมน์นี้
- `stock_status` เป็น source-only เพราะไม่ปรากฏใน target `fact_inventory`
- ต้องตรวจชื่อ schema, constraints, nullability, precision/scale, indexes และค่า sentinel `99991231` อีกครั้งกับ DDL/RDS จริง

## Verify against deployed RDS

ตัวตรวจจะอ่าน `information_schema` เท่านั้น และเปรียบเทียบ table, column, data type, primary key
และ foreign key กับ `app/db/schema_catalog.py` โดยไม่แก้ไขฐานข้อมูล

1. ตั้งค่า `DATABASE_URL` และ `DATABASE_SCHEMA` ใน `.env`
2. ใช้ database user ที่มีสิทธิ์ read-only
3. รันคำสั่ง:

```powershell
& '.\.venv\Scripts\python.exe' 'scripts\verify_rds_schema.py'
```

Exit code `0` หมายถึง schema ตรงกัน, `1` หมายถึงพบ schema drift และ `2` หมายถึงยังไม่ได้ตั้งค่า
`DATABASE_URL`
