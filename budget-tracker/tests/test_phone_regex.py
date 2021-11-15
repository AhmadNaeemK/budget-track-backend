import re

from accounts import models

import pytest

test_data = [
    ('+923089058725', True),
    ('921564323412', False),
    ('3214', False)
]


@pytest.mark.parametrize('phone_num,expected', test_data)
def test_phone_regex(phone_num, expected):
    assert (re.match(models.phone_regex.regex, phone_num) is not None) is expected
