# -*- encoding: utf-8 -*-

from django.urls import path

from .views import DashboardView, MonitorView,StatusView, SiteView, SiteItemView
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('', login_required(DashboardView.as_view()), name='dashboard'),
    path('monitor/', login_required(MonitorView.as_view()), name='monitor-view'),
    path('status/', login_required(StatusView.as_view()), name='status-view'),
    path('site/', login_required(SiteView.as_view()), name='site-view'),
    path('site/<int:id>/', login_required(SiteItemView.as_view()), name='site-item-view'),
]
