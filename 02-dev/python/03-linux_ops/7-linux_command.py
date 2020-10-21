# _*_ coding=utf-8 _*_
# author:韦博文
# date:2019/10/11
# content:调用外部linux命令

import subprocess

##1、call
'''
函数定义:
subprocess.call(args,*,stdin=None,stdout=None,stderr=None,shell=False)
说明：
    args是命令列表
    call的返回是命令的执行结果，0为正确执行
    check_call函数使用方法类似，但是命令执行失败直接报程序错误

run_result = subprocess.call(['ls','-l'])
print(run_result)
print('*'*200)
##指定以shell来运行时python会先运行一个shell再调用shell去执行命令，会产生两个进程
subprocess.call('ls -l *.py',shell=True)
print('*'*200)
##2、check_output,跟call的区别:call直接打印结果再控制台，output返回结果,命令执行失败报程序错误
output = subprocess.check_output('ls -l',shell=True)
print(str(output,encoding = 'utf-8'))           ##输出为bytes,需要解码为utf8
'''
###################popen类#######################

