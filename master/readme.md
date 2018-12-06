# 主节点部署文档

部署可以参考检测节点部署.


## 数据库

安装`mongo`,由于需要存储一些历史数据：

https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/

安装后可以改一下数据存储路径等,关于数据存储量:

1. 存储近一周的数据https://docs.mongodb.com/manual/tutorial/expire-data/#expire-documents-after-a-specified-number-of-seconds
2. 索引

```bash
use master
db.history.getIndexes()

db.history.createIndex({task_id:1})

db.history.createIndex( { task_id: 1, last_check_time: -1 } )

db.history.createIndex( { "createdAt": 1 }, { expireAfterSeconds: 7776000 } )
db.history.dropIndex( "createdAt_1" )
```

  

## 代码配置



- 修改`settings.env`
- 修改`init.py`
- 启动服务

## 接口

比如主机ip是:`192.168.1.1`

访问`http://192.168.1.1/api/` 可以看到`Django REST framework`的api路由信息:
```
HTTP 200 OK
Allow: GET, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept

{
    "tasks": "http://192.168.1.1/api/tasks/",
    "monitors": "http://192.168.1.1/api/monitors/",
    "results": "http://192.168.1.1/api/results/",
    "statistics": "http://192.168.1.1/api/statistics/",
    "sites": "http://192.168.1.1/api/sites/",
    "status": "http://192.168.1.1/api/status/"
}
```

#### tasks

任务接口

```
GET /api/tasks/
```

```json
HTTP 200 OK
Allow: GET, POST, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept

[
    {
        "id": 21552,
        "url": "http://www.qq.com",
        "task_type": "http",
        "frequency": "10",
        "retry": 1,
        "submit_method": "0",
        "time_out": 60,
        "created": "2018-06-08 11:35:32",
        "updated": "2018-11-23 11:29:32",
        "monitors": "1000,1001,1002,1003,1004,1005,1006,1007",
        "header": "User-Agent:Chrome\nRange: bytes=0-1040000",
        "redirect": true
    }
]
```



| 字段          | 描述                                                         |
| ------------- | ------------------------------------------------------------ |
| url           | 被检测的站点                                                 |
| task_type     | 任务类型,支持http、tcp、ping三种类型                         |
| frequency     | 检测频率，有2、5、10、15、20、30、60分钟                     |
| retry         | 检测重试次数                                                 |
| submit_method | 检测方法, 默认是get,还支持head、post                         |
| time_out      | 超时时间                                                     |
| monitors      | 监测点id列表,一个监测点表示一个检测节点.比如上海节点、北京节点等. |
| header        | 检测使用的http头                                             |
| redirect      | 是否支持重定向，如果支持最终结果是重定向后的结果             |
| created       | 创建时间                                                     |
| updated       | 更新时间                                                     |



## monitors

监测点接口

```
GET /api/monitors/
```

```
HTTP 200 OK
Allow: GET, POST, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept

[
    {
        "id": "1000",
        "created": "2018-06-04 10:59:35",
        "updated": "2018-06-04 10:59:35",
        "name": "上海电信",
        "ip": "1.2.3.4"
    },
    {
        "id": "1001",
        "created": "2018-06-22 08:36:14",
        "updated": "2018-06-22 08:38:02",
        "name": "江苏移动",
        "ip": "5.6.7.8"
    }
]
```

## results

结果获取接口

```
GET /api/results/
```

```
[
    {
        "id": 111,
        "content": {
            "1000": {
                "res": "1",
                "sta": "200 OK",
                "tim": "1668.17",
                "last_check_time": "1540880663",
                "monitor_name": "上海电信"
            },
            "1001": {
                "res": "1",
                "sta": "200 OK",
                "tim": "1817.46",
                "last_check_time": "1540880663",
                "monitor_name": "江苏移动"
            },
        }
    }
]
```

| 字段            | 描述                     |
| --------------- | ------------------------ |
| res             | 1表示站点正常，0表示异常 |
| sta             | 结果描述                 |
| tim             | 检测耗时                 |
| last_check_time | 检测完成时间点           |
| monitor_name    | 监测点名称               |
|                 |                          |



## statistics

任务信息统计接口

```
GET /api/statistics/
```

```
HTTP 200 OK
Allow: GET, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept

{
    "http_count": 1466,
    "tcp_count": 140,
    "ping_count": 5,
    "frequency_dict": {
        "2": 1164,
        "5": 443,
        "10": 1,
        "15": 3,
        "20": 0,
        "30": 0,
        "60": 0
    }
}
```

不同类型以及频率统计



## status

```
GET /api/status/
```

每一个监测点每一个频率任务状态

## sites

这个接口支持实时检测，就是下发任务，返回一个id，然后监控任务状态等待任务结束，然后拿到结果. 适合做实时检测功能.

上面的t`tasks`接口是后台进程定期来组装不同频率任务进行调度的.

```
GET /api/sites/
```

