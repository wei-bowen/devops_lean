## 05、Mysql备份恢复
### 备份策略
`SHOW VARIABLES LIKE 'datadir'`确认数据目录位置

#### 定义恢复需求
- 恢复点目标：容忍丢失多少数据
- 恢复时间目标：可以等待多久将数据恢复
- 需要恢复什么：整个实例还是单个数据库还是单个表
- 锁时间：备份缩表是否影响应用，影响多久
- 备份时间：复制备份到目的地要多久
- 备份负载：备份时对服务器性能影响多大


#### 备份方案
- 基于快照的备份时最好的选择，对于较小的数据库则可以考虑逻辑备份(导出数据)
- 备份建议异地多个
- 备份应抽取数据进行恢复测试
- 保存二进制日志用于基于故障时间点的恢复，参数expire_logs_days至少跨越两个备份周期
- 监控备份，确保备份正常
- 经常演练，测算恢复所需资源(cpu、磁盘空间、带宽、恢复时间)
- 备份文件加密
- 如果可以，关闭mysql做备份最简单且安全，可以获得完整一致性副本。锁表备份为次选，有一些一致性风险

- 最好时先使用物理复制，以此数据启动MYSQL服务器实例并运行mysqlcheck。周期性地使用mysqldump执行逻辑备份

### mysqldump热备
#### 数据导入
`cat 导出文件.sql | mysql -uroot -p`重定向即可导入

#### 全部导出
格式：`mysqldump [OPTIONS] --all-databases [OPTIONS]`<br>
例如：`mysqldump -uroot -proot --all-databases >/tmp/all.sql`

#### 整库导出
格式：`mysqldump [OPTIONS] --databases [OPTIONS] DB1 [DB2 DB3...]`<br>
例如：`mysqldump -uroot -proot --databases db1 db2 >/tmp/user.sql`

#### 导出表
导出表时将不会导出建库语句，导入时如果库不存在会报错
格式：`mysqldump [OPTIONS] database [tables]`<br>
例如：`mysqldump -uroot -proot --databases db1 --tables a1 a2  >/tmp/db1.sql`<br>

#### 可用选项
- --host指定数据库
<br>`mysqldump  -uroot -p --host=localhost --all-databases`

- --where="判断表达式"。按条件导出
<br>`mysqldump -uroot -proot --databases db1 --tables a1 --where='id=1'  >/tmp/a1.sql`

- --nodata只导出结构
<br>`mysqldump -uroot -proot --no-data --databases db1 >/tmp/db1.sql`

- -F导出后生成新的binlog
<br>`mysqldump -uroot -proot --databases db1 -F >/tmp/db1.sql`

- --lock-all-tables，缩略写成-l也可。导出时锁表。一般不用，下面有更好的选项。

- --single-transaction提交一个BEGIN SQL语句，通过事务的隔离性保证导出的一致性状态。
<br>`mysqldump -uroot -proot --single-transaction --databases db1 >/tmp/db1.sql`

- --dump-slave将主库的binlog位置和文件名追加到导出数据的文件中。该选项会调用--lock-all-tables缩表。如果是在从库执行，将会停止SLAVE线程，然后记录此时同步到的binlog位置.将CHANGE MASTER命令输出到数据文件.导出完成后自动start slave

- --master-data。将数据库本身的binlog位置输出到数据文件.而非同步的位置。

- --routines, -R导出存储过程和自定义函数。
<br>`mysqldump  -uroot -p --host=localhost --all-databases --routines`

### 冷备innobackupex
#### 安装
```
yum install https://repo.percona.com/yum/percona-release-latest.noarch.rpm -y
yum install percona-xtrabackup-80 -y
```
#### 整备
```
xtrabackup --defaults-file=/etc/my.cnf --user=root --password --backup=1 --target-dir=/data/backup/mysql/`date +%F_%T`
```
#### 整库恢复
- `systemctl stop mysql`关闭数据库
- `rm -rf /data/mysql/* && /var/log/mysql/*`清空数据目录和binlog存储目录
- `xtrabackup --defaults-file=/etc/my.cnf --prepare --target-dir=备份文件目录`。追平日志(xtrbackup备份开始到结束的的这段时间,数据库可能执行了其他操作，需要将binlog中记录的操作追平到数据文件中)
- `xtrabackup --defaults-file=/etc/my.cnf --copy-back --target-dir=备份文件目录`还原
- `chown -R mysql:mysql /data/mysql && chown -R mysql:mysql /var/log/mysql`root用户还原的数据数组默认是root，需要修改为mysql
- `systemctl start mysql`启动数据库即成功
