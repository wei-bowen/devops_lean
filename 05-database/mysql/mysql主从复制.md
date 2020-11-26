主从复制原理：
- 1、主库上把数据更改记录到bin log中
- 2、主库导出一个基线版本，并记录此时的bin log位置。
- 3、备库导入基线版本
- 4、备库将基线版本以后的binlog复制到自己的中继日志中
- 5、备库读取中继日志进行重放

### 1、开启binlog
主库和从的/etc/my.cnf中添加配置
```
log-bin   		    = /data/mysql/logs/mysql-bin.log
expire-logs-days  = 14
max-binlog-size   = 100M
server-id		      = 66				    ### 唯一ID，自行制定，每个库都不一样，默认为1
```
然后重启mysql

### 2、创建repl复制专用账户
mysql中执行(主库和从库都执行)
```
create user 'repl'@'192.168.0.%' IDENTIFIED BY 'rp1203';
GRANT REPLICATION SLAVE,REPLICATION CLIENT ON *.* TO 'repl'@'192.168.0.%';
flush privileges;
```

### 3、在备库开启复制
指定主库的相关信息，binlog位置
```
mysql> change master to master_host='192.168.0.66',master_user='repl',master_password='rp1203',master_log_file='mysql-bin.000002',master_log_pos=156;
```
- `start slave`开始复制。
- 备库上执行`show slave status\G`可以看到复制状态。Seconds_Behind_Master代表延迟时间
- 主控执行`show processlist\G`可以看到复制线程信息
- 从库配置只读`set global read_only=1;`
**同步异常处理**
- 根据从库发生异常的位置，查主库上的二进制日志。
- 根据主库二进制日志信息，找到更新后的整条记录。
- 在从库上执行在主库上找到的记录信息，进行insert操作。
- 跳过这条语句，再同步slave。
- pt-table-checksum可以校验主从库数据一致性。
