# encoding: utf-8

from __future__ import unicode_literals

import io
import logging

import pytest


class SimpleFormatter(object):
    def format(self, record):
        message = record.getMessage()
        if isinstance(message, bytes):
            message = message.decode('utf-8')
        return message


@pytest.yield_fixture
def captured_log():
    buff = io.StringIO()
    handler = logging.StreamHandler(buff)
    handler.setFormatter(SimpleFormatter())

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    yield buff

    logger.handlers.remove(handler)
