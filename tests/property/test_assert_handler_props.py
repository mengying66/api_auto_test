# describe: AssertHandler 属性测试（基于 hypothesis）
# Feature: excel-driven-api-test-engine

import json
from unittest.mock import MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from common.assert_handler import AssertHandler


def make_mock_response(status_code: int, body: dict) -> MagicMock:
    """构造 mock Response 对象。

    Args:
        status_code: HTTP 状态码。
        body: 响应 JSON 字典。

    Returns:
        mock Response 对象。
    """
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = body
    resp.text = json.dumps(body, ensure_ascii=False)
    return resp


# ── Property 11: 多字段断言正确性 ─────────────────────────────────────────────
# Validates: Requirements 3.2, 3.6

@given(fields=st.dictionaries(
    keys=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Ll",))),
    values=st.text(max_size=20),
    min_size=1,
    max_size=5,
))
@settings(max_examples=100)
def test_prop11_assert_matching_fields_passes(fields: dict) -> None:
    """Property 11a: 期望值与响应值完全一致时，断言应通过（不抛出异常）。"""
    resp = make_mock_response(200, fields)
    # expected 值与响应值相同，断言应通过
    AssertHandler.assert_response(resp, fields)


@given(
    field=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Ll",))),
    actual=st.text(max_size=20),
    wrong=st.text(max_size=20),
)
@settings(max_examples=100)
def test_prop11_assert_mismatched_field_fails(field: str, actual: str, wrong: str) -> None:
    """Property 11b: 期望值与实际值不一致时，断言应失败。"""
    from hypothesis import assume
    assume(actual != wrong)

    resp = make_mock_response(200, {field: actual})
    with pytest.raises(Exception):
        AssertHandler.assert_response(resp, {field: wrong})


# ── Property 12: 断言失败信息完整性 ───────────────────────────────────────────
# Validates: Requirements 3.3

@given(
    field=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Ll",))),
    expected_val=st.text(min_size=1, max_size=20),
    actual_val=st.text(min_size=1, max_size=20),
)
@settings(max_examples=100)
def test_prop12_failure_message_contains_all_info(
    field: str, expected_val: str, actual_val: str
) -> None:
    """Property 12: 断言失败时错误信息应同时包含字段名、期望值、实际值。"""
    from hypothesis import assume
    assume(expected_val != actual_val)

    resp = make_mock_response(200, {field: actual_val})
    with pytest.raises(Exception) as exc_info:
        AssertHandler.assert_response(resp, {field: expected_val})

    error_msg = str(exc_info.value)
    assert field in error_msg
    assert expected_val in error_msg
    assert actual_val in error_msg


# ── Property 13: 缺失字段断言失败 ─────────────────────────────────────────────
# Validates: Requirements 3.5

@given(
    missing_field=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Ll",))),
    other_field=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Ll",))),
)
@settings(max_examples=100)
def test_prop13_missing_field_fails_with_field_name(
    missing_field: str, other_field: str
) -> None:
    """Property 13: 响应 JSON 中不存在的期望字段应断言失败，且错误信息包含该字段名。"""
    from hypothesis import assume
    assume(missing_field != other_field)
    assume(missing_field != "code")

    # 响应中只有 other_field，没有 missing_field
    resp = make_mock_response(200, {other_field: "some_value"})
    with pytest.raises(Exception) as exc_info:
        AssertHandler.assert_response(resp, {missing_field: "expected_value"})

    assert missing_field in str(exc_info.value)
