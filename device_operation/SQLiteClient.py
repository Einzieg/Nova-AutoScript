import logging
import os
import sqlite3
from typing import List, Tuple, Any, Optional


class SQLiteClient:
    def __init__(self):
        """
        初始化 SQLiteHelper 实例
        """
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(self.project_root, "db", "nova_auto_script.db")
        self.connection = None
        self.cursor = None

    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close()

    def _connect(self):
        """建立数据库连接"""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()

    def _close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        self.connection = None
        self.cursor = None

    def execute_query(self, query: str, params: tuple = ()) -> List[dict]:
        """
        执行查询并返回结果（列表形式）
        :param query: SQL 查询语句
        :param params: 查询参数
        :return: 查询结果（列表，每个元素是一个字典）
        """
        self._connect()
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        columns = [description[0] for description in self.cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """
        执行插入、更新或删除语句
        :param query: SQL 更新语句
        :param params: SQL 更新的参数
        :return: 受影响的行数
        """
        try:
            self._connect()
            self.cursor.execute(query, params)
            self.connection.commit()
            logging.info(f"Executing query: {query} with params: {params}")
            return self.cursor.rowcount
        except sqlite3.Error as e:
            self.connection.rollback()
            logging.error(f"Error executing query: {e}")
            raise e

    def create_table(self, table_name: str, columns: List[Tuple[str, str]]) -> None:
        """
        创建表
        :param table_name: 表名
        :param columns: 列名和列类型的元组列表
        """
        column_defs = ", ".join([f"{col[0]} {col[1]}" for col in columns])
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_defs})"
        self.execute_update(query)

    def insert_data(self, table_name: str, columns: List[str], values: List[Any]) -> int:
        """
        插入数据
        :param table_name: 表名
        :param columns: 列名列表
        :param values: 值的列表
        :return: 插入的行数
        """
        placeholders = ", ".join(["?" for _ in columns])
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        return self.execute_update(query, tuple(values))

    def fetch_all(self, query: str, params: Tuple = ()) -> List[dict]:
        """
        执行查询并返回所有结果
        :param query: SQL 查询语句
        :param params: 查询参数
        :return: 所有查询结果（列表，每个元素是一个字典）
        """
        return self.execute_query(query, params)

    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[dict]:
        """
        执行查询并返回单行结果
        :param query: SQL 查询语句
        :param params: 查询参数
        :return: 单行查询结果（字典），如果没有结果则返回 None
        """
        results = self.execute_query(query, params)
        return results[0] if results else None
