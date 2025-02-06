import logging
import os
import subprocess
import sys
import time


class AdbClient:
    def __init__(self, ip=None, port=5555, adb_path=None):
        """
        初始化AdbClient实例。
        :param ip: 设备IP地址，默认为None，如果提供IP则通过TCP连接设备。
        :param port: 设备端口号，默认为5555。
        """
        self.ip = ip
        self.port = port
        if adb_path is None:
            # 如果 adb_path 未提供，则使用当前工作目录下的相对路径
            if getattr(sys, 'frozen', False):
                # 如果是打包的环境
                base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))  # 获取打包后的临时目录
            else:
                base_path = os.getcwd()  # 否则使用当前工作目录
            self.adb_path = os.path.join(base_path, 'static/platform-tools', 'adb.exe')
        else:
            self.adb_path = adb_path
        if ip:
            self.connect_tcp()

    def connect_tcp(self):
        """
        通过TCP连接到设备。
        """
        command = f"connect {self.ip}:{self.port}"
        result = self._run_command(command)
        if result is not None and "connected to" in result:
            logging.info(f"已成功连接到 {self.ip}:{self.port}")
        else:
            raise ConnectionError(f"无法连接到 {self.ip}:{self.port}: {result}")

    def disconnect(self):
        """
        断开与设备的连接。
        """
        if self.ip:
            command = f"disconnect {self.ip}:{self.port}"
            self._run_command(command)
            logging.debug(f"断开连接 {self.ip}:{self.port}")

    def shell(self, command):
        """
        在设备上执行shell命令。
        :param command: 要执行的shell命令。
        :return: 命令输出结果。
        """
        command = f"shell {command}"
        return self._run_command(command)

    def pull(self, remote_path, local_path):
        """
        从设备拉取文件到本地。
        :param remote_path: 设备上的文件路径。
        :param local_path: 本地保存路径。
        """
        command = f"pull {remote_path} {local_path}"
        self._run_command(command)
        logging.debug(f"已拉取 {remote_path} 至 {local_path}")

    def push(self, local_path, remote_path):
        """
        推送文件到设备。
        :param local_path: 本地文件路径。
        :param remote_path: 设备上的保存路径。
        """
        command = f"push {local_path} {remote_path}"
        self._run_command(command)
        logging.debug(f"推送 {local_path} 至 {remote_path}")

    def _run_command(self, command):
        """
        运行系统命令并返回结果。
        :param command: 要执行的系统命令。
        :return: 命令的输出结果。
        """
        full_command = f"{self.adb_path} -s {self.ip}:{self.port} {command}"
        logging.debug(f"运行命令: {full_command}")
        try:
            time_start = time.time()
            result = subprocess.run(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            logging.debug(f"执行耗时: {time.time() - time_start}")
            if result.returncode != 0:
                raise RuntimeError(f"命令失败并出现错误: {result}")
            return result.stdout
        except Exception as e:
            raise RuntimeError(f"无法运行命令 '{command}': {str(e)}")

# if __name__ == "__main__":
#     adb = AdbClient(ip="192.168.1.100")  # TCP连接设备
#     print(adb.shell("ls /sdcard"))  # 执行shell命令
#     adb.pull("/sdcard/test.txt", "./test.txt")  # 从设备拉取文件
#     adb.push("./local_file.txt", "/sdcard/remote_file.txt")  # 推送文件到设备
#     adb.disconnect()  # 断开连接
