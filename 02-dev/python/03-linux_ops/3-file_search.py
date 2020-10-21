# _*_ coding=utf-8 _*_
# author:韦博文
# date:2019/10/10
# content:文件查找

import os
import fnmatch          ##专门用于模糊查找的库
import glob

## print([item for item in os.listdir('.') if item.endswith('.txt')])          ##常规字符串匹配查找

os.system("rm -f {a..b}1.txt {c..d}2.jpg")
os.system("touch {a..b}1.txt {c..d}2.jpg")

'''
fnmatch支持4种统配符：
    *           任意数量字符
    ？          任意单个字符
    [seq]       匹配seq中的字符
    [!seq]      匹配除了seq以外的字符
函数的方法：
    fnmatch     判断文件名是否符合特定的模式，返回布尔值
    fnmatchcase 判断文件名是否符合特定模式，不区分大小写
    filter      返回输入列表符合特定模式的文件名列表
    translate   将通配符模式转换成正则表达式

print([name for name in os.listdir('.') if fnmatch.fnmatch(name,'*.jpg')])
print([filename for filename in os.listdir('.') if fnmatch.fnmatch(filename,'[a-c]*')])
print([filename for filename in os.listdir('.') if fnmatch.fnmatch(filename,'[!a-c]*')])

##filter对列表进行判断
print(fnmatch.filter(os.listdir('.'),'*.txt'))

##上面查找文件时先listir再匹配，当前目录下可以使用简洁的glob
print(glob.glob('*.jpg'))

##os.walk遍历目录树，指定查找文件
file_types = ['*.txt','*.jpg','*.py']
matches = []

##walk遍历时返回三元组(dirpath,dirnames,filenames),分别代表当前遍历到的目录、其下属目录集、其下属文件集
for dirpaths,dirnames,filenames in os.walk(os.path.expanduser('~')):
    print(dirpaths,dirnames,filenames)
    for extensions in file_types:
        for filename in fnmatch.filter(filenames,extensions):
            matches.append(os.path.join(dirpaths,filename))
print(matches)

'''

###实战案例
'''
1）找到某个目录及子目录下最大的十个文件
2）找到某个目录及子目录下最老的十个文件
3）找到某个目录及子目录下所有文件名中包含'mysql'的文件
4）找到某个目录及子目录下，排除.git子目录以后所有Python源文件
'''

def is_file_match(filename,patterns) :
    for pattern in patterns :
        if fnmatch.fnmatch(filename,pattern):
            return True
    return False

def find_specific_files(dirpath,patterns=['*'],exclude_dirs=[]) :
    for dir,dirnames,filenames in os.walk(os.path.abspath(dirpath)):
        for filename in filenames:
            if is_file_match(filename,patterns) :
                yield os.path.join(dir,filename)
        for d in exclude_dirs:
            if d in dirnames:
                dirnames.remove(d)

if __name__ == '__main__' :
    ##查找目录下所有文件
    print([filename for filename in find_specific_files('.')])

    ##查找目录下所有图片
    patterns = ['*.jpg','*.jepg','*.png','*.tif','*.tiff']
    print([filename for filename in find_specific_files('.',patterns)])

    ##查找/opt/github/python下除了03-linux_ops目录以外的其他目录的所有py文件
    print([filename for filename in find_specific_files('/opt/github/python',['*.py'],['03-linux_ops'])])

    ##
    files = {name:os.path.getsize(name) for name in find_specific_files('/opt/github/python')}
    resutlt = sorted(files.items(),key = lambda d:d[1],reverse = True )[:10]
    for i,t in enumerate(resutlt,1) :
        print(i,t[0],t[1])
