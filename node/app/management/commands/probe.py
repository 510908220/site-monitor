# -*- encoding: utf-8 -*-

'''
探针检测程序
'''
import json
import time
from concurrent import futures

import requests
from django.core.management.base import BaseCommand

from utils import check

requests.packages.urllib3.disable_warnings()

MAX_WORKERS = 3000

CHECK_FUN_MAP = {
    'http': check.http_check,
    'ping': check.ping_check,
    'tcp': check.tcp_check
}
HTTP_METHOD_MAP = {
    '0': 'get',
    '1': 'post',
    '2': 'head'
}


def get_max_workers(task_count):
    if task_count > MAX_WORKERS:
        return MAX_WORKERS
    return task_count


def build_params(task):
    task_type = task['task_type']
    url = task['url']
    args = ()
    kwargs = {}
    if task_type == 'http':
        args = (url,)
        kwargs = {'useragent': task['header'],
                  'method': HTTP_METHOD_MAP[task['submit_method']],
                  'retry': task['retry'],
                  'timeout': task['time_out'],
                  'data': None,
                  'is_301': task['redirect']}

    elif task_type == 'ping':
        args = (url,)
    elif task_type == 'tcp':
        url, port = url.split(':')
        args = (url, port)
    return args, kwargs


def process_one(task):
    fun = CHECK_FUN_MAP[task['task_type']]
    args, kwargs = build_params(task)
    ret = fun(*args, **kwargs)
    ret.update({
        'task_id': task['id']
    })
    return ret


def get_default_result(task):
    task_type = task['task_type']
    if task_type == 'http':
        ret = {'res': '0', 'sta': 'Read-timed-out', 'tim': 0, 'task_id': task['id']}
    elif task_type == 'ping':
        ret = {"res": '0', "tim": 0, "sta": 'PING-LOSS', "loss": 100, 'task_id': task['id']}
    else:
        ret = {'res': '0', 'tim': 0, 'sta': 'TCP-CONNECT-ERR', 'task_id': task['id']}
    return ret


def run(task_file, result_file, max_time=80):
    begin_time = time.time()
    # 获取任务
    tasks = []
    with open(task_file) as f:
        tasks = json.loads(f.read())
    # 创建future
    task_count = len(tasks)
    max_workers = get_max_workers(task_count)
    executor = futures.ThreadPoolExecutor(max_workers=max_workers)
    future_checks = []
    try:
        for task in tasks:
            future_checks.append(executor.submit(process_one, task))
    except Exception as e:
        print(e)

    # 目前用线上2400左右各站点测试, 这一步耗时在9s~20s左右
    submit_spent = time.time() - begin_time
    if submit_spent >= 30:
        print('{} submit spent {}'.format(task_file, submit_spent))

    # 等待任务结束或直到超时
    while time.time() - begin_time < max_time:
        print('wait ....')
        time.sleep(1)
    finished = []
    running_count = 0
    for future_check in future_checks:
        if future_check.done():
            finished.append(future_check.result())
            continue
        running_count += 1

    finished_task_ids = [result['task_id'] for result in finished]

    for task in tasks:
        if task['id'] in finished_task_ids:
            continue
        finished.append(
            get_default_result(task)
        )

    with open(result_file, 'w') as f:
        f.write(json.dumps(finished))

    with open(task_file + '.submit', 'a') as f:
        f.write("submit:{}, spent:{}, task count:{}, result count:{}, running:{}\n".format(
            submit_spent,
            time.time() - begin_time,
            len(tasks),
            len(finished),
            running_count))

    executor.shutdown(wait=False)


class Command(BaseCommand):
    help = '平稳度检查脚本'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task_file', dest='task_file', required=True,
            help='the task_file to process',
        )
        parser.add_argument(
            '--result_file', dest='result_file', required=True,
            help='result_file',
        )
        parser.add_argument(
            '--max_time', dest='max_time', required=True,
            help='max_time',
        )

    def handle(self, *args, **options):
        run(
            options['task_file'],
            options['result_file'],
            int(options['max_time']),
        )
