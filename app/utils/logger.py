
"""
项目日志工具
====================
基本日志输出：控制台 + logs/app.log 文件双通道。

用法示例：
    from app.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("学生创建成功: %s", student_no)
    logger.error("查询失败: %s", err)
"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 常量配置
# 日志格式：时间 | 日志级别 | 产生日志的模块名:行号 | 内容
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 日志目录
LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
# LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"



def get_logger(name: str = "wolin_sms") -> logging.Logger:
    """
    获取业务日志记录器（控制台 + 文件输出）。
    用法：get_logger(__name__)
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

        # 通道 1: 控制台
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)

        # 通道 2: 文件（超过 5MB 自动轮转，保留 3 份）防止日志无限膨胀把磁盘撑爆
        LOG_DIR.mkdir(parents=True, exist_ok=True)  # 目录不存在时创建，已存在不报错。
        file = RotatingFileHandler(
            LOG_DIR / "app.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file.setFormatter(formatter)
        logger.addHandler(file)
    return logger
