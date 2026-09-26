DATA_WAREHOUSE_SCHEMA = {
    "fact_harvest": {
        "description": "รายการรับซื้อผลผลิตจากเกษตรกรเข้าคลัง",
        "columns": [
            "harvest_id",
            "harvest_date_key",
            "farmer_sk",
            "crop_sk",
            "warehouse_sk",
            "quantity_kg",
            "price_per_kg",
            "total_amount_thb",
            "quality_grade",
        ],
        "metrics": ["total_amount_thb", "quantity_kg", "price_per_kg"],
    },
    "fact_sales": {
        "description": "รายการขายผลผลิตให้ลูกค้า",
        "columns": [
            "sales_id",
            "sale_date_key",
            "customer_sk",
            "crop_sk",
            "warehouse_sk",
            "quantity_kg",
            "unit_price_thb",
            "total_amount_thb",
            "discount_pct",
            "sale_channel",
        ],
        "metrics": ["total_amount_thb", "quantity_kg", "discount_pct"],
    },
    "fact_shipment": {
        "description": "รายการจัดส่งสินค้าไปยังลูกค้า",
        "columns": [
            "shipment_id",
            "shipment_date_key",
            "delivery_date_key",
            "customer_sk",
            "crop_sk",
            "warehouse_sk",
            "total_weight_kg",
            "shipping_cost_thb",
            "status",
            "transport_mode",
        ],
        "metrics": ["total_weight_kg", "shipping_cost_thb"],
    },
    "fact_inventory": {
        "description": "สถานะสินค้าในคลังรายรอบ",
        "columns": [
            "inventory_id",
            "snapshot_date_key",
            "warehouse_sk",
            "crop_sk",
            "beginning_stock_kg",
            "received_kg",
            "sold_kg",
            "ending_stock_kg",
            "unit_cost_thb",
        ],
        "metrics": ["ending_stock_kg", "received_kg", "sold_kg", "unit_cost_thb"],
    },
    "dim_date": {
        "description": "มิติเวลา",
        "columns": ["date_key", "date", "day", "month", "quarter", "year", "weekday"],
    },
    "dim_crop": {
        "description": "ข้อมูลผลผลิต",
        "columns": [
            "crop_sk",
            "crop_id",
            "crop_name",
            "category",
            "unit",
            "standard_price_per_unit",
            "season_months",
            "shelf_life_days",
        ],
    },
    "dim_warehouse": {
        "description": "ข้อมูลคลังสินค้า",
        "columns": [
            "warehouse_sk",
            "warehouse_id",
            "warehouse_name",
            "province",
            "region",
            "capacity_ton",
            "manager_name",
        ],
    },
    "dim_farmer": {
        "description": "ข้อมูลเกษตรกรแบบ SCD Type 2",
        "columns": [
            "farmer_sk",
            "farmer_id",
            "farmer_name",
            "province",
            "region",
            "cooperative",
            "farm_size_rai",
            "primary_crop",
            "valid_from",
            "valid_to",
            "is_current",
        ],
    },
    "dim_customer": {
        "description": "ข้อมูลลูกค้าแบบ SCD Type 2",
        "columns": [
            "customer_sk",
            "customer_id",
            "customer_name",
            "customer_type",
            "province",
            "region",
            "credit_limit_thb",
            "valid_from",
            "valid_to",
            "is_current",
        ],
    },
}


def render_schema_context() -> str:
    lines: list[str] = []
    for table_name, table in DATA_WAREHOUSE_SCHEMA.items():
        columns = ", ".join(table["columns"])
        lines.append(f"- {table_name}: {table['description']} | columns: {columns}")
    return "\n".join(lines)

