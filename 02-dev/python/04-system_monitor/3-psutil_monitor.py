# _*_ coding=utf-8 _*_
# author:韦博文
# date:2019/10/14
# content:使用psutil库监控linux


import psutil
'''
########################################CPU相关#################################################
print(psutil.cpu_count(logical=False))                  ##CPU个数，参数logical可省略，=False代表只统计物理CPU
print(psutil.cpu_percent(interval=2,percpu=True))       ##参数可省略。interval获取醉经几分钟内的平均CPU利用率
                                                        ##不指定则默认获取从上一次查询以来的平均利用率。默认情况
                                                        ##下获取每个CPU利用率，percpu=True获取整体利用率

print(psutil.cpu_times())                               ##元组形式返回CPU的时间花费，percpu指定获取每个CPU的统计
print(psutil.cpu_times_percent())                       ##类似times,返回比例
print(psutil.cpu_stats())                               ##元组返回CPU统计信息，包括上下文切换、系统调用次数等

########################################内存相关#################################################
print(psutil.virtual_memory())                          ##元组返回内存统计信息，除了利用率，都是字节单位
print(psutil.virtual_memory().total)
print(psutil.swap_memory().total)                       ##swap统计，类似内存

print(psutil.disk_partitions())                         ##元组返回磁盘名称、挂载点、文件系统类型
print(psutil.disk_usage('/'))                           ##元组返回目录对应磁盘的容量，利用率等统计信息
print(psutil.disk_io_counters())                        ##统计磁盘I/O相关信息，元组返回

print(psutil.net_io_counters(pernic=True))              ##统计所有网卡的网络IO，参数省略则返回整体网络IO
print(psutil.net_connections())                         ##列表返回网络链接的详细信息
print(psutil.net_if_addrs())                            ##字典返回网卡的配置信息，包括IP地址MAC等
print(psutil.net_if_stats())                            ##返回网卡详细信息，是否启动、通信类型、传输速度等

print(psutil.users())                                   ##命名元组方式返回当前登陆用户的信息
print(psutil.boot_time())                               ##返回系统启动时间戳

'''

##*****************************实战********************************************

