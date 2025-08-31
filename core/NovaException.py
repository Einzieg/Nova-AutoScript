class NovaException(Exception):
    def __init__(self, message="Nova"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class TaskFinishes(NovaException):
    def __init__(self, message="任务结束"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class RadarFinishes(NovaException):
    def __init__(self, message="雷达结束"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class OrderFinishes(NovaException):
    def __init__(self, message="订单结束"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message
    

class PermPirateFinishes(NovaException):
    def __init__(self, message="常驻海盗结束"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message