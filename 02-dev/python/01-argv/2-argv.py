#!/usr/bin/env python
# encoding: utf-8

from sys import argv

##argv的类型是列表
print type(argv)

##第一个参数argv[0]是执行文件本身
for argv_index in argv :
    print argv_index

