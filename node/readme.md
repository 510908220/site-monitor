# 监测点部署文档



## 环境安装

- ` vim /etc/sysctl.conf `
- `net.core.somaxconn=4096 `
- `sysctl -p `
- `cat /proc/sys/net/core/somaxconn`查看


- ulimit -n 

    在某个机器上模拟同事创建两千多个线程,每个线程调用requests. 遇到了

  `[Errno 24] Too many open files',))`错误. 最后发现是打开文件数量有限制.

  ```
  vim /etc/security/limits.conf
  root hard nofile 1000000
  root soft nofile 1000000
  root soft core unlimited
  root soft stack 10240
  ```

  


- 安装`mysql`,执行`node.sql`



- 项目使用了`python3.6`,没有的话需要安以及对应的pip

  ```
  add-apt-repository ppa:jonathonf/python-3.6 && apt-get update && apt-get install python3.6 -y
  
  curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
  sudo python3.6 get-pip.py
  
  ```

- ```
  mkdir ~/.pip && vim  ~/.pip/pip.conf
  [global]
  trusted-host =  mirrors.aliyun.com
  index-url = http://mirrors.aliyun.com/pypi/simple
  
  ```

- `sudo pip3.6 install pipenv`

- `sudo apt-get install build-essential libmysqlclient-dev python3-dev libpython3.6-dev unzip  ` 

- `sudo apt-get install nginx supervisor -y` 

- 代码拷贝到`/opt`目录

  在`/opt/node`里拷贝`cp www-nginx.conf  /etc/nginx/sites-enabled/default`

- `cd /opt/node`,执行`pipenv install`会自动创建虚拟环境和装包.

- 修改`settings.py`配置和`init.py`里配置

- `pipenv run python service.py restart`


## 反爬虫支持

如果站点有反爬虫机制, 比如知道创宇的加速乐. 使用requests去访问的话会返回一个错误码521,内容的话是一些奇怪的js. 当然网上也有一些方法去解密这个js等,但是这个js一直在变. 可以根据网上那些解密js去了解一下这个原理.
最后,选取了chrome headless方式去解决. 实际就是一个无头浏览器,拥有浏览器所有功能,只是没界面而已.

具体实现逻辑在代码. 这里说一下环境的安装:
```
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

sudo dpkg -i google-chrome-stable_current_amd64.deb
```
安装后,执行一下命令`which google-chrome`看位置是否在`/usr/bin/google-chrome`,因为`pyppeteer`这个库需要用到`chrome`浏览器, 我在配置里指定了`executablePath`为`/usr/bin/google-chrome`.(如果不指定,第一次用`pyppeteer`会下载浏览器,太慢了.)

chrome安装过程如果出现错误,可能少一些包,安装一下.

## 网速测试



```
curl -s https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python -
```


## 安全

由于监测点没有对外的web服务没加登陆，这里通过防火墙控制

```
sudo apt-get update
sudo apt-get install iptables-persistent

iptables -A INPUT -s x.x.x.x -p tcp --dport 80 -j ACCEPT

iptables -A INPUT -p tcp --dport 80 -j DROP
# 如果要新增规则,先执行iptables -D INPUT -p tcp --dport 80 -j DROP
然后新增，然后在执行iptables -A INPUT -p tcp --dport 80 -j DROP
invoke-rc.d iptables-persistent save

```

## 性能测试

#### 线程数

创建1万个线程

```python
import time
from concurrent import futures

def process_one(params):
    print(params)

tasks = range(50000)
results = []
with futures.ThreadPoolExecutor(max_workers=10000) as executor:
	for future in executor.map(process_one, tasks):
		results.append(future)

```

#### 并发访问网站

如下错误:

```
 Failed to establish a new connection: [Errno -2] Name or service not known',))")
 查询资料后,有这么句话:"但如果程序发起的请求量较大，那么服务器就容易被这些DNS服务器禁止访问"
 
```

这里考虑装一个nscd来缓存dns结果. 可以在这里看[详细说明](http://baijiahao.baidu.com/s?id=1583248175904249891&wfr=spider&for=pc)

- 安装: `apt-get install nscd  -y`

-  字段解释https://www.hi-linux.com/posts/9461.html


还可以新增域名服务器：

- `vim /etc/resolv.conf`

- 配置如下:

  ```
  nameserver 114.114.114.114
  nameserver 223.5.5.5
  其中一个是阿里云的域名服务
  ```



#### 检查超过60s

代码里配置的timeout最大是60s,实际出现过70、80、90甚至120.

查看`requests`文档,对`timeout`有这样的描述:

```
timeout 仅对连接过程有效，与响应体的下载无关。 timeout 并不是整个下载响应的时间限制，而是如果服务器在 timeout 秒内没有应答，将会引发一个异常（更精确地说，是在 timeout 秒内没有从基础套接字上接收到任何字节的数据时）
```

这里有详尽的关于`timeout`的描述:http://docs.python-requests.org/zh_CN/latest/user/advanced.html#timeout



如果你制订了一个单一的值作为 timeout，如下所示：

```
r = requests.get('https://github.com', timeout=5)
```

这一 timeout 值将会用作 `connect` 和 `read` 二者的 timeout。如果要分别制定，就传入一个元组：

```
r = requests.get('https://github.com', timeout=(3.05, 27))
```

如果远端服务器很慢，你可以让 Request 永远等待，传入一个 None 作为 timeout 值，然后就冲咖啡去吧。

```
r = requests.get('https://github.com', timeout=None)
```

后来发现,这样也解决不了问题. 线程还是会卡死.




