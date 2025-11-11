import asyncio
import json
import logging
import traceback

from core.LogManager import LogManager
from core.NovaException import NovaException
from core.task.daily_tasks.Order import Order
from core.task.daily_tasks.Radar import Radar
from core.task.permanent_tasks.Permanent import Permanent
from core.task.permanent_tasks.Start import Start
from models import Module


class MainProcess:

    def __init__(self, gui_app, target):
        self.target = target
        self.app = gui_app
        self.tasks = []
        self.logging = LogManager()
        self.module = Module.get(Module.name == target)
        self.logging.log(f"线程 [{self.target}] 初始化", target)

    async def run(self):
        # TODO 一键多线程启动 一键修改配置
        try:
            tasks = json.loads(self.module.task_type)
        except json.JSONDecodeError:
            tasks = []

        self.tasks.append(Start(self.target))

        task_handlers = {
            "outer": self._handle_outer_task,
            "events": self._handle_events_task,
            "daily": self._handle_daily_task
        }

        for task in tasks:
            if task in task_handlers:
                task_handlers[task]()
        if "permanent" in tasks:
            self.tasks.append(Permanent(self.target))
        await self.start()

    def _handle_outer_task(self):
        if self.module.hidden_switch:
            self.tasks.append(Radar(self.target))
        if self.module.order_switch:
            self.tasks.append(Order(self.target))

    def _handle_events_task(self):
        # TODO 活动任务
        pass

    def _handle_daily_task(self):
        # TODO 每日任务
        pass

    async def quick_run(self, task):
        self.tasks = [
            Start(self.target, True)
        ]
        self.tasks.append(task(self.target))
        await self.start()

    async def start(self):
        self.logging.clear_logs(self.target)
        try:
            for task in self.tasks:
                await task.prepare()
                await task.execute()
                await task.cleanup()

            await asyncio.sleep(3)
            self.logging.log(f"线程 [{self.target}] 执行结束", self.target)
            self.app.stop(self.target)
            # TODO 邮件结束通知
        except asyncio.CancelledError:
            self.logging.log(f"线程 [{self.target}] 停止", self.target)
        except NovaException as e:
            self.logging.log(f"线程 [{self.target}] 停止: {e}", self.target)
            self.app.stop(self.target)
        except Exception as e:
            self.logging.log(f"线程 [{self.target}] 执行异常: {e}", self.target, logging.ERROR)
            self.logging.log(traceback.format_exc(), self.target, logging.ERROR)
            self.app.stop(self.target)
