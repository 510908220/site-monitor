# -*- encoding: utf-8 -*-

import json
import logging
import sys
import time
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from app.models import Check
from utils import check as check_

logger = logging.getLogger('single_check')


CHECK_FUN_MAP = {
    'http': check_.http_check_ex,
    'ping': check_.ping_check,
    'tcp': check_.tcp_check,
    'dig': check_.dig_check
}


def do_check():
    # STEP1 删除2小时前的检查记录
    two_hour_ago = datetime.today() - timedelta(hours=2)
    # pylint: disable=no-member
    Check.objects.filter(created__lte=two_hour_ago).delete()

    # STEP2 获取所有状态为running的检查任务
    # pylint: disable=no-member
    checks = Check.objects.filter(status='running')
    for check in checks:
        logger.info('begin check %s, tp is %s', check.url, check.tp)
        func = CHECK_FUN_MAP[check.tp]
        resut = func(check.url)
        # 本来写result了,写错了.凑活着用把
        check.resut = json.dumps(resut)
        check.status = 'stoped'
        check.save()
        logger.info('end check %s, tp is %s', check.url, check.tp)


class Command(BaseCommand):
    help = '平稳度检查基类'

    def handle(self, *args, **options):
        while 1:
            try:
                do_check()
            except KeyboardInterrupt:
                logger.exception("KeyboardInterrupt")
                sys.exit(0)
            except Exception as e:
                logger.exception("Exception:%s", e)
            time.sleep(5)
