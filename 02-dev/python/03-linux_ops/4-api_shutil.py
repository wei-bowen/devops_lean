# _*_ coding=utf-8 _*_
# author:韦博文
# date:2019/10/10
# content:高级文件处理接口shutil

import os
import shutil

'''
shutil.copy('src_file','dest_file')                     ##复制文件
shutil.copytree('src_dir','dest_dir')                   ##复制文件夹
shutil.move('src','dest')                               ##复制文件/目录，如果dest是一个目录，则复制到该目录下并命名为dst
shutil.rmtree('dir')                                    ##删除目录，无论是否非空

##PS：如果是删除文件
os.remove('file_name')
os.unlink('filename')
'''

##shutil还可以创建和读取压缩包
##第一参数指定压缩包名称，第二参数指定格式 有gztar/zip,第三个参数默认为当前目录可为空，也可以指定需要打包的目录
shutil.make_archive('tarname','gztar','dirpath')

##解压.第一个参数指定报，第二个指定解压后的目录，默认当前可为空。第三个指定压缩包格式，一般自动识别无需指定
shutil.unpack_archive('filename','extract_dir','format')
