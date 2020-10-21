# _*_ coding=utf-8 _*_
# author:韦博文
# date:2019/10/9
# content:文件读写

##一次性读取所有
f = open('data.txt','r')    ## 此处r可以省略。打开模式还有w读(如果没有才新建)、a追加写、x新建(如果存在报错)
print(f.read())             ## 一次性
f.close()

##一次读一行
f = open('data.txt','r')
print(f.readline())
f.close()

##读取所有行存入列表
f = open('data.txt','r')
print(f.readlines())
f.close()

##写入
f = open('/tmp/data.txt','w+')
f.write('Beautiful is better than ugly')
print(f.read())
f.writelines(['Explicit is better than implicit.','Simple is better than complex.'])
print(f.read())
f.close()

## 案例.转换成所有首字母大写的标题格式
with open('data.txt') as inf,open('out.txt','w') as outf:
    for line in inf:
        outf.write(" ".join([word.capitalize() for word in line.split()]))
        outf.write('\n')

with open('out.txt') as of :
    print(of.read())