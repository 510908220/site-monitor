from django.db import models

# Create your models here.


class BaseModel(models.Model):
    class Meta:
        abstract = True  # Set this model as Abstract
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class Schedule(BaseModel):
    class Meta:
        db_table = 'schedule'
    STATUS = (
        ('stoped', 'stoped'),
        ('running', 'running'),
    )

    frequency = models.CharField(max_length=5, primary_key=True)
    master_schedule_id = models.IntegerField(default=0)
    status = models.CharField(choices=STATUS, default=STATUS[0][0], max_length=20)
    tasks = models.TextField(default='[]')
    resutls = models.TextField(default='[]')


class Check(BaseModel):
    class Meta:
        db_table = 'check'

    TYPES = (
        ('http', 'http'),
        ('ping', 'ping'),
        ('tcp', 'tcp'),
        ('dig', 'dig'),
    )

    STATUS = (
        ('running', 'running'),
        ('stoped', 'stoped'),
    )

    url = models.CharField(max_length=255)
    status = models.CharField(choices=STATUS, default=STATUS[0][0], max_length=20)
    tp = models.CharField(choices=TYPES, default=TYPES[0][0], max_length=20)
    resut = models.TextField(default='{}')
