import datetime
import logging
import os
import time
from logging.handlers import TimedRotatingFileHandler

from nicegui import ui


class LogManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.loggers = {}
            self.log_dir = os.path.join(os.getcwd(), 'logs')
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir)

            # 初始化时清理过期日志（保险措施，TimedRotatingFileHandler 也会做清理）
            # self.cleanup_old_logs(days=7)

            self.initialized = True

    def cleanup_old_logs(self, days=7):
        """删除指定天数之前的日志文件"""
        now = time.time()
        expire_time = days * 24 * 60 * 60  # 秒数

        for filename in os.listdir(self.log_dir):
            filepath = os.path.join(self.log_dir, filename)
            if os.path.isfile(filepath) and filename.endswith(".log"):
                file_mtime = os.path.getmtime(filepath)
                if now - file_mtime > expire_time:
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass

    def get_logger(self, tab_name):
        """获取指定 tab_name 的 logger"""
        if tab_name not in self.loggers:
            logger = logging.getLogger(tab_name)
            logger.setLevel(logging.INFO)  # 默认日志级别

            log_stream = ui.log(max_lines=1000).classes('h-full w-full')

            class UIStreamHandler(logging.Handler):
                def emit(self, record):
                    log_stream.push(record.getMessage())

            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

            handler = UIStreamHandler()
            handler.setFormatter(formatter)
            logger.addHandler(handler)

            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            log_file = os.path.join(self.log_dir, f"{date_str}_{tab_name}.log")

            file_handler = TimedRotatingFileHandler(
                log_file,
                when="midnight",
                interval=1,
                backupCount=7,
                encoding="utf-8",
                utc=False
            )
            file_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            self.loggers[tab_name] = logger

        return self.loggers[tab_name]

    def log(self, message, tab_name, level=logging.INFO):
        """输出日志信息，支持不同级别"""
        logger = self.get_logger(tab_name)
        logger.log(level, message)

    def set_level(self, tab_name, level):
        """设置指定 tab_name 的日志级别"""
        logger = self.get_logger(tab_name)
        logger.setLevel(level)

    def clear(self):
        self.loggers = {}
