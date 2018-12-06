# -*- encoding: utf-8 -*-

import requests
import logging
import json
from app.models import Monitor
nodeapi_logger = logging.getLogger('nodeapi')


class NodeApi(object):
    def __init__(self, master_schedule_id, monitor, frequency):
        self.master_schedule_id = master_schedule_id
        self.monitor = monitor
        self.frequency = frequency

        self.url = 'http://{ip}/api/schedules/{frequency}/'.format(
            ip=Monitor.to_dict()[monitor]['ip'],
            frequency=frequency
        )

    def _get_info(self):
        nodeapi_logger.info('begin get node info:%s', self.frequency)
        r = requests.get(self.url, timeout=60)
        result = r.json()
        nodeapi_logger.info('end get node info:%s, status is:%s', self.frequency, r.status_code)
        return result

    def is_idle(self):
        info = self._get_info()
        if info['master_schedule_id'] == 0 and info['status'] == 'stoped':
            return True
        return False

    def is_stoped(self):
        '''
        节点已经完成任务,等待主节点读取数据. 这个函数名不太好.待改进
        返回值 stoped, idle, result
        '''
        info = self._get_info()
        if info['status'] != 'stoped':
            return False, False, info['resutls']

        if info['master_schedule_id'] == 0:
            return False, True, info['resutls']
        else:
            return True, False, info['resutls']

    def reset(self):
        '''
        实际上就是重置状态和主节点调度id.
        这样探针节点就空闲了,可以接受任务了.
        '''
        nodeapi_logger.info('begin reset node, url is:%s', self.url)
        data = {
            'status': 'stoped',
            'master_schedule_id': 0,
            'resutls': json.dumps([])
        }
        r = requests.patch(self.url, data, timeout=60)
        nodeapi_logger.info('status code is:%s', r.status_code)
        assert r.status_code == 200, 'status_code not 200'
        # TODO:需要检测返回码
        nodeapi_logger.info('end reset node')
        return True

    def create(self, tasks):
        '''
        下发任务给探针,实际上就是修改探针的状态和主节点调度id.
        XXX:记着调用前一定得先用is_idle检测
        '''
        nodeapi_logger.info('begin create node, url is:%s', self.url)
        data = {
            'status': 'running',
            'master_schedule_id': self.master_schedule_id,
            'tasks':  json.dumps(tasks)
        }
        r = requests.patch(self.url, data, timeout=60)
        # TODO:需要检测返回码
        nodeapi_logger.info('status code is:%s', r.status_code)
        assert r.status_code == 200, 'status_code not 200'
        nodeapi_logger.info('end create node')
        return True


class NodeStatusApi(object):
    def __init__(self, monitor):
        self.monitor = monitor
        self.url = 'http://{ip}/api/status/'.format(
            ip=Monitor.to_dict()[monitor]['ip']
        )

    def fetch(self):
        r = requests.get(self.url, timeout=60)
        return r.json()
