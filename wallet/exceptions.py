""" Exceptions module for custom exceptions """


class AccountBalanceLimitException(Exception):
    """Exception raised when cash account of user does not have enough cash"""

    def __init__(self, username):
        super().__init__()
        self.username = username

    def __str__(self):
        return f'Cash Account of {self.username} does not have enough amount'
