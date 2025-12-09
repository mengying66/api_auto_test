import pytest
from common.request_handler import RequestHandler

@pytest.fixture(scope="session")  # 会话级别，只执行一次
def login_token():
    """获取登录token，供其他接口使用"""
    req = RequestHandler()
    login_data = {"username": "admin", "password": "admin123"}
    response = req.post("/login", json=login_data)
    token = response.json()["token"]
    yield token  # 传递token给用例
    # 后置操作（如登出，可选）
    req.post("/logout", headers={"Authorization": f"Bearer {token}"})

# 其他用例中直接引用fixture
# testcases/test_user.py
def test_get_user_info(login_token):
    req = RequestHandler()
    headers = {"Authorization": f"Bearer {login_token}"}
    response = req.get("/user/info", headers=headers)
    # ... 断言逻辑