class ErrorWithReturn(Exception):
    def __init__(self, message, return_value):
        super().__init__(message)
        self.return_value = return_value
