### tips
如果忘记了root密码，可以在配置文件(默认是/etc/mt.cnf)中添加`skip-grant-tables`跳过权限验证直接root登陆来修改权限。
### 授权对象
'user_name'@'hostname'
- hostname支持%通配符，可以是所有主机'%'或者'192.168.1.%'网段、'*.weibowen.cn'域名段

### 权限级别
- 实例级。存放在mysql.user表中
- 数据库级。存放在mysql.db表中
- 数据库对象级(表/视图等)。tables_priv、columns_priv、procs_priv表等

### 权限查看
- `select User,host from user`可以看到用户信息及其全局权限情况。
- `show grants for 'root'@'localhost'`可以查看用户的具体权限信息。

### 创建用户
- `create user 'user_name'@'host_name' identified by 'password'`  创建用户
- `alter user 'user_name'@'host_name' identified by 'new_password';`修改用户密码
- `delete from user where user='user_name'`删除用户
