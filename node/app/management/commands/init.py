# -*- encoding: utf-8 -*-

import logging

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import Schedule
from app.constant import TASK_FREQUENCY_LIST

logger = logging.getLogger("app")


class Command(BaseCommand):
    help = '数据初始化'

    def handle(self, *args, **options):
        logger.info('begin init')
        # 创建不同频率的检测
        for frequency in TASK_FREQUENCY_LIST:
            logger.info('create frequency:%s', frequency)
            # pylint: disable=no-member
            Schedule.objects.get_or_create(frequency=frequency)
        # 创建管理员密码
        if not User.objects.filter(email='admin@example.com'):
            User.objects.create_superuser('admin', 'admin@example.com', '管理员密码')
        logger.info('end init')
