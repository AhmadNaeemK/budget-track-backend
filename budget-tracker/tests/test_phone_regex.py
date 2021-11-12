import re

import django
django.setup()

from accounts import models

import pytest


def test_phone_regex():
    assert re.match(models.phone_regex.regex, '+923089058725')
    # tests "+" at beginning of phone string
    assert re.match(models.phone_regex.regex, '923089058725') is None
    # tests length of phone string
    assert re.match(models.phone_regex.regex, '923') is None
