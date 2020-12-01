![redis知识全景](images/redis_qj.jpg)
- **高性能**，包括线程模型、数据结构、持久化、网络框架
- **高可靠**，包括主从复制、烧饼机制
- **高可扩展**，数据分片，负载均衡

redis特性
- key-value型数据库
- 内存键值数据库。所有操作都在内存上完成，这是它快的基础
- 单线程，高性能
- 使用哈希表作为key-value索引
- 通过网络框架进行访问，而非动态库
- 支持日志/快照两种持久化方式

redis是key-value键值对型数据库，value支持
- Strng
- 哈希表
- 列表
- 集合

支持的操作
- PUT: 新写入一个key-value对
- SET：更新一个key-value对
- GET：根据key读取value
- DELETE: 根据key删除键值对
------------------------------------------------------------------------------------------------------
>redis能干什么

- 内存存储、持久化。内存中是断电即失，所以说持久化很重要(rdb、aof)
- 效率高，可用于高速缓存
- 发布订阅系统
- 地图信息分析
- 计数器、计时器
- ....

>特性

- 多样的数据类型
- 持久化
- 集群
- 事务
- ...

## 安装

- yum install gcc-c++ tcl -y`安装依赖，redis是c++写的,tcl是make test需要用
- `yum -y install centos-release-scl && yum -y install devtoolset-9-gcc &&devtoolset-9-gcc-c++ devtoolset-9-binutils&& scl enable devtoolset-9 bash`需要9.01以上的gcc版本
- 下载`wget http://download.redis.io/releases/redis-6.0.6.tar.gz`
- `tar -zxvf redis-6.0.9.tar.gz && cd redis-6.0.9`
- `make && make install`编译安装.默认二进制文件会安装在/usr/local/bin/下
- `cp redis.conf /etc/`这个随意的，启动的时候指定位置即可.
- `redis-server /etc/redis.conf`即可运行redis

### 配置文件

```nginx
daemonize no                                ###改成yes即可后台运行
```

#### 压测redis-benchmark



#### 基础知识

- 配置文件中`databases 16`默认有16个数据库标号0~15，可以通过select n进行切换
- DBSIZE可以查看当前库大小
- `keys *`查看库内所有key
- flushdb清空当前库,flushall清空所有数据库

>redis是单线程的

- redis是基于内存操作的，性能瓶颈不在于CPU而是机器的欸粗和网络宽带，所以没必要多线程

## redis五大数据类型

- **String**

```
- - set key value                       ##设置值
- - get key                             ##获取值
- - append key value2                   ##原值的基础上再接上一个字符串
- - exists key                          ##判断key是否存在
- - INCR key                            ##key如果是数字的话加一
- - INCRBY key n                        ##自增n
- - DECR key                            ##自减1
- - DECRBY key n                        ##自减n
- - GETRANGE key1 startN endN           ##截取字符串，切片
- - SETRANGE key1 n XXXX                ##从指定位置开始替换字符串
- - setnx key value                     ##key不存在时创建
- - setex key seconds value             ##同时设置过期时间
- - mset key1 value1 key2 value2 ..     ##同时配置多值
- - mget key1 key2 ..                   ##同时获取多值
- - msetnx key1 value1 key2 value2 ..   ##同时配置多值,不存在时才成功。任意失败全部失败
- - getset key value                    ##先获取再设置
```

- **List**，所有命令用l/R开头,L是左边追加R右边追加，取都是右边取

```
- - lpush list value                    ##从左边向列表追加值
- - RPUSH list value                    ##从右边追加值
- - LRANGE list startN endN             ##取liSt的值。序号是从左到右排
- - Lpop list                           ##移除列表左边第一个元素
- - Rpop list                           ##移除列表最后一个元素，即右边第一个元素
- - LINDEX list n                       ##按下标取值，左排序
- - Rindex list                         ##按下标取值,右排序
- - Llen list                           ##算列表长度
- - Lrem list count value               ##移除count个value
- - Ltrim list startN endN              ##截断。保留一部分列表，其余删除
- - rpoplpush srclist dstlist           ##移除列表最后一个元素并推到另一个列表
- - exists list                         ##判断列表是否存在
- - lset list index value               ##修改特定下表的值，下标不存在时报错
- - LINSERT list before 3 r             ##列表中3的前面插入r,也可以使用after
```

- **Set**,无序不重复集合

```
- - setadd myset value                  ##添加成员
- - smembers myset                      ##获取集合全部成员
- - SISMEMBER myset value               ##判断是否时集合成员之一
- - SCARD myset                         ##获取集合成员数量
- - SREM myset value                    ##移除指定成员
- - SRANDMEMBER myset n                 ##随机抽出n个成员
- - SPOP myset                          ##随机移除一个成员
- - SMPVE srcSet dstSet member          ##将成员移动到另一个集合
- - SDIFF set1 set2 ..                  ##多个set的差集
- - SINTER set1 set2 ..                 ##并集
- - SUNION set1 set2 ..                 ##并集

```

- **Hash**
- **Zset**


- `exists name`查看name这个key是否存在。

## Redis持久化

### RDB

### AOF

## Redis发布订阅

发送者(pub)发送消息,订阅者(sub)接收消息  
Redis客户端可以定于任意数量的频道

> 三要素

- 消息发送者
- 频道
- 消息订阅者

> 原理

通过SUBSCRIBE命令订阅某频道后,Redis-server维护了一个字典，键是一个个频道，值则时一个链表，链表中保存了所有定义这个channel的客户端。  
通过PUBLISH命令向定义这发送消息,Redis-server会使用给定的频道作为键，遍历字典中对应的链表，将消息逐个发送

> 命令与描述

| 序号 | 命令                                        | 描述                        |
| ---- | ------------------------------------------- | --------------------------- |
| 1    | PSUBSCRIBE pattern [pattern ...]            | 订阅1~n个符合给定模式的频道 |
| 2    | PUBSUB subcommand [argument [argument ...]] | 查看订阅与发布系统状态      |
| 3    | PUBLISH channel message                     | 将消息发送到指定的频道      |
| 4    | PUNSUBSCRIBE [pattern [pattern ...]]        | 退订所有给定模式的频道      |
| 5    | SUBSCRIBE channel [channel ...]             | 定于给定的1~n个频道的信息   |
| 6    | UNSUBSCRIBE [channel [channel ...]]         | 推定给定的频道              |

```shell
127.0.0.1:6379> SUBSCRIBE kuangshenshuo						##接收端订阅频道，名称自定义
127.0.0.1:6379> PUBLISH kuangshenshuo "hello"				##发布端只要发送消息，订阅者就会同步收到消息
```



## Redis主从复制

> 原理

- slave启动成功连接到master后会发送一个sync同步命令
- Master街道命令后启动后台存盘进程，同时收集所有接收到的用于修改数据集命令，在后台进程执行完毕之后，master将传送整个数据文件到slave，完成一次完全同步
- 全量复制:slave接收到数据库文件数据后，将其存盘并加载到内存中
- 增量复制:Master继续将新的所有收集到的修改命令一次传给slave，完成同步。
- 如果master关机或者其他原因断开链接，slave重新连接后会进行一次完全同步。

> 配置准备

- 192.168.0.66	master
- 192.168.0.88    slave1
- 192.168.0.99    slave2

> 环境配置

- mater无需配置，redis默认自己是主库

```shell
127.0.0.1:6379> info replication					##查看当前库的信息
# Replication
role:master											##角色
connected_slaves:0									##从机数量
master_replid:6496fa0bac88b66a21ccbc42f31aac70cafc10b4
master_replid2:0000000000000000000000000000000000000000
master_repl_offset:0
second_repl_offset:-1
repl_backlog_active:0
repl_backlog_size:1048576
repl_backlog_first_byte_offset:0
repl_backlog_histlen:0
```



- slave配置
  - `SLAVEOF Masr_IP port`可以命令行中执行，也可以写入配置文件。`SLAVEOF NO ONE`可以关闭slave重新恢复master
  - `config set masterauth <password>`如果master有密码，可以命令行设置。最好是文件中配置`masterauth <password>`
  - `role`查看当前角色是master还是slave，`info replication`查看同步状态

## 哨兵模式

哨兵作为独立进程，通过发送命令，等待Redis服务器响应,从而监控多个Redis实例。当检测到Master宕机时，自动将slave切成Master,然后通过发布定于模式通知其他slave服务器修改配置跟从新的Master。可以启动多个哨兵，监控Redis主机的同时还可以互相监控。

- **哨兵配置**

  - 配置文件

    ```
    port 16379											##哨兵模式端口
    dir /tmp											##工作目录
    daemonize no										##是否后台运行
    pidfile /var/run/redis-sentinel.pid					##pid文件路径
    logfile ""											##日志位置
    sentinel deny-scripts-reconfig yes
    sentinel notification-script mymaster /var/redis/notify.sh	##Master故障时执行脚本，自己写的通知脚本
    sentinel monitor mymaster 127.0.0.1 6379 2			##2代表需要至少两个哨兵认为需要切换时才进行主从切换.主机名自定义
    sentinel down-after-milliseconds mymaster 60000		##受控服务器多少毫秒无反应时哨兵可认为已断线
    sentinel failover-timeout mymaster 180000
    sentinel client-reconfig-script mymaster reconfig.sh	##Master变动时，调用脚本更改Slave配置
    sentinel parallel-syncs mymaster 1					##指定最多可以有多少个Slave同时对新Master进行同步
    
    sentinel monitor resque 192.168.1.3 6380 4
    sentinel down-after-milliseconds resque 10000
    sentinel failover-timeout resque 180000
    sentinel parallel-syncs resque 5
    ```

  - 哨兵启动`redis-server /path/to/sentinel.conf --sentinel`

## 缓存穿透和雪崩

### 缓存穿透

> 概念

用户想要查询一个数据，发现redis内存数据库没有(即缓存未命中)，于是项持久层数据库(如Mysql)发起查询，给持久层数据库造成了压力。

> 解决方案

- **布隆过滤器**

  对所有可能查询得参数以hash形式存储，在控制层先进行校验，不符合就丢弃，避免无谓查询对持久层数据库造成查询压力。

- **缓存空对象**

  当存储层未命中，即使返回得空对象也将其缓存起来，同时设置国企时间，之后再访问这个数据将会从缓存中获取，保护后端数据源。

### 缓存击穿

> 概念

某个key特别热门，不停被大并发集中访问，在这个key失效的瞬间，持续的大并发穿破缓存直接请求数据库。

> 解决方案

- **设置热点永不过期**

- **加互斥锁** 

  使用分布式锁，保证对于每个key

### 缓存雪崩

> 概念

某一个时间段，缓存集中过期失效，或者redis宕机。产生周期性的压力波峰，导致所有请求到达存储层，存储层调用激增容易产生故障。

> 解决方案

- **redis高可用**

- **限流降级**

- **数据预热**

  
