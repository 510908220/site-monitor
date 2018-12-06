from rest_framework import serializers
from app.models import Task, Result, Monitor
from app.constant import TASK_FREQUENCY_LIST


class TaskSerializer(serializers.ModelSerializer):
    """
    Task Serializer
    """
    url = serializers.CharField(max_length=255)
    task_type = serializers.ChoiceField(choices=['http', 'ping', 'tcp'])
    frequency = serializers.ChoiceField(choices=TASK_FREQUENCY_LIST)
    retry = serializers.IntegerField(min_value=1, max_value=3)
    submit_method = serializers.ChoiceField(choices=['0', '1', '2'])
    time_out = serializers.IntegerField(min_value=1)

    class Meta:
        model = Task
        fields = '__all__'


class MonitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Monitor
        fields = '__all__'
