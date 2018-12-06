from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Task, Result, Monitor


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    pass


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    pass


@admin.register(Monitor)
class MonitorAdmin(admin.ModelAdmin):
    pass
