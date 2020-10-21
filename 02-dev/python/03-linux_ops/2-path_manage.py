# _*_ coding=utf-8 _*_
# author:韦博文
# date:2019/10/10
# content:文件与文件路径管理

import  os
from collections import Counter

'''
print(os.getcwd())                                      ##获取当前路径
print(os.listdir('.'))                                  ##列表形式展示路径下所有文件
print(os.path.split('/opt/github/python/03-linux_ops/1-file_read.py'))      ##split拆分返回路径和文件名的元组
print(os.path.dirname('/opt/github/python/03-linux_ops/1-file_read.py'))    ##返回路径
print(os.path.basename('/opt/github/python/03-linux_ops/1-file_read.py'))   ##返回文件名
print(os.path.splitext('/opt/github/python/03-linux_ops/1-file_read.py'))   ##按.拆分，返回文件后缀及后缀以外的二元组

print(os.path.expanduser('~root'))                      ##返回指定用户的家目录，缺省则为当前用户
print(os.path.abspath('1-file_read.py'))                ##得到文件或目录的绝对路径
print(os.path.isabs('.'))                               ##判断是否为绝对路径，返回布尔值

##获取文件属性
print(os.path.getctime('1-file_read.py'))               ##获取文件创建时间
print(os.path.getmtime('1-file_read.py'))               ##获取文件最后修改时间，时间戳格式
print(os.path.getatime('1-file_read.py'))               ##获取文件最后访问时间，时间戳格式
print(os.path.getsize('1-file_read.py'))                ##获取文件最后访问时间，时间戳格式

##判断文件类型
print(os.path.exists('1-file_read.py'))                 ##判断文件/路径是否存在
print(os.path.isfile('1-file_read.py'))                 ##判断文件存在(必须是文件否则False)
print(os.path.isdir('1-file_read.py'))                  ##判断目录存在(必须是目录否则False)
print(os.path.islink('1-file_read.py'))                 ##判断链接存在(必须是链接件否则False)
print(os.path.ismount('1-file_read.py'))                ##判断挂载点存在(必须是挂载点否则False)

##################范例###########################

##获取当前用户下所有文件列表
print([item for item in os.listdir(os.path.expanduser('~')) if os.path.isfile(os.path.expanduser('~') + '/' + item)])

##获取当前用户下所有文件大小的字典
print({item:os.path.getsize(os.path.expanduser('~') + '/' + item) for item in os.listdir(os.path.expanduser('~'))})


############文件管理

##切换当前工作目录
print(os.getcwd())
os.chdir(os.path.expanduser('~'))                   ##从脚本目录切换到家目录
print(os.getcwd())

os.remove('nohup.out')                              ##删除文件/路径
os.unlink('sda')                                    ##删除链接
os.rmdir('sasad')                                   ##删除空目录，非空报错
os.rename('old_name','new_name')                    ##重命名

os.chmod('path',777)                                ##修改文件权限
os.access('filename',os.R_OK)                       ##权限判断  R_OK是否可读，W_OK是否可写，X_OK是否可执行
os.chown('filename',600,800)                        ##修改文件所有者，需指定UID,GID
'''
##案例，打印最常用的10条命令

c = Counter()
with open(os.path.expanduser('~') + '/.bash_history') as his_commands:
    for line in his_commands:
        cmd = line.strip().split()
        if cmd:
            c[cmd[0]] += 1
print(c.most_common(10))