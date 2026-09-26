from app.db.schema_catalog import DATA_WAREHOUSE_SCHEMA
from app.db.schema_verifier import ActualTable, compare_schema, normalize_data_type


def documented_schema_snapshot() -> dict[str, ActualTable]:
    return {
        table_name: ActualTable(
            columns=dict(table["column_types"]),
            primary_key=table["primary_key"],
            foreign_keys=dict(table.get("foreign_keys", {})),
        )
        for table_name, table in DATA_WAREHOUSE_SCHEMA.items()
    }


def test_documented_snapshot_matches_catalog() -> None:
    comparison = compare_schema(documented_schema_snapshot())

    assert comparison.matches is True
    assert comparison.mismatches == ()


def test_comparison_reports_column_type_key_and_table_drift() -> None:
    actual = documented_schema_snapshot()
    sales = actual["fact_sales"]
    changed_columns = dict(sales.columns)
    changed_columns.pop("discount_pct")
    changed_columns["legacy_total"] = "NUMERIC"
    changed_columns["quantity_kg"] = "INTEGER"
    actual["fact_sales"] = ActualTable(
        columns=changed_columns,
        primary_key=None,
        foreign_keys={
            **sales.foreign_keys,
            "customer_sk": "dim_customer.customer_id",
        },
    )
    actual["etl_error_log"] = ActualTable({}, None, {})

    comparison = compare_schema(actual)

    assert comparison.matches is False
    assert "missing column: fact_sales.discount_pct" in comparison.mismatches
    assert "unexpected column: fact_sales.legacy_total" in comparison.mismatches
    assert any(item.startswith("type mismatch: fact_sales.quantity_kg") for item in comparison.mismatches)
    assert any(item.startswith("primary key mismatch: fact_sales") for item in comparison.mismatches)
    assert any(item.startswith("foreign key mismatch: fact_sales.customer_sk") for item in comparison.mismatches)
    assert "unexpected table: etl_error_log" in comparison.mismatches


def test_postgresql_type_names_are_normalized() -> None:
    assert normalize_data_type("character varying") == "VARCHAR"
    assert normalize_data_type("numeric") == "NUMERIC"
    assert normalize_data_type("timestamp with time zone") == "TIMESTAMPTZ"
