class TaskFinishes(Exception):
    def __init__(self, message="Task finishes"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message
