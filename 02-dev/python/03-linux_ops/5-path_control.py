# _*_ coding=utf-8 _*_
# author:韦博文
# date:2019/10/10
# content:文件内容管理

import sys
import os
import fnmatch
import filecmp
import hashlib

'''
filecmp.cmp('file1','file2')                                ##比较两个文件是否相同，返回布尔值
filecmp.cmpfiles('dir1','dir2',['file1','file2','...'])     ##比较两个目录下指定文件，返回三元组，包括一个相同列表，一个不通列表，一个无法比较列表

compare_result = filecmp.dircmp('dir1','dir2')              ##比较两个目录，返回很多属性
print(compare_result.report())                              ##返回详细比较结果。PS：该函数不会递归比对，子目录仅比对名称，不会比对里面的内容
print(compare_result.left_only)                             ##还有不少属性可以获取，再行研究

##MD5校验
d = hashlib.md5()
with open('/etc/passwd') as f :
    for line in f:
        d.update(line.encode('utf-8'))
print(d.hexdigest())
'''

##实战案例，查找目录下的重复文件
CHUNK_SIZE = 8129                                       ##指定读取字节数，避免打开过大文件

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

def get_chunk(filename) :
    with open (filename) as f :
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            else:
                yield chunk

def get_file_checksum(filename) :
    h = hashlib.md5()
    for chunk in get_chunk(filename) :
        h.update(chunk)
    return h.hexdigest()

def main():
    sys.argv.append("")
    directory = sys.argv[1]
    if not  os.path.isdir(directory):
        raise  SystemExit("{} 不是一个目录".format(directory))

    record = {}                                                             ##定义一个字典，以MD5未key,文件名为value
    for item in find_specific_files(directory) :                            ##遍历目录，获取所有文件
        checksum = get_file_checksum(item)                                  ##获取文件的MD5值
        if checksum in record :
            print('找到一个重复文件:{0}和{1}'.format(record[checksum],item)) ##如MD5值已存在字典中，说明重复
        else:
            record.[checksum] = item

if __name__ == '__main__' :
    main()
