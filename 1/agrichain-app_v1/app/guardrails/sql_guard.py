from dataclasses import dataclass

from sqlglot import exp, parse
from sqlglot.errors import ParseError

from app.core.config import settings
from app.db.schema_catalog import DATA_WAREHOUSE_SCHEMA


@dataclass(frozen=True)
class SQLValidationResult:
    allowed: bool
    sql: str | None = None
    violations: tuple[str, ...] = ()


class SQLGuardrailError(ValueError):
    def __init__(self, violations: tuple[str, ...]):
        self.violations = violations
        super().__init__("; ".join(violations))


def validate_and_bound_sql(sql: str) -> SQLValidationResult:
    """Parse, validate, and cap one PostgreSQL read-only query."""
    if not sql.strip():
        return SQLValidationResult(False, violations=("SQL is empty",))

    try:
        statements = parse(sql, read="postgres")
    except ParseError as exc:
        return SQLValidationResult(False, violations=(f"SQL parse error: {exc}",))

    if len(statements) != 1:
        return SQLValidationResult(
            False,
            violations=("Exactly one SQL statement is allowed",),
        )

    statement = statements[0]
    violations: list[str] = []

    if not isinstance(statement, exp.Query):
        violations.append("Only SELECT queries are allowed")

    has_wildcard_projection = any(
        projection.is_star
        for select in statement.find_all(exp.Select)
        for projection in select.expressions
    )
    if has_wildcard_projection:
        violations.append("SELECT * is not allowed")

    cte_names = {cte.alias_or_name.lower() for cte in statement.find_all(exp.CTE)}
    allowed_tables = {name.lower() for name in DATA_WAREHOUSE_SCHEMA}
    referenced_tables: set[str] = set()
    table_aliases: dict[str, str] = {}

    for table in statement.find_all(exp.Table):
        table_name = table.name.lower()
        if table_name in cte_names:
            continue
        referenced_tables.add(table_name)
        table_aliases[table_name] = table_name
        table_aliases[table.alias_or_name.lower()] = table_name
        if table_name not in allowed_tables:
            violations.append(f"Table is not allowlisted: {table.name}")
        if table.db and table.db.lower() != settings.database_schema.lower():
            violations.append(f"Schema is not allowlisted: {table.db}")

    if not referenced_tables:
        violations.append("Query must reference an allowlisted warehouse table")

    allowed_columns = {
        column.lower()
        for table_name in referenced_tables
        for column in DATA_WAREHOUSE_SCHEMA.get(table_name, {}).get("columns", [])
    }
    projected_aliases = {
        expression.alias.lower()
        for select in statement.find_all(exp.Select)
        for expression in select.expressions
        if expression.alias
    }
    for column in statement.find_all(exp.Column):
        column_name = column.name.lower()
        qualifier = column.table.lower()
        if qualifier and qualifier in table_aliases:
            table_name = table_aliases[qualifier]
            table_columns = {
                name.lower()
                for name in DATA_WAREHOUSE_SCHEMA.get(table_name, {}).get("columns", [])
            }
            column_is_allowed = column_name in table_columns
        elif qualifier and qualifier in cte_names:
            column_is_allowed = column_name in allowed_columns | projected_aliases
        elif qualifier:
            column_is_allowed = False
        else:
            column_is_allowed = column_name in allowed_columns | projected_aliases

        if not column_is_allowed:
            violations.append(f"Column is not allowlisted: {column.name}")

    if violations:
        return SQLValidationResult(False, violations=tuple(dict.fromkeys(violations)))

    bounded_statement = _apply_row_limit(statement)
    return SQLValidationResult(True, sql=bounded_statement.sql(dialect="postgres"))


def require_safe_sql(sql: str) -> str:
    result = validate_and_bound_sql(sql)
    if not result.allowed or result.sql is None:
        raise SQLGuardrailError(result.violations)
    return result.sql


def _apply_row_limit(statement: exp.Query) -> exp.Query:
    limit = statement.args.get("limit")
    if limit is None:
        return statement.limit(settings.max_sql_rows)

    limit_expression = limit.expression
    if isinstance(limit_expression, exp.Literal) and limit_expression.is_int:
        if int(limit_expression.this) <= settings.max_sql_rows:
            return statement

    return statement.limit(settings.max_sql_rows, copy=True)
