import pytest
from common.request_handler import RequestHandler
from utils.read_file import ExcelReader


def pytest_addoption(parser: pytest.Parser) -> None:
    """注册自定义命令行参数。

    Args:
        parser: pytest 命令行参数解析器。
    """
    parser.addoption(
        "--excel",
        default="testcases/autotest_case.xlsx",
        help="Excel 用例文件路径，默认: testcases/autotest_case.xlsx",
    )
    parser.addoption(
        "--sheet",
        default="Sheet1",
        help="Excel Sheet 名称，默认: Sheet1",
    )


@pytest.fixture(scope="session")
def excel_cases(request: pytest.FixtureRequest) -> list[dict]:
    """加载 Excel 测试用例列表（session 级别）。

    从 --excel / --sheet 命令行参数读取路径和 Sheet 名，
    调用 ExcelReader 解析并返回用例列表。

    Args:
        request: pytest fixture 请求对象。

    Returns:
        TestCase 字典列表。
    """
    excel_path: str = request.config.getoption("--excel")
    sheet_name: str = request.config.getoption("--sheet")
    return ExcelReader(excel_path, sheet_name).load_cases()


@pytest.fixture(scope="session")  # 会话级别，只执行一次
def login_token() -> str:
    """获取登录 token，供其他接口使用。

    Returns:
        登录成功后的 Bearer Token 字符串。
    """
    req = RequestHandler()
    login_data = {"username": "admin", "password": "admin123"}
    response = req.post("/login", json=login_data)
    token: str = response.json()["token"]
    yield token  # 传递 token 给用例
    # 后置操作（登出）
    req.post("/logout", headers={"Authorization": f"Bearer {token}"})