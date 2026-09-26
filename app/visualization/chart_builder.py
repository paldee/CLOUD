from dataclasses import dataclass, field
from numbers import Number
from typing import Literal


ChartType = Literal["bar", "line"]
TIME_DIMENSIONS = {
    "year",
    "quarter",
    "month",
    "date",
    "sale_date",
    "harvest_date",
    "shipment_date",
    "snapshot_date",
}
MAX_DATASETS = 3
MAX_POINTS = 60


@dataclass(frozen=True)
class ChartDataset:
    label: str
    data: list[float | None] = field(default_factory=list)


@dataclass(frozen=True)
class ChartSpec:
    type: ChartType
    title: str
    labels: list[str] = field(default_factory=list)
    datasets: list[ChartDataset] = field(default_factory=list)
    total_points: int = 0


def build_chart_spec(question: str, rows: list[dict]) -> ChartSpec | None:
    """Build a small chart spec from query rows without asking the LLM."""
    if len(rows) < 2:
        return None

    keys = list(rows[0])
    time_keys = [key for key in keys if key.lower() in TIME_DIMENSIONS]
    dimension_keys = [
        key
        for key in keys
        if key in time_keys or not _column_is_numeric(rows, key)
    ]
    measure_keys = [
        key
        for key in keys
        if key not in dimension_keys and _column_has_number(rows, key)
    ][:MAX_DATASETS]
    if not measure_keys:
        return None

    chart_rows = rows[:MAX_POINTS]
    labels = [
        _build_label(row, dimension_keys, index)
        for index, row in enumerate(chart_rows)
    ]
    datasets = [
        ChartDataset(
            label=_humanize(measure_key),
            data=[_as_float(row.get(measure_key)) for row in chart_rows],
        )
        for measure_key in measure_keys
    ]
    return ChartSpec(
        type="line" if time_keys else "bar",
        title=question,
        labels=labels,
        datasets=datasets,
        total_points=len(rows),
    )


def _column_has_number(rows: list[dict], key: str) -> bool:
    return any(_is_number(row.get(key)) for row in rows)


def _column_is_numeric(rows: list[dict], key: str) -> bool:
    values = [row.get(key) for row in rows if row.get(key) is not None]
    return bool(values) and all(_is_number(value) for value in values)


def _is_number(value: object) -> bool:
    return isinstance(value, Number) and not isinstance(value, bool)


def _as_float(value: object) -> float | None:
    return float(value) if _is_number(value) else None


def _build_label(row: dict, dimension_keys: list[str], index: int) -> str:
    if not dimension_keys:
        return str(index + 1)

    values = [str(row.get(key, "-")) for key in dimension_keys]
    return " / ".join(values)


def _humanize(name: str) -> str:
    return name.replace("_", " ").strip().title()
