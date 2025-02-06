import hashlib
import logging
import os
import sqlite3
import traceback

from device_operation.SQLiteClient import SQLiteClient


class SQLInitialization:
    def __init__(self, sql_script_path: str = None, marker_file: str = None):
        """
        初始化类，检查 SQL 脚本文件是否变更
        :param sql_script_path: SQL 脚本文件路径，用于检测文件是否变更
        :param marker_file: 标记文件，记录上次初始化的状态
        """
        # 获取项目根目录
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # 设置默认路径
        self.sql_script_path = sql_script_path or os.path.join(self.project_root, "db", "init_script.sql")
        self.marker_file = marker_file or os.path.join(self.project_root, "db", "init_marker.txt")

    def get_file_hash(self) -> str:
        """计算文件的 hash 值，用于检测文件是否变更"""
        with open(self.sql_script_path, 'rb') as f:
            file_content = f.read()
        return hashlib.sha256(file_content).hexdigest()

    def get_file_modification_time(self) -> float:
        """获取文件的修改时间"""
        return os.path.getmtime(self.sql_script_path)

    def should_initialize(self) -> bool:
        """检查 SQL 脚本文件是否变更"""
        if not os.path.exists(self.marker_file):
            return True

        with open(self.marker_file, 'r') as f:
            last_mod_time, last_file_hash = f.read().split("\n")
            last_mod_time = float(last_mod_time)
            last_file_hash = last_file_hash.strip()

        current_mod_time = self.get_file_modification_time()
        current_file_hash = self.get_file_hash()

        return current_mod_time > last_mod_time or current_file_hash != last_file_hash

    def run_initialization(self):
        """执行初始化逻辑"""
        logging.info("执行初始化...")
        self.setup()

    def setup(self):
        """实际初始化的逻辑"""
        if not os.path.exists(self.sql_script_path):
            raise FileNotFoundError(f"SQL 脚本文件不存在：{self.sql_script_path}")

        with open(self.sql_script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
        with SQLiteClient() as db:
            for statement in statements:
                try:
                    db.execute_update(statement + ";")
                    logging.info(f"成功执行：{statement}")
                except sqlite3.OperationalError as e:
                    logging.error(f"执行失败：{statement}\n错误信息：{e}")

        # 完成初始化后，记录当前文件的修改时间和哈希值
        current_mod_time = self.get_file_modification_time()
        current_file_hash = self.get_file_hash()
        with open(self.marker_file, 'w') as f:
            f.write(f"{current_mod_time}\n{current_file_hash}")

    def initialization(self):
        """执行初始化检查并初始化"""
        # logging.info("调用堆栈追踪:\n%s", "".join(traceback.format_stack()))
        if self.should_initialize():
            self.run_initialization()
        else:
            logging.info("脚本没有变更，不需要初始化。")

