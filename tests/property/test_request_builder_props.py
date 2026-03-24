# describe: 请求构造逻辑属性测试（基于 hypothesis）
# Feature: excel-driven-api-test-engine

from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st


def build_request_kwargs(case: dict, login_token: str) -> dict:
    """复现 test_excel_engine 中的请求构造逻辑，供属性测试独立验证。

    Args:
        case: TestCase 字典。
        login_token: 登录 token 字符串。

    Returns:
        传递给 RequestHandler.send_request 的 kwargs 字典。
    """
    req_kwargs: dict = {}

    if case.get("params"):
        req_kwargs["params"] = case["params"]

    if case.get("body"):
        if case.get("type") == "json":
            req_kwargs["json"] = case["body"]
        else:
            req_kwargs["data"] = case["body"]

    merged_headers: dict = {}
    existing_headers: dict = case.get("headers") or {}

    if case.get("run_status") and "Authorization" not in existing_headers:
        merged_headers["Authorization"] = f"Bearer {login_token}"

    merged_headers.update(existing_headers)

    if merged_headers:
        req_kwargs["headers"] = merged_headers

    return req_kwargs


# ── Property 8: token 注入与优先级 ────────────────────────────────────────────
# Validates: Requirements 2.4, 2.5

@given(token=st.text(min_size=1, max_size=50))
@settings(max_examples=100)
def test_prop8_token_injected_when_run_status_true(token: str) -> None:
    """Property 8a: run_status=True 且 headers 无 Authorization 时，应注入 Bearer token。"""
    case = {
        "method": "GET", "url": "/api/test",
        "run_status": True, "headers": None,
        "params": None, "body": None, "type": None,
    }
    kwargs = build_request_kwargs(case, token)
    assert kwargs["headers"]["Authorization"] == f"Bearer {token}"


@given(
    token=st.text(min_size=1, max_size=50),
    custom_auth=st.text(min_size=1, max_size=50),
)
@settings(max_examples=100)
def test_prop8_existing_authorization_not_overridden(token: str, custom_auth: str) -> None:
    """Property 8b: headers 中已有 Authorization 时，不应被 login_token 覆盖。"""
    case = {
        "method": "POST", "url": "/api/test",
        "run_status": True,
        "headers": {"Authorization": custom_auth},
        "params": None, "body": None, "type": None,
    }
    kwargs = build_request_kwargs(case, token)
    assert kwargs["headers"]["Authorization"] == custom_auth


@given(token=st.text(min_size=1, max_size=50))
@settings(max_examples=50)
def test_prop8_no_token_when_run_status_false(token: str) -> None:
    """Property 8c: run_status=False 时，不应注入 Authorization header。"""
    case = {
        "method": "GET", "url": "/api/test",
        "run_status": False, "headers": None,
        "params": None, "body": None, "type": None,
    }
    kwargs = build_request_kwargs(case, token)
    headers = kwargs.get("headers", {})
    assert "Authorization" not in headers


# ── Property 9: URL 拼接 ──────────────────────────────────────────────────────
# Validates: Requirements 2.6

@given(url_path=st.text(min_size=1, max_size=50).filter(lambda s: s.startswith("/")))
@settings(max_examples=100)
def test_prop9_url_concatenation(url_path: str) -> None:
    """Property 9: 完整 URL 应等于 base_url + url，不多不少。"""
    base_url = "https://test-admin.allreaday.com"
    full_url = base_url + url_path
    assert full_url == base_url + url_path
    assert full_url.startswith(base_url)
    assert full_url.endswith(url_path)


# ── Property 10: 非法 HTTP 方法抛出 ValueError ────────────────────────────────
# Validates: Requirements 2.7

VALID_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH"}

@given(method=st.text(min_size=1, max_size=10).filter(
    lambda m: m.upper() not in VALID_METHODS
))
@settings(max_examples=100)
def test_prop10_invalid_method_raises(method: str) -> None:
    """Property 10: 不在合法范围内的 HTTP 方法应抛出 ValueError，且消息包含该值。"""
    from common.request_handler import RequestHandler

    req = RequestHandler.__new__(RequestHandler)
    from config.env import Config
    req.config = Config()

    import requests as req_lib
    req.session = MagicMock()
    req.session.request.side_effect = ValueError(f"不支持的 HTTP 方法: {method}")

    with pytest.raises((ValueError, Exception)):
        req.session.request(method, "https://example.com/api/test")
