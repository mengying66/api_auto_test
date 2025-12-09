# author=@mengmeng
# time：2025/12/3 10：16：41
# describe：

# testcases/test_login_excel.py
import pytest
import requests
import allure
from pathlib import Path
from utils.read_file import read_excel

# 读取Excel用例（过滤is_run=True的用例）
CASE_FILE = Path(__file__).parent / "autotest_case.xlsx"
test_cases = read_excel(str(CASE_FILE), sheet_name="Sheet1")


@allure.feature("登录模块")
class TestLoginWithExcel:
    # 接口基础配置
    login_url = "https://test-admin.allreaday.com/api/account/login"

    @allure.story("账号密码登录")
    @pytest.mark.login
    @pytest.mark.parametrize("case", test_cases)  # 参数化传入Excel用例
    def test_login(self, case):
        """登录接口测试（Excel驱动）"""
        # 动态设置用例标题
        allure.dynamic.title(f"[{case['case_id']}] {case['title']}")

        # 1. 构造请求参数
        payload = {
            "username": case["username"],
            "password": case["password"]
        }

        # 2. 发送请求（添加Allure步骤）
        with allure.step("发送登录请求"):
            response = requests.post(
                url=self.login_url,
                json=payload,
                timeout=10
            )
            allure.attach(f"请求参数：{payload}", name="Request", attachment_type=allure.attachment_type.JSON)
            allure.attach(f"响应内容：{response.text}", name="Response", attachment_type=allure.attachment_type.JSON)

        # 3. 结果断言
        result = response.json()
        with allure.step("验证响应结果"):
            assert response.status_code == 200, f"接口请求失败，状态码：{response.status_code}"
            assert result["code"] == case["expected_code"], f"预期code：{case['expected_code']}，实际：{result['code']}"
            assert result["msg"] == case["expected_msg"], f"预期msg：{case['expected_msg']}，实际：{result['msg']}"