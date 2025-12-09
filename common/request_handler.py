# 请求封装（含日志、重试）
import requests
from .log_handler import logger
from config.env import Config


class RequestHandler:
    def __init__(self):
        self.config = Config()
        self.session = requests.Session()  # 维持会话（自动处理cookie）

    def send_request(self, method, url, **kwargs):
        # 拼接完整URL
        full_url = self.config.base_url + url
        # 补充超时参数
        kwargs.setdefault("timeout", self.config.timeout)

        # 日志记录请求信息
        logger.info(f"请求: {method} {full_url}, 参数: {kwargs}")

        try:
            response = self.session.request(method, full_url, **kwargs)
            logger.info(f"响应: 状态码 {response.status_code}, 内容: {response.text}")
            return response
        except Exception as e:
            logger.error(f"请求失败: {str(e)}", exc_info=True)
            raise  # 抛出异常，让用例捕获

    # 快捷方法（简化调用）
    def get(self, url, **kwargs):
        return self.send_request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.send_request("POST", url, **kwargs)