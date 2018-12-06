# -*- coding: utf-8 -*-

import os
import json
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.base import TemplateView
from app.models import Task


def login_user(request):
    logout(request)
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/')
    return render(request, "registration/login.html")


class DashboardView(TemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        context['title'] = "仪表盘"
        return context


class MonitorView(TemplateView):
    template_name = "monitor/monitor.html"

    def get_context_data(self, **kwargs):
        context = super(MonitorView, self).get_context_data(**kwargs)
        context['title'] = "探针管理"
        return context


class StatusView(TemplateView):
    template_name = "monitor/status.html"

    def get_context_data(self, **kwargs):
        context = super(StatusView, self).get_context_data(**kwargs)
        context['title'] = "探针状态"
        return context


class SiteView(TemplateView):
    template_name = "site_monitor/site.html"

    def get_context_data(self, **kwargs):
        context = super(SiteView, self).get_context_data(**kwargs)
        context['title'] = "网站监控"

        return context


class SiteItemView(TemplateView):
    template_name = "site_monitor/site_item.html"

    def get_context_data(self, **kwargs):
        task = Task.objects.get(**kwargs)
        context = super(SiteItemView, self).get_context_data(**kwargs)
        context['title'] = "历史监控数据"
        context['task_id'] = task.id
        context['task_type'] = task.task_type
        context['url'] = task.url
        context['frequency'] = task.frequency
        return context
