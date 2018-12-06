from django.contrib import admin

# Register your models here.
from .models import Schedule


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    pass
