import pytest

from .utils import TransactionUtils
from .models import TransactionCategories

test_data = [
    (0, 20, TransactionCategories.Income.value, 20),
    (20, 20, TransactionCategories.Income.value, 40),
    (60, 10, TransactionCategories.Drink.value, 50)
]


@pytest.mark.parametrize('prev_balance,amount,category,expected', test_data)
def test_new_account_balance(prev_balance, amount, category, expected):
    assert TransactionUtils().get_new_account_balance(prev_balance, amount, category) == expected
