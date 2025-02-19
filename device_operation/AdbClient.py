import logging
import os
import subprocess
import sys
import time
from threading import Lock


class AdbClient:
    def __init__(self, ip=None, port=5555, adb_path=None, max_retries=3, retry_delay=2):
        """
        初始化AdbClient实例。
        :param ip: 设备IP地址，默认为None。
        :param port: 设备端口号，默认为5555。
        :param adb_path: adb可执行文件的路径，若未提供则自动查找。
        :param max_retries: 连接重试次数，默认为3次。
        :param retry_delay: 每次重试之间的延迟时间，默认为2秒。
        """
        self.ip = ip
        self.port = port
        self.connected = False  # 跟踪连接状态
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.lock = Lock()  # 确保命令唯一执行
        if adb_path is None:
            # 自动确定adb路径
            if getattr(sys, 'frozen', False):
                base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
            else:
                base_path = os.getcwd()
            self.adb_path = os.path.join(base_path, 'static/platform-tools', 'adb.exe')
            if not os.path.exists(self.adb_path):
                raise FileNotFoundError(f"ADB路径 {self.adb_path} 不存在")
        else:
            self.adb_path = adb_path
            if not os.path.exists(self.adb_path):
                raise FileNotFoundError(f"ADB路径 {self.adb_path} 不存在")

    def connect_tcp(self):
        """建立TCP连接"""
        for attempt in range(self.max_retries + 1):
            if self.connected:
                logging.debug("已连接，跳过重复连接")
                return True
            if not self.ip:
                raise ValueError("IP地址不能为空")

            command = ["connect", f"{self.ip}:{self.port}"]
            try:
                result = self._run_command(command)
                result_lower = result.lower()

                # 处理连接结果
                if "connected to" in result_lower or "already connected" in result_lower:
                    logging.info(f"成功连接至 {self.ip}:{self.port}")
                    self.connected = True
                    return True
                else:
                    logging.warning(f"连接尝试 {attempt + 1}/{self.max_retries} 失败: {result.strip()}")
                    if attempt < self.max_retries:
                        logging.info(f"等待 {self.retry_delay} 秒后重试...")
                        time.sleep(self.retry_delay)
            except Exception as e:
                logging.error(f"连接尝试 {attempt + 1}/{self.max_retries} 出错: {str(e)}")
                if attempt < self.max_retries:
                    logging.info(f"等待 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)

        return False

    def disconnect(self):
        """断开连接"""
        if self.connected:
            try:
                self._run_command(["disconnect", f"{self.ip}:{self.port}"])
                logging.info(f"已断开 {self.ip}:{self.port}")
            except Exception as e:
                logging.error(f"断开连接时出错: {str(e)}")
            finally:
                self.connected = False

    def shell(self, command):
        """执行shell命令"""
        with self.lock:
            if not self.connected:
                logging.warning("尝试重新连接设备...")
                if not self.connect_tcp():
                    raise RuntimeError("无法连接设备")
            return self._run_command(["shell", command])

    def pull(self, remote_path, local_path):
        """拉取文件"""
        with self.lock:
            if not self.connected:
                logging.warning("尝试重新连接设备...")
                if not self.connect_tcp():
                    raise RuntimeError("无法连接设备")
            self._run_command(["pull", remote_path, local_path])
            logging.info(f"文件已拉取: {remote_path} -> {local_path}")

    def push(self, local_path, remote_path):
        """推送文件"""
        with self.lock:
            if not self.connected:
                logging.warning("尝试重新连接设备...")
                if not self.connect_tcp():
                    raise RuntimeError("无法连接设备")
            self._run_command(["push", local_path, remote_path])
            logging.info(f"文件已推送: {local_path} -> {remote_path}")

    def _run_command(self, command):
        """执行底层ADB命令"""
        full_cmd = [self.adb_path, "-s", f"{self.ip}:{self.port}"] + command
        logging.debug(f"执行命令: {' '.join(full_cmd)}")

        try:
            start_time = time.time()
            result = subprocess.run(
                full_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            elapsed = time.time() - start_time
            logging.debug(f"命令执行耗时: {elapsed:.2f}s")

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                raise RuntimeError(f"命令执行失败（{result.returncode}）: {error_msg}")

            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"命令执行异常: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"意外错误: {str(e)}")

