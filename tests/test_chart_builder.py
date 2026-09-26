from app.visualization.chart_builder import build_chart_spec


def test_builds_line_chart_for_time_series() -> None:
    chart = build_chart_spec(
        "ยอดขายสุทธิรายเดือน",
        [
            {"year": 2025, "month": 1, "net_sales_thb": 120.5},
            {"year": 2025, "month": 2, "net_sales_thb": 140.0},
        ],
    )

    assert chart is not None
    assert chart.type == "line"
    assert chart.labels == ["2025 / 1", "2025 / 2"]
    assert chart.datasets[0].data == [120.5, 140.0]


def test_builds_bar_chart_for_categories() -> None:
    chart = build_chart_spec(
        "ยอดขายตามภูมิภาค",
        [
            {"region": "เหนือ", "net_sales_thb": 100},
            {"region": "ใต้", "net_sales_thb": 80},
        ],
    )

    assert chart is not None
    assert chart.type == "bar"
    assert chart.labels == ["เหนือ", "ใต้"]
    assert chart.datasets[0].label == "Net Sales Thb"


def test_skips_chart_for_single_value() -> None:
    chart = build_chart_spec("ยอดขายรวม", [{"total_sales_thb": 100}])

    assert chart is None
