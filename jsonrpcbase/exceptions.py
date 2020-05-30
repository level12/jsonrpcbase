"""
Exception classes
"""


class InvalidServerErrorCode(RuntimeError):
    message = "Invalid server error code; must be in the range -32000 to -32099."


class DuplicateMethodName(RuntimeError):

    def __init__(self, name):
        self.name = name
        self.message = f"Duplicate method name for JSON-RPC service: '{self.name}'"
        super().__init__(self.message)

    def __str__(self):
        return self.message
