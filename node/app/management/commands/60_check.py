# -*- encoding: utf-8 -*-

from .base_check import BaseCheckCommand


LOGGER_NAME = __name__.split(".")[-1]
FREQUENCY = LOGGER_NAME.split('_')[0]


class Command(BaseCheckCommand):
    help = '平稳度检查基类'

    def __init__(self):
        super().__init__(FREQUENCY, LOGGER_NAME)
