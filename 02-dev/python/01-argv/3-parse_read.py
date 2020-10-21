#!/usr/bin/env python
# encoding: utf-8

import ConfigParser
from sys import argv


##初始化对象
cf = ConfigParser.ConfigParser(allow_no_value = True)

##读取参数文件
cf.read(argv[1])

print('返回一个包含所有章节的列表:')
print cf.sections()                 

print('\n判断章节是否存在，返回布尔值:')
print cf.has_section('mysqld')          

print('\n以元组的形式返回章节下所有参数及其对应的参数值:')
print cf.items('client')        

print('\n以列表形式返回章节下所有参数:')
print cf.options('mysqld')

print('\n判断章节下某个指定参数是否存在:')
print cf.has_option('client','host')

print('\n获取参数值:')
print cf.get('client','host')
print cf.getint('client','port')                        ##指定格式返回参数值

##参数文件的操作
cf.remove_section('mysqld')
cf.remove_option('client','port')
cf.add_section('server')
cf.set('server','server_name','mariadb')                ##新增一个参数并指定值，也可以不指定，修改参数值也用此方法

##修改完成后存在新文件
cf.write(open('mysql.ini.bak','w'))
with open('mysql.ini.bak') as p_file : 
    print p_file.read()


