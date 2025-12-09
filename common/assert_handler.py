# 断言封装（支持响应字段校验）
from .log_handler import logger
class AssertHandler:
    @staticmethod
    def assert_status_code(response, expected_code):
        """断言响应状态码"""
        actual_code = response.status_code
        assert actual_code == expected_code, \
            f"状态码断言失败: 预期 {expected_code}, 实际 {actual_code}"
        logger.info("状态码断言通过")

    @staticmethod
    def assert_json_key(response, key):
        """断言JSON响应的data中包含指定字段（如token）"""
        json_data = response.json()
        # 1. 先确保data字段存在且是字典
        assert "data" in json_data, "响应中没有data字段"
        data = json_data["data"]
        assert isinstance(data, dict), "data字段不是字典"
        # 2. 检查key是否是data字典的键（正确逻辑）
        assert key in data, f"响应data中不包含字段: {key}"
        logger.info(f"字段 {key} 在data中存在，断言通过")

    @staticmethod
    def assert_json_value(response, key, expected_value):
        """断言JSON响应字段值"""
        json_data = response.json()
        actual_value = json_data.get(key)
        assert actual_value == expected_value, \
            f"字段 {key} 断言失败: 预期 {expected_value}, 实际 {actual_value}"
        logger.info(f"字段 {key} 值断言通过")