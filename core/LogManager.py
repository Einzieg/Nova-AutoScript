import logging
import os
from datetime import datetime

from nicegui import ui


class LogManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, log_level):
        if not hasattr(self, 'initialized'):
            self.loggers = {}
            self.log_level = log_level
            self.log_dir = os.path.join(os.getcwd(), 'logs')
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir)
            self.initialized = True

    def get_logger(self, tab_name):
        """获取指定 tab_name 的 logger"""
        if tab_name not in self.loggers:
            logger = logging.getLogger(tab_name)
            logger.setLevel(logging.DEBUG)  # 默认日志级别是 DEBUG

            # 创建日志流处理器
            log_stream = ui.log(max_lines=1000).classes('h-full w-full')

            # 创建一个自定义的日志处理器
            class UIStreamHandler(logging.Handler):
                def emit(self, record):

                    log_stream.push(record.getMessage())

            # 创建格式化器
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

            # 创建处理器并设置格式化器
            handler = UIStreamHandler()
            handler.setFormatter(formatter)

            # 添加文件处理器
            log_file = os.path.join(self.log_dir, f"{datetime.now().strftime('%Y-%m-%d')}_{tab_name}.log")
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)

            # 将这两个处理器添加到日志器
            logger.addHandler(handler)
            logger.addHandler(file_handler)
            self.loggers[tab_name] = logger

        return self.loggers[tab_name]

    def log(self, message, tab_name, level=logging.INFO):
        """输出日志信息，支持不同级别"""
        logger = self.get_logger(tab_name)

        level_methods = {
            logging.DEBUG: logger.debug,
            logging.INFO: logger.info,
            logging.WARNING: logger.warning,
            logging.ERROR: logger.error,
            logging.CRITICAL: logger.critical,
        }

        log_method = level_methods.get(level)
        log_method(message)

    def set_level(self, tab_name, level):
        """设置指定 tab_name 的日志级别"""
        logger = self.get_logger(tab_name)
        logger.setLevel(level)
