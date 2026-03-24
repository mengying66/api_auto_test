# author=@mengmeng
# describe: 通用 Excel 驱动接口测试入口

import json
from typing import Any

import allure
import pytest

from common.assert_handler import AssertHandler
from common.request_handler import RequestHandler


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """动态参数化：将 excel_cases fixture 中的用例注入到 test_api_case。

    Args:
        metafunc: pytest 元函数对象。
    """
    if "case" in metafunc.fixturenames:
        cases: list[dict] = metafunc.config._excel_cases_cache  # type: ignore[attr-defined]
        ids = [f"{c.get('case_id', i)}-{c.get('title', '')}" for i, c in enumerate(cases)]
        metafunc.parametrize("case", cases, ids=ids)


def pytest_configure(config: pytest.Config) -> None:
    """在 pytest 配置阶段预加载 Excel 用例，供 pytest_generate_tests 使用。

    Args:
        config: pytest 配置对象。
    """
    # 仅在非 worker 进程（或单进程）时加载
    if not hasattr(config, "_excel_cases_cache"):
        try:
            from utils.read_file import ExcelReader
            excel_path: str = config.getoption("--excel", default="testcases/autotest_case.xlsx")
            sheet_name: str = config.getoption("--sheet", default="Sheet1")
            config._excel_cases_cache = ExcelReader(excel_path, sheet_name).load_cases()  # type: ignore[attr-defined]
        except Exception:
            config._excel_cases_cache = []  # type: ignore[attr-defined]


@allure.feature("通用接口测试")
class TestExcelEngine:
    """通用 Excel 驱动接口测试类。"""

    @allure.story("Excel 用例驱动")
    def test_api_case(self, case: dict[str, Any], login_token: str) -> None:
        """执行单条 Excel 用例。

        Args:
            case: 从 Excel 解析出的 TestCase 字典。
            login_token: 会话级登录 token（来自 conftest fixture）。
        """
        # 动态设置 Allure 用例标题
        allure.dynamic.title(f"[{case['case_id']}] {case['title']}")

        # ── 构造请求参数 ──────────────────────────────────────────
        req_kwargs: dict[str, Any] = {}

        # params（GET 查询参数）
        if case.get("params"):
            req_kwargs["params"] = case["params"]

        # body（POST 请求体）
        if case.get("body"):
            if case.get("type") == "json":
                req_kwargs["json"] = case["body"]
            else:
                req_kwargs["data"] = case["body"]

        # headers 合并：run_status=True 时注入 token，headers 中已有 Authorization 则优先
        merged_headers: dict[str, str] = {}
        existing_headers: dict[str, str] = case.get("headers") or {}

        if case.get("run_status") and "Authorization" not in existing_headers:
            merged_headers["Authorization"] = f"Bearer {login_token}"

        merged_headers.update(existing_headers)

        if merged_headers:
            req_kwargs["headers"] = merged_headers

        # ── 发送请求 ──────────────────────────────────────────────
        req = RequestHandler()
        full_url = req.config.base_url + case["url"]

        with allure.step(f"发送请求: {case['method']} {full_url}"):
            allure.attach(
                json.dumps(req_kwargs, ensure_ascii=False, indent=2),
                name="请求参数",
                attachment_type=allure.attachment_type.JSON,
            )
            response = req.send_request(case["method"], case["url"], **req_kwargs)
            allure.attach(
                str(response.status_code),
                name="响应状态码",
                attachment_type=allure.attachment_type.TEXT,
            )
            allure.attach(
                response.text,
                name="响应内容",
                attachment_type=allure.attachment_type.JSON,
            )

        # ── 断言 ──────────────────────────────────────────────────
        with allure.step("验证响应结果"):
            try:
                AssertHandler.assert_response(response, case["expected"])
            except Exception as exc:
                # 断言失败时补充附件，再重新抛出
                allure.attach(
                    json.dumps(req_kwargs, ensure_ascii=False, indent=2),
                    name="失败-请求参数",
                    attachment_type=allure.attachment_type.JSON,
                )
                allure.attach(
                    response.text,
                    name="失败-响应内容",
                    attachment_type=allure.attachment_type.JSON,
                )
                raise exc
