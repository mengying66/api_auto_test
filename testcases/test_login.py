# testcases/test_login.py
import pytest
import yaml
from pathlib import Path
from common.request_handler import RequestHandler
from common.assert_handler import AssertHandler

# 读取测试数据
def load_login_data():
    with open(Path(__file__).parent.parent / "data" / "login_data.yaml", "r") as f:
        return yaml.safe_load(f)

@pytest.mark.login
class TestLogin:
    def setup_class(self):
        self.req = RequestHandler()
        self.assertor = AssertHandler()

    @pytest.mark.parametrize("case", load_login_data())
    def test_login(self, case):
        # 请求参数
        data = {
            "username": case["username"],
            "password": case["password"]
        }
        # 发送请求
        response = self.req.post("/api/account/login", json=data)
        # 断言状态码
        self.assertor.assert_status_code(response, case["expected_code"])
        # 断言响应内容（根据用例动态处理）
        if case["case_name"] == "正常登录":
            self.assertor.assert_json_key(response, "token")
            assert response.json()["data"]["token"] != "", "token为空"
        else:
            self.assertor.assert_json_value(response, "msg", case["expected_msg"])