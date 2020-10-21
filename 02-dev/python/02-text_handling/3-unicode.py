# _*_ coding=utf-8 _*_
# author:韦博文
# date:2019/10/9
# content:字符集编码

## unicode和utf-8之间不需要转换，直接相互打印
## GBK和utf-8之间要通过unicode转换
## 转换到unicode叫编码decode,转换到GBK和utf-8叫解码encode

uni_str = u'hello world!'

##示例：转换到utf-8
utf8_str = uni_str.encode('utf-8')

##由utf-8转gbk要先编码再解码
gbk_str = utf8_str.decode('utf-8').encode('gbk')