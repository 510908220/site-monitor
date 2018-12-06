# -*- encoding: utf-8 -*-

import os
from .base_dispatcher import BaseDispatcherCommand


LOGGER_NAME = __name__.split(".")[-1]
FREQUENCY = LOGGER_NAME.split('_')[0]


class Command(BaseDispatcherCommand):
    help = '平稳度检查基类'

    def __init__(self):
        super().__init__(FREQUENCY, LOGGER_NAME)
