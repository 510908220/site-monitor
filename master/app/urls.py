# -*- encoding: utf-8 -*-
from rest_framework import routers

from . import views

router = routers.DefaultRouter()  # DefaultRouter会生成rootview

router.register(r'tasks', views.TaskViewSet)
router.register(r'monitors', views.MonitorViewSet)
router.register(r'results', views.ResultViewSet, 'result')
router.register(r'statistics', views.StatisticsViewSet, 'statistics')
router.register(r'sites', views.SiteViewSet, 'sites')
router.register(r'status', views.StatusViewSet, 'status')