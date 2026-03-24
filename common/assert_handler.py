# describe: 通用多字段断言处理器

from typing import Any

import pytest
import requests

from .log_handler import logger


class AssertHandler:
    """通用多字段断言处理器。

    根据 expected 字典对响应进行多字段比对，支持：
    - code 字段与 HTTP 状态码比对
    - 其余字段从响应 JSON 中取值比对
    - 数字字符串类型自动转换
    """

    @staticmethod
    def _coerce_value(expected: Any, actual: Any) -> tuple[Any, Any]:
        """尝试将期望值类型对齐到实际值类型。

        当期望值为数字字符串而实际值为数字时，自动转换后比对。

        Args:
            expected: Excel 中的期望值。
            actual: 响应中的实际值。

        Returns:
            转换后的 (expected, actual) 元组。
        """
        if isinstance(expected, str) and isinstance(actual, (int, float)):
            try:
                return int(expected), actual
            except ValueError:
                try:
                    return float(expected), actual
                except ValueError:
                    pass
        return expected, actual

    @staticmethod
    def assert_response(
        response: requests.Response,
        expected: dict[str, Any],
    ) -> None:
        """对响应执行多字段断言。

        遍历 expected 字典，对每个字段进行比对：
        - "code" 字段与 response.status_code 比对
        - 其余字段从 response.json() 中取同名字段比对

        Args:
            response: HTTP 响应对象。
            expected: 期望值字典，key 为字段名（去掉 expected_ 前缀），value 为期望值。

        Raises:
            pytest.fail: 任意字段断言失败时调用。
        """
        # 解析响应体
        try:
            resp_json: dict[str, Any] = response.json()
        except Exception:
            pytest.fail(f"响应体无法解析为 JSON，原始内容: {response.text}")
            return  # 让类型检查器知道后续不会执行

        for field, exp_val in expected.items():
            if field == "code":
                # code 字段与 HTTP 状态码比对
                exp_coerced, actual = AssertHandler._coerce_value(
                    exp_val, response.status_code
                )
                if exp_coerced != actual:
                    msg = (
                        f"字段 code 断言失败: "
                        f"期望 {exp_coerced}, 实际 {actual}"
                    )
                    logger.error(msg)
                    pytest.fail(msg)
            else:
                # 其余字段从响应 JSON 取值
                if field not in resp_json:
                    msg = f"响应 JSON 中缺少字段: {field}"
                    logger.error(msg)
                    pytest.fail(msg)
                    continue

                actual_val = resp_json[field]
                exp_coerced, actual_coerced = AssertHandler._coerce_value(
                    exp_val, actual_val
                )
                if exp_coerced != actual_coerced:
                    msg = (
                        f"字段 {field} 断言失败: "
                        f"期望 {exp_coerced}, 实际 {actual_coerced}"
                    )
                    logger.error(msg)
                    pytest.fail(msg)

        logger.info(f"所有断言通过，expected: {expected}")
