# -*- encoding: utf-8 -*-

import os
import datetime
import json
import logging
import sys
import threading
import time
from collections import defaultdict
from concurrent import futures
from functools import partial

import schedule
from django.conf import settings
from django.core.management.base import BaseCommand
from pymongo import MongoClient

from app.constant import TASK_FREQUENCY_LIST
from app.models import Monitor, Result, Schedule, Task
from app.node_api import NodeApi


class BaseDispatcherCommand(BaseCommand):
    help = '任务发布器'

    def __init__(self, frequency, logger_name):
        self.frequency = frequency
        self.logger = logging.getLogger(logger_name)
        self.client = MongoClient(host=settings.MONGO_HOST,
                                  port=settings.MONGO_PORT)
        self.db = self.client[settings.MONGO_DB]

    def save_to_mongo(self, records):
        self.logger.info('before save, count is %s',  self.db['history'].count())
        self.db['history'].insert_many(records)
        self.logger.info('after save, count is %s',  self.db['history'].count())

    def get_monitor_task_dict(self, frequency):
        # TODO: 慢的话考虑放缓存
        monitor_task_dict = defaultdict(lambda: [])
        tasks = Task.objects.filter(frequency=frequency).values(
            'id',
            'task_type',
            'url',
            'header',
            'submit_method',
            'retry',
            'time_out',
            'redirect',
            'monitors'
        )
        for task in tasks:
            monitors = task['monitors'].split(",")
            for monitor in monitors:
                monitor_task_dict[monitor].append(task)
        return monitor_task_dict

    def create_task(self, param):
        node_api = param[0]
        tasks = param[1]
        try:
            node_api.create(tasks)
        except Exception as e:
            self.logger.exception("node %s has exception on create", node_api.monitor)

    def run(self, frequency):
        self.logger.info('begin %s schedule', frequency)

        # STEP1: 看是否有任务正在调度
        # 原来根据status判断调度是否运行,现在放在独立的进程里了。所以不需要用了.
        s = Schedule.objects.get(frequency=frequency)

        # STEP2: 获取响应频率的任务
        monitor_task_dict = self.get_monitor_task_dict(frequency)
        if not monitor_task_dict:
            self.logger.warning('frequency:%s has not task', frequency)
            return

        if settings.DEBUG:
            self.logger.info('monitor task is:%s', json.dumps(monitor_task_dict))

        # STEP3:创建监测点接口
        node_dict = {monitor: NodeApi(s.id, monitor, frequency) for monitor in monitor_task_dict.keys()}

        # STEP4: 给各个监测点下发任务
        self.logger.info('begin create tasks')
        node_tasks = []
        for monitor, tasks in monitor_task_dict.items():
            node_tasks.append((node_dict[monitor], tasks))

        with futures.ThreadPoolExecutor(max_workers=len(node_tasks)) as executor:
            for future in executor.map(self.create_task, node_tasks):
                pass
        self.logger.info('end create tasks')

        # STEP5: 等待结果
        task_result_list = defaultdict(lambda: {})
        last_check_time = str(int(time.time()))
        for node_id, node in node_dict.items():
            begin_time = time.time()
            while 1:
                try:
                    # 出现过这一步是idle状态,导致一直死等.改进is_stoped返回idle状态
                    stoped, idle, json_results = node.is_stoped()
                except Exception as e:
                    self.logger.exception("node %s has exception on is_stoped", node.url)
                    stoped, idle, json_results = True, True, "[]"
                if stoped:
                    self.logger.info('node %s finished', node.url)
                    break
                if idle:
                    self.logger.error('node %s finished, but is idle status', node.url)
                    break
                self.logger.warning('node %s is not stop, wait 3 second', node.url)
                time.sleep(3)

                if time.time() - begin_time > 100:
                    self.logger.error("node {} get result has spent 100s".format(node.url))
                    stoped, idle, json_results = True, True, "[]"
                    break

            results = json.loads(json_results)
            monitor_name = Monitor.to_dict()[node.monitor]['name']

            # 构造为类似监控宝的结果
            for result in results:
                task_id = result.pop('task_id')
                result.update({
                    'last_check_time': last_check_time,
                    'monitor_name': monitor_name
                })
                task_result_list[task_id][node.monitor] = result

        if settings.DEBUG:
            self.logger.info('merge frequency: %s result is:%s', frequency, json.dumps(task_result_list))
        # STEP6: 入库mysql && 存到mongo
        # TODO: 任务多的话这里会调用很多次数据插入,是否会有性能问题呢
        self.logger.info('begin save to db')
        mongo_datas = []
        for task_id in task_result_list:
            result_obj, _ = Result.objects.get_or_create(job_id=task_id)
            result_obj.content = json.dumps(task_result_list[task_id])
            result_obj.save()
            mongo_datas.append({
                'createdAt': datetime.datetime.utcnow(),
                'last_check_time': int(last_check_time),
                'task_id': int(task_id),
                'nodes': task_result_list[task_id]
            })
        self.logger.info('end save to db')

        self.logger.info('begin save to mongo')
        self.save_to_mongo(mongo_datas)
        self.logger.info('end save to mongo')

        # STEP7: 重置监测点频率状态
        self.logger.info('bein reset node %s', frequency)
        for node in node_dict.values():
            try:
                node.reset()
            except Exception as e:
                self.logger.exception("node %s has exception on reset", node.url)
                continue

        self.logger.info('end reset node %s', frequency)
        self.logger.info('end %s schedule', frequency)

    def handle(self, *args, **options):
        while 1:
            # XXX: 因为程序本身会消耗一定时间,所以按照频率检测
            # 间隔不是很准确. 可以调整睡眠时间解决
            time.sleep(int(self.frequency) * 60 - 60)

            try:
                self.run(self.frequency)
            except KeyboardInterrupt:
                self.logger.exception("KeyboardInterrupt")
                sys.exit(0)
            except Exception as e:
                self.logger.exception("Exception:%s", e)
