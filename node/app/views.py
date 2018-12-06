# -*- encoding: utf-8 -*-
import logging

# Create your views here.
import django_filters

from rest_framework.response import Response
from rest_framework import (filters,
                            viewsets)

from .models import Schedule, Check
from .serializers import ScheduleSerializer, CheckSerializer

logger = logging.getLogger('app')


class DefaultsMixin(object):
    # authentication_classes = (
    #     authentication.BasicAuthentication,
    #     authentication.TokenAuthentication
    # )
    # permission_classes = (
    #     permissions.IsAuthenticated,
    # )

    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    )


class ScheduleViewSet(DefaultsMixin, viewsets.ModelViewSet):
    # pylint: disable=no-member
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    filter_fields = ('frequency',)


class StatusViewSet(viewsets.ViewSet):
    # pylint: disable=unused-argument
    def list(self, request):
        node_status_dict = {}
        # pylint: disable=no-member
        for shedule in Schedule.objects.values('frequency', 'master_schedule_id', 'status', 'updated', 'created'):
            node_status = ''
            if shedule['status'] == 'running':
                node_status = '运行'
            else:
                if shedule['master_schedule_id'] == 0:
                    node_status = '空闲'
                else:
                    node_status = '执行完毕'
            node_status_dict[shedule['frequency']] = {
                'status': node_status,
                'created': shedule['created'],
                'updated': shedule['updated']
            }
        return Response(node_status_dict)


class CheckViewSet(DefaultsMixin, viewsets.ModelViewSet):
    # pylint: disable=no-member
    queryset = Check.objects.all()
    serializer_class = CheckSerializer
