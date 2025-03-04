import asyncio
import logging
from datetime import datetime

from core.LogManager import LogManager


class MainProcess:

    def __init__(self, target):
        self.target = target
        self.logging = LogManager(logging.DEBUG)
        self.logging.log(f"MainProcess init {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" + str(target), target)

    async def run(self):
        while True:
            try:
                self.logging.log(f"MainProcess run {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} " + str(self.target), self.target)
                await asyncio.sleep(3)  # 非阻塞延时
            except asyncio.CancelledError:
                print(f"MainProcess for {self.target} is stopping.")
                break
