from core.task.TaskBase import *


class DailyTest(TaskBase):

    def __init__(self, target):
        super().__init__(target)
        self.name = 'DailyTest'
        self.target = target

    async def execute(self):
        self._update_status(RUNNING)
        try:
            self.logging.log('DailyTest Starting...', self.target)
            self.logging.log('DailyTest Finished.', self.target)
            self._update_status(SUCCESS)
        except Exception as e:
            self.logging.log('DailyTest Failed.', self.target)
            self._update_status(FAILED)
            raise e
