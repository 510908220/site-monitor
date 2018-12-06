
import json
import logging
import os
import re
import tempfile
from collections import Counter, defaultdict
from concurrent import futures
from urllib.parse import urlparse

import pendulum
import pymongo
from django.conf import settings
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from pendulum import from_timestamp
from pymongo import MongoClient
from rest_framework import filters, permissions, status, viewsets
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from rest_framework.response import Response

import django_filters
from app.constant import TASK_FREQUENCY_LIST
from app.node_api import NodeApi, NodeStatusApi

from . import export as export_utils
from .models import Monitor, Result, Schedule, Task
from .serializers import MonitorSerializer, TaskSerializer

logger = logging.getLogger('app')


class DefaultsMixin(object):
    authentication_classes = (
        SessionAuthentication,
        BasicAuthentication
    )
    permission_classes = (
        permissions.IsAuthenticated,
    )

    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    )


class TaskViewSet(DefaultsMixin, viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class MonitorViewSet(DefaultsMixin, viewsets.ModelViewSet):
    queryset = Monitor.objects.all()
    serializer_class = MonitorSerializer


class ResultViewSet(viewsets.ViewSet):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def retrieve(self, request, pk=None):
        result_obj = get_object_or_404(Result, job_id=pk)
        return Response(json.loads(result_obj.content))

    def list(self, request):
        results = []
        for result_obj in Result.objects.all():
            results.append(
                {
                    'id': result_obj.job_id,
                    'content': json.loads(result_obj.content)
                }
            )
        return Response(results)


class StatisticsViewSet(viewsets.ViewSet):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request):
        data = {
            'http_count': 0,
            'tcp_count': 0,
            'ping_count': 0
        }
        frequency_dict = {frequency: 0 for frequency in TASK_FREQUENCY_LIST}
        for item in Task.objects.all().values('frequency').annotate(total=Count('frequency')).order_by('total'):
            frequency_dict[item['frequency']] = item['total']
        data['frequency_dict'] = frequency_dict

        for item in Task.objects.all().values('task_type').annotate(total=Count('task_type')).order_by('total'):
            key = "_".join([item['task_type'], 'count'])
            data[key] = item['total']
        return Response(data)


class SiteViewSet(viewsets.ViewSet):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get_ss(self, monitor_result):
        availability_counter = Counter()
        average_response_times = []
        update_time = 0
        availability = 0
        average_response_time = 0

        monitor_result_list = []
        for monitor_id, monitor_data in monitor_result.items():
            monitor_result_list.append(monitor_data)
            availability_counter[monitor_data['res']] += 1
            average_response_times.append(float(monitor_data['tim']))
            if not update_time:
                update_time = from_timestamp(int(monitor_data['last_check_time']), 'Asia/Shanghai').to_datetime_string()
        if monitor_result_list:
            availability = format((availability_counter['1'] / sum(availability_counter.values()) * 100), '.2f')
            average_response_time = format(sum(average_response_times) / len(average_response_times), '.2f')
        return {
            'monitor_result_list': monitor_result_list,
            'ok': availability_counter['1'],
            'bad': availability_counter['0'],
            'availability': availability,
            'update_time': update_time,
            'average_response_time': average_response_time
        }

    def retrieve(self, request, pk=None):
        """
        站点监控历史,从mongo里查询.这里先模拟一些数据.
        """
        begin_date = self.request.query_params.get('begin_date')
        end_date = self.request.query_params.get('end_date')
        export = self.request.query_params.get('export')  # 控制是否是导出数据

        if begin_date:
            begin_date = pendulum.parse(begin_date, tz='Asia/Shanghai')
        else:
            # 默认显示近一小时数据
            begin_date = pendulum.now(tz='Asia/Shanghai').subtract(minutes=60)

        if end_date:
            end_date = pendulum.parse(end_date, tz='Asia/Shanghai')
        else:
            end_date = pendulum.now(tz='Asia/Shanghai')

        logger.info('begin get task %s data, begin_date:%s(%s) end_date:%s(%s)',
                    pk,
                    begin_date.to_datetime_string(),
                    begin_date.int_timestamp,
                    end_date.to_datetime_string(),
                    end_date.int_timestamp
                    )

        client = MongoClient(host=settings.MONGO_HOST, port=settings.MONGO_PORT)
        db = client[settings.MONGO_DB]
        records = db.history.find({
            'task_id': int(pk),
            'last_check_time': {
                "$gte": begin_date.int_timestamp,
                "$lte": end_date.int_timestamp
            }
        }, {'_id': False, 'createdAt': False}).sort('last_check_time', pymongo.DESCENDING)

        results = []
        for record in records:
            results.append(self.get_ss(record['nodes']))

        if not export:
            logger.info('end get task %s data', pk)
            return Response(results)

        # 导出数据逻辑
        task = Task.objects.get(pk=pk)
        basic_info = {
            'task_id': task.id,
            'task_type': task.task_type,
            'url': task.url,
            'begin_date': begin_date.to_datetime_string(),
            'end_date': end_date.to_datetime_string()
        }
        domain = urlparse(task.url).netloc
        if ':' in domain:
            domain = '-'.join(domain.split(':'))
        excel_name = '{}_{}_{}'.format(
            task.task_type,
            domain,
            task.id
        )
        with tempfile.TemporaryDirectory() as tmpdirname:
            path = os.path.join(tmpdirname, '{}.xls'.format(excel_name))
            export_utils.excel(basic_info, results, path)
            response = HttpResponse(content_type='application/ms-excel')
            response['Content-Disposition'] = 'attachment; filename="{}.xls"'.format(excel_name)
            response.write(open(path, 'rb').read())
            return response
        logger.info('end get task %s data, with export', pk)

    def list(self, request):
        search_url = self.request.query_params.get('search_url')
        search_task_type = self.request.query_params.get('search_task_type')
        if search_task_type:
            queryset = Task.objects.filter(task_type=search_task_type)
        else:
            queryset = Task.objects.all()

        if search_url:
            queryset = queryset.filter(url__contains=search_url)[:20]
        else:
            queryset = queryset[:20]
        task_dict = {}

        for task in queryset:
            task_dict[task.id] = {
                'task_id': task.id,
                'task_type': task.task_type,
                'frequency': task.frequency,
                'url': task.url,
                'time_out': task.time_out,
                'redirect': task.redirect,
                'monitors': task.monitors
            }

        results = Result.objects.filter(job_id__in=task_dict.keys())
        for result in results:
            monitor_result = json.loads(result.content)
            task_dict[result.job_id].update(self.get_ss(monitor_result))
        return Response(task_dict.values())


class StatusViewSet(viewsets.ViewSet):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (permissions.IsAdminUser,)

    def retrieve(self, request, pk=None):
        frequency = pk
        logger.info('begin api reset %s ', frequency)
        if pk not in TASK_FREQUENCY_LIST:
            return Response('bad ', status=status.HTTP_400_BAD_REQUEST)

        nodes = [NodeApi(0, monitor_id, frequency) for monitor_id in Monitor.get_ids()]
        for node in nodes:
            node.reset()
        logger.info('begin api reset %s ', frequency)
        return Response('ok', status=status.HTTP_200_OK)

    def get_node_status(self, monitor_id):
        status_dict = {}
        try:
            node_api = NodeStatusApi(monitor_id)
            result = node_api.fetch()
            for frequency, data in result.items():
                # 简单格式化一下日期显示
                updated = pendulum.parse(data['updated'], tz='Asia/Shanghai').to_datetime_string()
                value = '{}/{}'.format(data['status'], updated)
                status_dict[frequency] = '{}/{}'.format(monitor_id, value) 
        except:
            status_dict['2'] = '{}/{}'.format(monitor_id, 'bad')
            
            logger.exception('get node %s error', monitor_id)
        return status_dict

    def list(self, request):
        node_status_dict = defaultdict(list)

        with futures.ThreadPoolExecutor(max_workers=10) as executor:
            for future in executor.map(self.get_node_status, Monitor.get_ids()):
                for frequency, value in future.items():
                    node_status_dict[frequency].append(value)

        status_list = []
        for frequency in TASK_FREQUENCY_LIST:
            data = node_status_dict[frequency]
            for item in data:
                status_list.append('/'.join([frequency, item]))

        return Response(status_list)
