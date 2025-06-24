class NovaException(Exception):
    def __init__(self, message="Nova"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class TaskFinishes(Exception):
    def __init__(self, message="任务结束"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class RadarFinishes(TaskFinishes):
    def __init__(self, message="雷达结束"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message
