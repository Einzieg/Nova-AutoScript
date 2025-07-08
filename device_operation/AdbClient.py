import asyncio
import logging
import os
import re
import subprocess
import time
import sys
from threading import Lock

from core.LogManager import LogManager


class AdbClient:
    def __init__(self, name, ip="127.0.0.1", port=5555, adb_path=None, max_retries=3, retry_delay=2):
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
        self.name = name
        self.logging = LogManager()
        self.lock = Lock()  # 确保命令唯一执行
        if adb_path is None:
            self.adb_path = self.get_adb_path()
        else:
            self.adb_path = adb_path
            if not os.path.exists(self.adb_path):
                raise FileNotFoundError(f"ADB路径 {self.adb_path} 不存在")

    def get_adb_path(self):
        possible_adb_paths = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Android", "Sdk", "platform-tools"),
            os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local", "Android", "Sdk", "platform-tools"),
            os.path.join(os.environ.get("ProgramFiles", ""), "Android", "platform-tools"),
        ]
        for path in possible_adb_paths:
            if os.path.exists(os.path.join(path, "adb.exe")):
                return os.path.join(path, "adb.exe")

        try:
            # 执行 adb version 命令
            result = subprocess.run(
                ["adb", "version"],
                capture_output=True,
                text=True,
                check=True
            )
            match = re.search(r"Installed as (.+)$", result.stdout, re.MULTILINE)

            if match:
                return match.group(1).strip()
            else:
                return None
        except Exception as e:
            self.logging.log(f"adb version 命令执行失败: {e}", self.name, logging.ERROR)

        for path in os.environ["PATH"].split(";"):
            if os.path.exists(os.path.join(path, "adb.exe")):
                return os.path.join(path, "adb.exe")

    async def connect_tcp(self):
        """建立TCP连接"""
        for attempt in range(self.max_retries):
            if self.connected:
                self.logging.log("已连接，跳过重复连接", self.name, logging.DEBUG)
                return True
            if not self.ip:
                raise ValueError("IP地址不能为空")

            command = ["connect", f"{self.ip}:{self.port}"]
            try:
                result = await self._run_command(command)
                result_lower = result.lower()

                # 处理连接结果
                if "connected to" in result_lower or "already connected" in result_lower:
                    self.logging.log(f"成功连接至 {self.ip}:{self.port}", self.name, logging.INFO)
                    self.connected = True
                    return True
                else:
                    self.logging.log(f"连接尝试 {attempt + 1}/{self.max_retries} 失败: {result.strip()}", self.name, logging.WARNING)
                    if attempt < self.max_retries:
                        self.logging.log(f"等待 {self.retry_delay} 秒后重试...", self.name, logging.INFO)
                        await asyncio.sleep(self.retry_delay)
            except Exception as e:
                self.logging.log(f"连接尝试 {attempt + 1}/{self.max_retries} 出错: {str(e)}", self.name, logging.ERROR)
                if attempt < self.max_retries:
                    self.logging.log(f"等待 {self.retry_delay} 秒后重试...", self.name, logging.INFO)
                    await asyncio.sleep(self.retry_delay)

        return False

    def disconnect(self):
        """断开连接"""
        if self.connected:
            try:
                self._run_command(["disconnect", f"{self.ip}:{self.port}"])
                self.logging.log(f"已断开 {self.ip}:{self.port}", self.name, logging.INFO)
            except Exception as e:
                self.logging.log(f"断开连接时出错: {str(e)}", self.name, logging.ERROR)
            finally:
                self.connected = False

    async def shell(self, command):
        """执行shell命令"""
        with self.lock:
            if not self.connected:
                self.logging.log("尝试重新连接设备...", self.name, logging.WARNING)
                if not self.connect_tcp():
                    raise RuntimeError("无法连接设备")
            return await self._run_command(["shell", command])

    async def pull(self, remote_path, local_path):
        """拉取文件"""
        with self.lock:
            if not self.connected:
                self.logging.log("尝试重新连接设备...", self.name, logging.WARNING)
                if not self.connect_tcp():
                    raise RuntimeError("无法连接设备")
            await self._run_command(["pull", remote_path, local_path])
            self.logging.log(f"文件已拉取: {remote_path} -> {local_path}", self.name, logging.DEBUG)

    async def push(self, local_path, remote_path):
        """推送文件"""
        with self.lock:
            if not self.connected:
                self.logging.log("尝试重新连接设备...", self.name, logging.WARNING)
                if not self.connect_tcp():
                    raise RuntimeError("无法连接设备")
            await self._run_command(["push", local_path, remote_path])
            self.logging.log(f"文件已推送: {local_path} -> {remote_path}", self.name, logging.DEBUG)

    async def _run_command(self, command):
        """执行底层ADB命令"""
        full_cmd = [self.adb_path, "-s", f"{self.ip}:{self.port}"] + command
        cmd_str = ' '.join(full_cmd)
        self.logging.log(f"执行命令: {cmd_str}", self.name, logging.DEBUG)

        try:
            start_time = time.time()
            if sys.platform != 'darwin':
                process = await asyncio.create_subprocess_exec(
                    *full_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=None,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    *full_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    stdin=None
                )

            try:
                stdout, stderr = await process.communicate()
            except asyncio.TimeoutError:
                process.kill()
                raise TimeoutError(f"命令执行超时: {cmd_str}")

            elapsed = time.time() - start_time
            self.logging.log(f"命令执行耗时: {elapsed:.2f}s", self.name, logging.DEBUG)

            stdout_decoded = (stdout or b'').decode('utf-8', errors='replace').strip()
            stderr_decoded = (stderr or b'').decode('utf-8', errors='replace').strip()

            if process.returncode != 0:
                error_msg = stderr_decoded or stdout_decoded
                raise RuntimeError(f"命令执行失败（{process.returncode}）: {error_msg}")

            return stdout_decoded

        except Exception as e:
            raise RuntimeError(f"命令执行异常: {str(e)}")

    @staticmethod
    def get_device_id_by_port(port):
        """根据端口号获取ADB设备ID"""
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if f":{port}" in line:
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] == "device":
                    return parts[0]
        return None
