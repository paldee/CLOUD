from app.guardrails.sql_guard import validate_and_bound_sql


def test_accepts_allowlisted_select_and_adds_limit() -> None:
    result = validate_and_bound_sql(
        "SELECT sales_id, total_amount_thb FROM data_warehouse.fact_sales"
    )

    assert result.allowed is True
    assert result.sql is not None
    assert "LIMIT 100" in result.sql


def test_rejects_write_statement() -> None:
    result = validate_and_bound_sql(
        "DELETE FROM data_warehouse.fact_sales WHERE sales_id = 1"
    )

    assert result.allowed is False
    assert "Only SELECT queries are allowed" in result.violations


def test_rejects_non_allowlisted_table() -> None:
    result = validate_and_bound_sql("SELECT password FROM public.users")

    assert result.allowed is False
    assert "Table is not allowlisted: users" in result.violations
    assert "Schema is not allowlisted: public" in result.violations


def test_rejects_select_star() -> None:
    result = validate_and_bound_sql("SELECT * FROM data_warehouse.fact_sales")

    assert result.allowed is False
    assert "SELECT * is not allowed" in result.violations


def test_accepts_count_star() -> None:
    result = validate_and_bound_sql(
        "SELECT COUNT(*) AS row_count FROM data_warehouse.fact_inventory"
    )

    assert result.allowed is True


def test_rejects_column_from_wrong_qualified_table() -> None:
    result = validate_and_bound_sql(
        "SELECT s.farmer_name FROM data_warehouse.fact_sales AS s"
    )

    assert result.allowed is False
    assert "Column is not allowlisted: farmer_name" in result.violations


def test_caps_existing_limit() -> None:
    result = validate_and_bound_sql(
        "SELECT sales_id FROM data_warehouse.fact_sales LIMIT 1000"
    )

    assert result.allowed is True
    assert result.sql is not None
    assert "LIMIT 100" in result.sql


def test_rejects_multiple_statements() -> None:
    result = validate_and_bound_sql(
        "SELECT sales_id FROM data_warehouse.fact_sales; "
        "SELECT farmer_id FROM data_warehouse.dim_farmer"
    )

    assert result.allowed is False
    assert "Exactly one SQL statement is allowed" in result.violations
