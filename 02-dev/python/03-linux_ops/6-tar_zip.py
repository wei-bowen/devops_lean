# _*_ coding=utf-8 _*_
# author:韦博文
# date:2019/10/10
# content:压缩包管理

import os
import tarfile
import fnmatch
import datetime
import shutil
import zipfile


'''
##打包当前目录下所有文件
tar_name = os.getcwd().split('/')[-1] + '.tar'
with tarfile.open(tar_name,mode = 'w') as out :  ##w是普通打包，w:gz 是gz压缩打包，w:bz2
    for file in os.listdir('.') :
        out.add(file)

##查看包内的文件
with tarfile.open(tar_name) as t_file :             ##缺省了参数mode='r'  同理 r:gz是解压读取gz包
    for mem_file in t_file.getmembers() :           ##getmenbers()方法获取包内成员
        print(mem_file.name)

## extract提取单个文件   extractall 提取所有文件


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

##备份案例
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

##zip压缩包的创建
def zipfile_create(path = '.') :
    zip_name = os.path.abspath(path).split('/')[-1] + '.zip'
    print('开始压缩生成{}'.format(zip_name))
    for file in find_specific_files(path,'*.py') :
        newZip = zipfile.ZipFile(zip_name, 'w')
        newZip.write(file)
        newZip.close()
        print('完成文件{}的压缩'.format(file))
    return zip_name


def main():
    patterns = ['*.jpg', '*.png', '*.py']
    now = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    filename = "all_code_{}.tar.gz".format(now)
    with tarfile.open(filename, mode='w:gz') as f:
        for file in find_specific_files("/opt/github/python", patterns):
            f.add(file)
    shutil.move(filename, '/bak/' + filename)

if __name__ == '__main__':
    #main()
    zip_name = zipfile_create('/tmp/pycharm_project_765')            ##创建zip压缩包，不指定目录则默认当前目录
    zip_read = zipfile.ZipFile(zip_name)
    print(zip_read.namelist())

'''

###################命令行直接使用ziopfile
'''
    -l          列出zip包内的文件
        python -m zipfile -l 压缩包名称
    -c          创建压缩包
        python -m zipfile -c 指定压缩包名称 待压缩文件1 文件2 ...
    -e          提取压缩包
        python -m zipfile -e 指定压缩包名称 指定解压路径
    -t          验证是否为有效压缩包
'''
