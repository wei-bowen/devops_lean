# _*_ coding=utf-8 _*_
# author:韦博文
# date:2019/10/9
# content:文本处理

from collections import Counter

'''
### 使用原始字符串
print('c:\next\date')           #不使用原始字符串输出路径时,\被当成转义符

print(r'c:\next\date')          #使用原始字符串，取消一切转义

###字符串的特性之一：不可变性，当我们对字符串操作时，看起来是字符串变了，实际上是产生了新的字符串

words = ('i','am','a','chinese','!')
text = ''
for word in words :
    text += word + ' '
print(text)                     ##使用此方法拼接列表中的字符串时，循环5次，实际产生5个字符串，浪费内存

text = " ".join(words)
print(text)                     ##指定分割符，对列表中的字符进行拼接，只产生一个新的字符串，操作比较合理

print('i','am','a','chinese','!',sep = ' ')     ##无需产生新字符串，指定分割符打印即可

###字符串函数
print(len(text))                ##计算字符串长度，以单词为单位

print(text[0:10:2])             ##字符串长度，指定起止点和步长
print(text.upper())             ##转换成全大写
print(text.lower())             ##转换成全小写
print(text.isupper())           ##判断是否为全大写，返回布尔值
print(text.islower())           ##判断是否为全小写，返回布尔值
print(text.swapcase())          ##大小写转置
print(text.capitalize())        ##转换成首字母大写的标题格式
print(text.istitle())           ##判断是否为手写字母大写的标题格式

#判断类
print(text.isalpha())           ##判断是为全字母
print(text.isalnum())           ##判断是否包含字母+数字
print(text.isspace())           ##判断是否包含回车制表符空格等空白字符
print(text.isdecimal())         ##判断是否全数字

print(text.startswith('i am'))  ##判断是否以指定字符串为开头
print(text.endswith('am'))          ##判断是否以指定字符串为后缀

#查找类
print(text.find('am'))          ##返回指定字符串在文本中的位置，如果不存在返回-1
print(text.rfind('am'))         ##从后倒着找，找不到返回-1
print(text.index('i'))         ##返回指定字符串在文本中的下标，找不到直接程序报错
print(text.rindex('!'))         ##返回指定字符串在文本中的下标(倒着找)，找不到直接程序报错
'''
##字符串格式化
print("{1} {0} {1}".format('hello','world'))     ##可以指定顺序，也可以缺省使用默认顺序
print("网站名={name}，站长：{user}".format(name = '野狼之家',user = '韦博文'))
##还有数字格式，需要学习以下

###实战案例
'''1、分析apache访问日志'''

ips = []
with open('/application/nginx-1.16.1/logs/access.log') as f :
    for line in f :
        ips.append(line.split()[0])             ###访问日志是以空格为分割符，每一行的第一个数据为IP

print("PV is {0}".format(len(ips)))
print("UV is {0}".format(len(set(ips))) )       ##利用set去重获取独立IP数

'''2、分析资源热度'''

d = {}
with open('/application/nginx-1.16.1/logs/access.log') as f :
    for line in f :
        key = line.split()[9]               ##第九个变量为状态码
        d.setdefault(key,0)                 ##如果是第一次统计则初始化为0
        d[key] += 1

sum_requests = 0
err_requests = 0

for key,value in d.items():
    try:
        if int(key) >= 400:
            err_requests += value
    except:                                 ##日志状态码有些是“-”不是数字会报错，暂不深究
        err_requests += value
    sum_requests += value

print('error rate:{0:.2f}%'.format((err_requests * 100.0 / sum_requests)))



