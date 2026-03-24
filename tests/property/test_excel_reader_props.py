# describe: ExcelReader 属性测试（基于 hypothesis）
# Feature: excel-driven-api-test-engine

import json
from pathlib import Path

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from openpyxl import Workbook

from utils.read_file import ExcelReader


# ── 辅助函数 ──────────────────────────────────────────────────────────────────

def make_excel_from_rows(
    tmp_path: Path, rows: list[list], sheet_name: str = "Sheet1"
) -> str:
    """创建临时 Excel 文件。

    Args:
        tmp_path: 临时目录路径。
        rows: 行数据，第一行为表头。
        sheet_name: Sheet 名称。

    Returns:
        文件路径字符串。
    """
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    for row in rows:
        ws.append(row)
    path = tmp_path / "prop_cases.xlsx"
    wb.save(str(path))
    return str(path)


# ── Property 1: JSON 列往返解析 ───────────────────────────────────────────────
# Validates: Requirements 1.4, 1.5, 1.6

@given(data=st.dictionaries(
    keys=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
    values=st.text(max_size=50),
    max_size=5,
))
@settings(max_examples=100)
def test_prop1_json_column_roundtrip(data: dict, tmp_path: Path) -> None:
    """Property 1: 合法字典序列化为 JSON 后写入 Excel，解析结果应与原始字典等价。"""
    json_str = json.dumps(data, ensure_ascii=False)
    rows = [
        ["case_id", "title", "method", "url", "params", "run_status"],
        [1, "往返测试", "GET", "/api/test", json_str, "TRUE"],
    ]
    path = make_excel_from_rows(tmp_path, rows)
    cases = ExcelReader(path).load_cases()
    assert cases[0]["params"] == data


# ── Property 2: run_status 过滤 ───────────────────────────────────────────────
# Validates: Requirements 1.2

@given(status_values=st.lists(
    st.sampled_from(["TRUE", "FALSE", "true", "false", "True", None, ""]),
    min_size=1,
    max_size=10,
))
@settings(max_examples=100)
def test_prop2_run_status_filter(status_values: list, tmp_path: Path) -> None:
    """Property 2: 解析结果中不应包含 run_status 不为 TRUE（大小写不敏感）的行。"""
    rows = [["case_id", "title", "method", "url", "run_status"]]
    for i, sv in enumerate(status_values):
        rows.append([i + 1, f"用例{i}", "GET", f"/api/{i}", sv])

    path = make_excel_from_rows(tmp_path, rows)
    cases = ExcelReader(path).load_cases()

    expected_count = sum(
        1 for sv in status_values
        if sv is not None and str(sv).strip().upper() == "TRUE"
    )
    assert len(cases) == expected_count


# ── Property 3: expected_ 前缀列自动识别 ──────────────────────────────────────
# Validates: Requirements 1.3

@given(field_names=st.lists(
    st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=("Ll",))),
    min_size=1,
    max_size=5,
    unique=True,
))
@settings(max_examples=100)
def test_prop3_expected_prefix_recognition(field_names: list[str], tmp_path: Path) -> None:
    """Property 3: 所有 expected_ 前缀列都应收集到 expected 子字典，非前缀列不应出现其中。"""
    headers = ["case_id", "title", "method", "url", "run_status"]
    values: list = [1, "测试", "GET", "/api/test", "TRUE"]

    for name in field_names:
        headers.append(f"expected_{name}")
        values.append(f"val_{name}")

    rows = [headers, values]
    path = make_excel_from_rows(tmp_path, rows)
    cases = ExcelReader(path).load_cases()

    assert len(cases) == 1
    expected = cases[0]["expected"]

    # 所有 expected_ 列都应在 expected 子字典中
    for name in field_names:
        assert name in expected

    # expected 子字典中不应有非 expected_ 列的 key
    reserved_non_expected = {"case_id", "title", "method", "url", "run_status"}
    for key in expected:
        assert key not in reserved_non_expected


# ── Property 4: run_status 布尔解析 ───────────────────────────────────────────
# Validates: Requirements 1.8

@given(value=st.one_of(st.just("TRUE"), st.just("true"), st.just("True"), st.just("TrUe")))
@settings(max_examples=50)
def test_prop4_run_status_true_variants(value: str, tmp_path: Path) -> None:
    """Property 4a: TRUE 的各种大小写变体都应解析为 True。"""
    rows = [
        ["case_id", "title", "method", "url", "run_status"],
        [1, "测试", "GET", "/api/test", value],
    ]
    path = make_excel_from_rows(tmp_path, rows)
    cases = ExcelReader(path).load_cases()
    assert len(cases) == 1
    assert cases[0]["run_status"] is True


@given(value=st.one_of(
    st.just("FALSE"), st.just("false"), st.just("0"),
    st.just(""), st.just("no"), st.just("N"),
))
@settings(max_examples=50)
def test_prop4_run_status_false_variants(value: str, tmp_path: Path) -> None:
    """Property 4b: 非 TRUE 值都应解析为 False（用例被跳过）。"""
    rows = [
        ["case_id", "title", "method", "url", "run_status"],
        [1, "测试", "GET", "/api/test", value],
    ]
    path = make_excel_from_rows(tmp_path, rows)
    cases = ExcelReader(path).load_cases()
    assert len(cases) == 0


# ── Property 5: 文件不存在时抛出 FileNotFoundError ────────────────────────────
# Validates: Requirements 1.9

@given(suffix=st.text(
    min_size=1, max_size=20,
    alphabet=st.characters(whitelist_categories=("Ll", "Nd")),
))
@settings(max_examples=50)
def test_prop5_file_not_found(suffix: str) -> None:
    """Property 5: 任意不存在的路径都应抛出 FileNotFoundError，且消息包含路径。"""
    bad_path = f"/nonexistent/path_{suffix}/cases.xlsx"
    with pytest.raises(FileNotFoundError, match=bad_path.replace("/", "/")):
        ExcelReader(bad_path)


# ── Property 6: 非法 JSON 字段抛出 ValueError ─────────────────────────────────
# Validates: Requirements 1.10

@given(bad_value=st.text(min_size=1, max_size=30).filter(
    lambda s: s.strip() != "" and not _is_valid_json_dict(s)
))
@settings(max_examples=100)
def test_prop6_invalid_json_raises_value_error(bad_value: str, tmp_path: Path) -> None:
    """Property 6: 非空且非合法 JSON 字典的 params 值应抛出 ValueError，包含列名。"""
    rows = [
        ["case_id", "title", "method", "url", "params", "run_status"],
        [1, "测试", "GET", "/api/test", bad_value, "TRUE"],
    ]
    path = make_excel_from_rows(tmp_path, rows)
    with pytest.raises(ValueError, match="params"):
        ExcelReader(path).load_cases()


def _is_valid_json_dict(s: str) -> bool:
    """判断字符串是否为合法 JSON 字典。"""
    try:
        result = json.loads(s)
        return isinstance(result, dict)
    except (json.JSONDecodeError, ValueError):
        return False


# ── Property 14: 空值字段忽略 ─────────────────────────────────────────────────
# Validates: Requirements 5.3

@given(null_col=st.sampled_from(["headers", "params", "body"]))
@settings(max_examples=30)
def test_prop14_null_fields_return_none(null_col: str, tmp_path: Path) -> None:
    """Property 14: None 或空字符串的 JSON 列应解析为 None，不返回空字典。"""
    for null_val in [None, ""]:
        rows = [
            ["case_id", "title", "method", "url", null_col, "run_status"],
            [1, "测试", "GET", "/api/test", null_val, "TRUE"],
        ]
        path = make_excel_from_rows(tmp_path, rows)
        cases = ExcelReader(path).load_cases()
        assert cases[0][null_col] is None
