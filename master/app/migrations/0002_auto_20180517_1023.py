# Generated by Django 2.0.5 on 2018-05-17 10:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='is_agent',
        ),
        migrations.RemoveField(
            model_name='task',
            name='rp_time',
        ),
        migrations.RemoveField(
            model_name='task',
            name='status',
        ),
        migrations.RemoveField(
            model_name='task',
            name='task_name',
        ),
    ]