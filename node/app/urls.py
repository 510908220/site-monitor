# -*- encoding: utf-8 -*-
from rest_framework import routers

from . import views

router = routers.DefaultRouter()  # DefaultRouter会生成rootview

router.register(r'schedules', views.ScheduleViewSet)
router.register(r'status', views.StatusViewSet, 'status')
router.register(r'checks', views.CheckViewSet, 'checks')
