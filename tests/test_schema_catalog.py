from app.db.schema_catalog import DATA_WAREHOUSE_SCHEMA, render_schema_context


def test_catalog_has_documented_star_schema() -> None:
    assert set(DATA_WAREHOUSE_SCHEMA) == {
        "dim_date",
        "dim_crop",
        "dim_warehouse",
        "dim_farmer",
        "dim_customer",
        "fact_harvest",
        "fact_sales",
        "fact_shipment",
        "fact_inventory",
    }


def test_every_column_has_type_and_description() -> None:
    for table in DATA_WAREHOUSE_SCHEMA.values():
        assert set(table["columns"]) == set(table["column_types"])
        assert set(table["columns"]) == set(table["column_descriptions"])


def test_rendered_context_contains_grain_relationships_and_rules() -> None:
    context = render_schema_context()

    assert "TABLE: data_warehouse.fact_sales" in context
    assert "GRAIN: 1 แถว = 1 รายการขาย" in context
    assert "customer_sk -> dim_customer.customer_sk" in context
    assert "net_sales_thb = total_amount_thb" in context
    assert "national_id" not in DATA_WAREHOUSE_SCHEMA["dim_farmer"]["columns"]


def test_warehouse_uses_documented_scd3_names() -> None:
    columns = DATA_WAREHOUSE_SCHEMA["dim_warehouse"]["columns"]

    assert "current_warehouse_name" in columns
    assert "previous_warehouse_name" in columns
    assert "warehouse_name" not in columns
