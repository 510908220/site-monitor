# -*- encoding:utf-8 -*-

from .models import Task, Result
from django.db.models.signals import post_delete
from django.dispatch import receiver


@receiver(post_delete, sender=Task)
def delete_task_cleanup(sender, instance, *args, **kwargs):
    # 任务删除后，将结果也一并删除
    Result.objects.filter(job_id=instance.id).delete()
