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

### 创建repl复制专用账户
mysql中执行(主库和从库都执行)
```
create user 'repl'@'192.168.0.%' IDENTIFIED BY 'rp1203';
GRANT REPLICATION SLAVE,REPLICATION CLIENT ON *.* TO 'repl'@'192.168.0.%';
flush privileges;
```
