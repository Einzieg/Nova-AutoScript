from core.LogManager import LogManager

WAITING = 0
RUNNING = 1
SUCCESS = 2
FAILED = -1


class TaskBase:
    def __init__(self):
        self.status = WAITING
        self.logging = LogManager()

    async def prepare(self):
        """任务前置操作"""
        self._update_status(WAITING)

    async def execute(self):
        """主执行逻辑（需子类实现）"""
        raise NotImplementedError

    async def cleanup(self):
        """任务后置操作"""
        pass

    def _update_status(self, status):
        """更新任务状态"""
        self.status = status
