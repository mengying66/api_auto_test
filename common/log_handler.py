import logging
from pathlib import Path


def init_logger():
    logger = logging.getLogger("api_auto")
    logger.setLevel(logging.INFO)

    # 确保日志目录存在
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # 文件handler
    file_handler = logging.FileHandler(log_dir / "api_test.log", encoding="utf-8")
    # 控制台handler
    console_handler = logging.StreamHandler()

    # 日志格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


logger = init_logger()