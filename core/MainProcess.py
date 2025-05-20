import asyncio

from core.LogManager import LogManager
from core.NovaException import TaskFinishes
from core.task.daily_tasks.DailyTest import DailyTest
from core.task.outer_tasks.BlessingFlip import BlessingFlip
from core.task.permanent_tasks.Permanent import Permanent


class MainProcess:

    def __init__(self, gui_app, target):
        self.target = target
        self.app = gui_app
        self.tasks = []
        self.logging = LogManager()
        self.logging.log(f"任务 [{self.target}] 初始化", target)

    async def run(self):
        self.load_tasks()
        try:
            for task in self.tasks:
                await task.prepare()
                await task.execute()
                await task.cleanup()

            await asyncio.sleep(3)
            self.logging.log(f"任务 [{self.target}] 执行结束", self.target)
            self.app.stop(self.target)
        except asyncio.CancelledError:
            self.logging.log(f"任务 [{self.target}] 停止", self.target)
        except TaskFinishes as e:
            self.logging.log(f"任务 [{self.target}] 执行完成: {e}", self.target)
            self.app.stop(self.target)
        except Exception as e:
            self.logging.log(f"任务 [{self.target}] 执行异常: {e}", self.target)
            self.app.stop(self.target)

    def load_tasks(self):
        self.tasks = [
            # DailyTest(self.target),
            BlessingFlip(self.target),
            # Permanent(self.target),
        ]
