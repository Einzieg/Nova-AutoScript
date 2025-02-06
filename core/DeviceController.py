import threading
import time
import logging


class DeviceController(threading.Thread):
    def __init__(self, device_name, log_callback):
        super().__init__()
        self.device_name = device_name
        self.log_callback = log_callback  # 日志回调函数
        self._stop_event = threading.Event()  # 线程停止标志

    def run(self):
        """线程运行逻辑"""
        self.log_callback(f"设备 {self.device_name} 启动中...")
        while not self._stop_event.is_set():
            # 模拟设备运行
            self.log_callback(f"设备 {self.device_name} 运行中...")
            time.sleep(1)
        self.log_callback(f"设备 {self.device_name} 已停止")

    def stop(self):
        """停止线程"""
        self._stop_event.set()
