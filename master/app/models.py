from django.db import models
from django.conf import settings
import re
import socket

# Create your models here.


def valid_ip(address):
    try:
        socket.inet_aton(address)
        return True
    except:
        return False


class BaseModel(models.Model):
    class Meta:
        abstract = True  # Set this model as Abstract
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class Monitor(BaseModel):
    class Meta:
        db_table = 'monitor'
    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    ip = models.CharField(max_length=255)

    @classmethod
    def get_ids(cls):
        return list(Monitor.objects.values_list('id', flat=True))

    @classmethod
    def to_dict(cls):
        monitor_dict = {}
        for item in Monitor.objects.all():
            monitor_dict[item.id] = {
                'name': item.name,
                'ip': item.ip
            }
        return monitor_dict


class Task(BaseModel):
    class Meta:
        db_table = 'task'
        indexes = [
            models.Index(fields=['frequency'], name='frequency_idx'),
            models.Index(fields=['url'], name='url_idx'),
            models.Index(fields=['task_type'], name='task_type_idx')
        ]
    url = models.CharField(max_length=255)
    task_type = models.CharField(max_length=10)
    monitors = models.TextField()
    frequency = models.CharField(max_length=5)
    retry = models.IntegerField()
    submit_method = models.CharField(max_length=10)
    header = models.TextField(blank=True, null=True)
    redirect = models.BooleanField(default=False)
    time_out = models.IntegerField()

    def save(self, *args, **kwargs):
        monitors_str = self.monitors.strip(' ,')
        self.monitors = monitors_str
        monitors = monitors_str.split(',')
        all_monitors = Monitor.get_ids()
        if not set(monitors).issubset(set(all_monitors)):
            raise Exception('monitors invalid')

        regex_domain = re.compile(r'(?i)^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$', re.IGNORECASE)
        regex_ip = re.compile(r'^(([0-2]*[0-9]+[0-9]+)\.([0-2]*[0-9]+[0-9]+)\.([0-2]*[0-9]+[0-9]+)\.([0-2]*[0-9]+[0-9]+))$', re.IGNORECASE)
        regex_num = re.compile(r'[1-9][0-9]*')

        # 是否加上http验证呢

        if self.task_type == 'ping':
            match_domain = regex_domain.match(self.url)
            match_ip = valid_ip(self.url)
            if not match_domain and not match_ip:
                raise Exception('ping url shoule match ip or domain')
        if self.task_type == 'tcp':
            url = self.url
            u_list = url.split(':')
            if len(u_list) == 2:
                domain = u_list[0]
                match_domain = regex_domain.match(domain)
                match_ip = valid_ip(domain)
                if not match_domain and not match_ip:
                    raise Exception('tcp url shoule match ip or domain')
                port = u_list[1]
                match_port = regex_num.match(port)
                if not match_port:
                    raise Exception('tcp port not correct')

        super().save(*args, **kwargs)

    def __str__(self):
        return "{}:{}".format(self.task_type, self.id)


class Schedule(BaseModel):
    class Meta:
        db_table = 'schedule'
    STATUS = (
        ('stoped', 'stoped'),
        ('running', 'running'),
    )
    frequency = models.CharField(max_length=5,  unique=True, blank=False, null=False)
    status = models.CharField(choices=STATUS, default=STATUS[0][0], max_length=20)


class Result(BaseModel):
    class Meta:
        db_table = 'result'
    job_id = models.IntegerField(primary_key=True)
    content = models.TextField(default="[]")
