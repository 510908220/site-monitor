# -*- encoding: utf-8 -*-


import os
import subprocess
import time

import fire

import delegator
from app.constant import TASK_FREQUENCY_LIST

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SUPERVISOR_CONF = "/etc/supervisor/conf.d/supervisor-app.conf"
UWSGI_CONFIG_FILE = os.path.join(ROOT_DIR, 'uwsgi.ini')


UWSGI_CONFIG_TEMPLATE = """
[uwsgi]
master=true      
socket=127.0.0.1:8000 
home={virtualenv_dir}
processes=9     
socket-timeout=300
reload-mercy=10
vacuum=true
max-requests=1000
limit-as=1024
listen=1024
buffer-size=30000
memory-report=true
chdir=/opt/node
module=node.wsgi:application
"""
UWSGI_SUPERVISOR_TEMPLATE = """
[program:app-uwsgi]
command = {uwsgi_path} --ini {config}
stopsignal=QUIT
redirect_stderr=true
stdout_logfile = /var/log/uwsgi.log
stdout_logfile_backups = 2
stdout_logfile_maxbytes=20MB
user=root
"""

NGINX_SUPERVISOR_TEMPLATE = """
[program:nginx-app]
command = /usr/sbin/nginx  -g 'daemon off;'
"""
CHECK_TEMPLATE = """
[program:{frequency}_check]
command={python} {project_dir}/manage.py {frequency}_check
directory=/opt/node
autostart = false
autorestart = true
startsecs = 5
stopwaitsecs = 10
redirect_stderr=true
stdout_logfile=/var/log/{frequency}_supervisor.log
stdout_logfile_maxbytes=20MB
user=root
"""

SINGLE_CHECK_TEMPLATE = """
[program:single_check]
command={python} {project_dir}/manage.py single_check
directory=/opt/node
autostart = false
autorestart = true
startsecs = 5
stopwaitsecs = 10
redirect_stderr=true
stdout_logfile=/var/log/single_check.log
stdout_logfile_maxbytes=20MB
user=root
"""


def _log(msg):
    print(msg)


def _run_supervisor_cmd(supervisor_cmd):
    cmd = 'supervisorctl  {supervisor_cmd}'.format(
        supervisor_cmd=supervisor_cmd
    )
    c = delegator.run(cmd)
    print(c.out)


def _run_cmd(cmd):
    c = delegator.run(cmd)
    return c.out


def _get_process_cnt():
    out = _run_cmd('ps aux |grep -v grep|grep manage.py | grep check | wc -l')
    out_1 = _run_cmd('ps aux|grep "supervisord"|grep -v grep|wc -l')
    out_2 = _run_cmd('ps aux|grep "nginx"|grep -v grep|wc -l')
    out_3 = _run_cmd('ps aux|grep "uwsgi"|grep -v grep|wc -l')
    return int(out) + int(out_1) + int(out_2) + int(out_3)


def get_python():
    out = subprocess.check_output('pipenv run which python', shell=True)
    return out.decode('utf-8').strip()


def get_uwsgi():
    out = subprocess.check_output('pipenv run which uwsgi', shell=True)
    return out.decode('utf-8').strip()


def update_django_res(python_path):
    cmds = [
        "{} manage.py makemigrations",
        "{} manage.py migrate",
        "{} manage.py collectstatic --noinput",
        "{} manage.py init"
    ]

    for cmd in cmds:
        out = subprocess.check_output(cmd.format(python_path), shell=True)
        print(out)


def update_uwsgi_config(python_path):
    """
    设置虚拟环境目录到uwsgi.ini,写入文件.
    """
    with open(UWSGI_CONFIG_FILE, "w") as f:
        f.write(
            UWSGI_CONFIG_TEMPLATE.format(
                virtualenv_dir=os.path.dirname(os.path.dirname(python_path))
            )
        )


def update_supervisor_config():
    """
    将uwsgi和nginx写入supervisor配置.
    """
    uwsgi_config = os.path.join(ROOT_DIR, 'uwsgi.ini')

    configs = [NGINX_SUPERVISOR_TEMPLATE]
    configs.append(UWSGI_SUPERVISOR_TEMPLATE.format(
        config=uwsgi_config,
        uwsgi_path=get_uwsgi()
    ))

    for frequency in TASK_FREQUENCY_LIST:
        configs.append(CHECK_TEMPLATE.format(
            python=get_python(),
            project_dir=ROOT_DIR,
            frequency=frequency
        ))

    configs.append(SINGLE_CHECK_TEMPLATE.format(
        python=get_python(),
        project_dir=ROOT_DIR,
    ))
    with open(SUPERVISOR_CONF, "w") as f:
        f.write("\n\n".join(configs))


def _check_process():
    # 检查supervisord
    out = subprocess.check_output('ps aux | grep "supervisord" | grep -v grep | wc -l', shell=True)
    assert int(out.decode('utf-8')) == 1, 'supervisord process bad'

    # 正常进程数字
    process_count = 1  # supervisord进程
    process_count += 7  # command
    process_count += 1  # simgle_check command
    process_count += 5  # nginx
    process_count += 10  # uwsgi

    current_count = _get_process_cnt()
    assert current_count == process_count, 'process shoudle has {process_count}, but only has {current_count}'.format(
        process_count=process_count,
        current_count=current_count)


def stop():
    _run_supervisor_cmd('stop all')
    _run_supervisor_cmd('shutdown')

    if _get_process_cnt() > 0:
        _run_cmd("ps aux |grep -v grep|grep manage.py |awk '{print $2}'|xargs kill -9")
        _run_cmd("ps aux |grep -v grep|grep supervisord |awk '{print $2}'|xargs kill -9")
        _run_cmd("ps aux |grep -v grep|grep nginx|awk '{print $2}'|xargs kill -9")
        _run_cmd("ps aux |grep -v grep|grep uwsgi|awk '{print $2}'|xargs kill -9")
        time.sleep(2)

    if _get_process_cnt() != 0:
        raise Exception('stop failed, process count not is 0')

    if os.path.exists('/var/run/supervisor.sock'):
        os.remove('/var/run/supervisor.sock')


def start():
    if _get_process_cnt() != 0:
        raise Exception('process count not is 0')

    os.chdir(ROOT_DIR)
    # 更新配置
    python_path = get_python()
    update_django_res(python_path)
    update_uwsgi_config(python_path)
    update_supervisor_config()

    # 启动supervisor以及worker
    subprocess.check_output('service supervisor start', shell=True)
    time.sleep(1)
    _run_supervisor_cmd('start all')

    # 检查进程是否正常
    _check_process()


def restart():
    stop()
    start()


if __name__ == '__main__':
    fire.Fire({
        'stop': stop,
        'start': start,
        'restart': restart,
    })
