# -*- encoding: utf-8 -*-

import json
import logging
import os
import subprocess
import sys
import time

from django.conf import settings
from django.core.management.base import BaseCommand

import delegator
from app.models import Schedule


def get_process_count(frequency):
    '''
    注意这里根据命令行部分来判断进程是否存在,如果路径改了. 这里也需要修改的.
    '''
    cmd = 'task_file=/opt/node/log/{}.task'.format(frequency)
    new_cmd = 'ps aux |grep -v grep|grep {} | wc -l'.format(cmd)
    print(new_cmd)
    c = delegator.run(new_cmd)
    return int(c.out)


def kill_process(frequency):
    cmd = 'task_file=/opt/node/log/{}.task'.format(frequency)
    new_cmd = "ps aux |grep -v grep|grep %s |awk '{print $2}'|xargs kill -9" % cmd
    print(new_cmd)
    delegator.run(new_cmd)


class BaseCheckCommand(BaseCommand):
    help = '平稳度检查基类'

    def __init__(self, frequency, logger_name):
        super().__init__()
        self.frequency = frequency
        self.logger = logging.getLogger(logger_name)

    def run(self):
        time_flag = time.time()
        log_dir = os.path.join(settings.BASE_DIR, "log")
        task_file = os.path.join(log_dir, '{}.task'.format(self.frequency))
        result_file = os.path.join(log_dir, '{}.result'.format(self.frequency))

        # pylint: disable=no-member
        schedule = Schedule.objects.get(frequency=self.frequency)
        if schedule.status == 'stoped':
            return
        self.logger.info('start schedule: master id is %s, frequency is:%s, status is:%s',
                         schedule.master_schedule_id,
                         schedule.frequency,
                         schedule.status)

        # STEP1: 初始化, 检测僵尸进程以及结果文件是否删除
        if get_process_count(self.frequency) > 0:
            kill_process(self.frequency)
            self.logger.error('{} probe exists, will kill'.format(self.frequency))
        if os.path.exists(result_file):
            os.remove(result_file)

        # STEP2: 下发任务&等待结果
        with open(task_file, 'w') as f:
            f.write(schedule.tasks)

        python = delegator.run('pipenv run which python').out.strip()
        # 这里设置了任务执行脚本最长执行时间为70s
        cmd = "{python} manage.py probe --task_file={task_file} --result_file={result_file} --max_time={max_time}".format(
            python=python,
            task_file=task_file,
            result_file=result_file,
            max_time=70
        )
        self.logger.info('cmd:%s', cmd)
        proc = subprocess.Popen(cmd, shell=True)

        # 当probe执行检测完后或达到超时时间70s的话,就停止并写入结果文件
        check_start_time = time.time()
        while 1:
            flag = os.path.exists(result_file)
            if flag:
                break
            time.sleep(1)
            # 理论上70s左右就会返回.
            if time.time() - check_start_time > 80:
                schedule.status = 'stoped'
                schedule.tasks = json.dumps([])
                schedule.resutls = json.dumps([])
                schedule.save()
                proc.kill()
                kill_process(self.frequency)
                raise Exception('check spent more than 90 sec')
        if proc.poll() is None:
            self.logger.error('process is  running')
            proc.kill()
            kill_process(self.frequency)
            time.sleep(1)
        if proc.poll() is None:
            schedule.status = 'stoped'
            schedule.tasks = json.dumps([])
            schedule.resutls = json.dumps([])
            schedule.save()
            raise Exception('process alive:{}'.format(self.frequency))

        # STEP3: 读取结果,删除结果，写入数据库
        time.sleep(1)
        with open(result_file) as f:
            results = json.loads(f.read())

        os.remove(result_file)

        schedule.status = 'stoped'
        schedule.tasks = json.dumps([])
        schedule.resutls = json.dumps(results)
        schedule.save()
        self.logger.info('end schedule: master id is %s, frequency is:%s time_flag:%s, spent:%s',
                         schedule.master_schedule_id,
                         schedule.frequency,
                         time_flag,
                         time.time() - time_flag)

    def handle(self, *args, **options):
        while 1:
            try:
                self.run()
            except KeyboardInterrupt:
                self.logger.exception("KeyboardInterrupt")
                sys.exit(0)
            except Exception as e:
                self.logger.exception("Exception:%s", e)
            time.sleep(2)
