import sys
import logging
from pathlib import Path
import pytest

# 配置日志（可选，便于调试）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def get_project_paths() -> dict:
    """获取项目路径配置（统一管理路径，便于维护）"""
    project_root = Path(__file__).parent
    paths = {
        "testcases_dir": project_root / "testcases",
        "allure_results_dir": project_root / "reports" / "allure-results",
        "allure_report_dir": project_root / "reports" / "allure-report"  # 新增报告输出目录
    }
    # 确保目录存在
    for path in paths.values():
        path.mkdir(exist_ok=True, parents=True)
    return paths


def run_pytest_testcases(paths: dict, marker: str = "login") -> None:
    """
    执行pytest测试用例

    Args:
        paths: 路径配置字典
        marker: 要执行的测试标记（默认login）
    """
    # 构造pytest参数列表（更灵活的参数化）
    pytest_args = [
        str(paths["testcases_dir"] / "test_login_excel.py"),  # 路径转字符串，兼容旧版本pytest
        "-vs",  # 详细日志+显示跳过的用例
        f"--alluredir={paths['allure_results_dir']}",
        f"-m={marker}",
        "--tb=short",  # 简化traceback输出（可选）
        "--disable-warnings"  # 禁用警告（可选，根据需求调整）
    ]

    logger.info(f"开始执行测试用例，参数：{pytest_args}")

    try:
        # 执行pytest并获取退出码
        exit_code = pytest.main(pytest_args)
        if exit_code == 0:
            logger.info("测试用例执行成功！")
        else:
            logger.error(f"测试用例执行失败，退出码：{exit_code}")
            sys.exit(exit_code)  # 非0退出码终止程序

    except Exception as e:
        logger.error(f"测试用例执行异常：{str(e)}", exc_info=True)
        sys.exit(1)


def generate_allure_report(paths: dict) -> None:
    """生成Allure HTML报告（可选扩展）"""
    try:
        from subprocess import run
        # 检查allure命令是否可用
        run(["allure", "--version"], check=True, capture_output=True)
        # 生成报告（覆盖旧报告）
        run([
            "allure", "generate",
            str(paths["allure_results_dir"]),
            "-o", str(paths["allure_report_dir"]),
            "--clean"
        ], check=True)
        logger.info(f"Allure报告已生成至：{paths['allure_report_dir']}")

    except ImportError:
        logger.warning("未找到allure模块，跳过报告生成")
    except Exception as e:
        logger.error(f"生成Allure报告失败：{str(e)}", exc_info=True)


if __name__ == "__main__":
    # 获取路径配置
    project_paths = get_project_paths()

    # 执行测试用例
    run_pytest_testcases(project_paths, marker="login")

    # 可选：自动生成Allure报告（根据需求启用）
    generate_allure_report(project_paths)