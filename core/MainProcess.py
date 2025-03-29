import asyncio
import logging
from datetime import datetime

from core.LogManager import LogManager
from core.NovaException import TaskFinishes


class MainProcess:

    def __init__(self, gui_app, target):
        self.target = target
        self.app = gui_app
        self.logging = LogManager(logging.DEBUG)
        self.logging.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 任务 [{self.target}] 初始化", target)

    async def run(self):
        while True:
            try:
                self.logging.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 任务 [{self.target}] 执行", self.target)
                await asyncio.sleep(3)
                raise TaskFinishes("任务完成")
            except asyncio.CancelledError:
                self.logging.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 任务 [{self.target}] 停止", self.target)
                break
            except TaskFinishes as e:
                self.logging.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 任务 [{self.target}] 执行完成: {e}", self.target)
                self.app.stop(self.target)
                break
            except Exception as e:
                self.logging.log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 任务 [{self.target}] 执行异常: {e}", self.target)
                self.app.stop(self.target)
                break
