# _*_ coding=utf-8 _*_
# author:韦博文
# date:2019/10/12
# content:mysql安装

import urllib
import os
import shutil
import tarfile
import subprocess
import ConfigParser

def shell_call(cmd) :
    p = subprocess.Popen(cmd,
                         shell=True,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        return p.returncode, stderr
    return p.returncode, stdout

def installfile_download(url,download_dir='/opt/install_file/') :
    filename = os.path.join(download_dir, os.path.basename(url))
    if os.path.exists(filename) :
        print('{}安装文件下载完成'.format(filename))
        return filename
    print('开始下载安装文件。。。。')
    create_datadir(download_dir)
    urllib.urlretrieve(url, filename)
    print('{}安装文件下载完成'.format(filename))

def unpackage(tar_name,install_dir = '/usr/local') :
    basedir = os.path.join(install_dir,tar_name.split('/')[-1].split('.tar')[0])
    if os.path.exists(basedir):
        shutil.rmtree(basedir)
    print("安装文件{}开始解压到指定的安装目录{}".format(tar_name, install_dir))
    t = tarfile.open(os.path.join(tar_name),'r:gz')
    t.extractall(install_dir)
    return basedir

def dir_link(src_dir,link_file) :
    if os.path.exists(link_file) :
        os.remove(link_file)
    os.symlink(src_dir,link_file)

def create_datadir(data_dir) :
    if os.path.exists(data_dir) :
        shutil.rmtree(data_dir)
    os.makedirs(data_dir)

def format_init_command(basedir,datadir) :
    bin_path = os.path.join(basedir, 'bin/mysqld')
    cmd = "{} --initialize --user=mysql --basedir={} --datadir={}".format(bin_path,basedir,datadir)
    return cmd

def command_init(basedir):
    server_bin = os.path.join(basedir, 'support-files', 'mysql.server')
    shutil.copy(server_bin, '/etc/init.d/mysqld')
    restart_cmd = "{} restart".format('/etc/init.d/mysqld')
    shell_call(restart_cmd)
    link_path = '/usr/local/bin/mysql'
    if os.path.exists(link_path):
        os.remove(link_path)
    os.symlink(os.path.join(basedir, 'bin', 'mysql'), link_path)

def config_init() :
    print('配置my.cnf....')
    cf = ConfigParser.ConfigParser(allow_no_value=True)
    cf.read('/etc/my.cnf')
    if not cf.has_section('mysqld'):
        cf.add_section('mysqld')
    cf.set('mysqld', 'basedir', '/usr/local/mysql')
    cf.set('mysqld', 'datadir', '/usr/local/mysql/data')
    cf.set('mysqld', 'port', '3306')
    cf.set('mysqld', 'socket', '/tmp/mysql.sock')
    cf.set('mysqld', 'pid-file', '/usr/local/mysql/data/mysql.pid')
    cf.set('mysqld', 'log-error', '/usr/local/mysql/data/error.log')
    cf.set('mysqld', 'character_set_server', 'utf8')
    cf.set('mysqld', 'user', 'mysql')
    cf.set('mysqld', 'max_connections', '500')
    cf.set('mysqld', 'symbolic-links', '0')
    cf.set('mysqld', 'skip-grant-tables')
    cf.set('mysqld', '!includedir /etc/my.cnf.d')
    cf.write(open('/etc/my.cnf', 'w'))
    print('配置完成，准备重启')

def main() :
    ##路径定义
    url = 'https://dev.mysql.com/get/Downloads/MySQL-8.0/mysql-8.0.17-el7-x86_64.tar.gz'    #下载路径
    download_dir = '/opt/install_file/'         # 下载文件保存目录
    install_dir = '/usr/local'                  #安装路径
    link_path = '/usr/bin/mysql'                #为了便于管理，建议建立软连接
    data_dir = '/usr/local/mysql/data'          #数据目录

    ##1、建立用户
    shell_call('groupadd mysql')
    shell_call('useradd -M mysql -g mysql -s /sbin/nologin')

    ##2、下载安装文件
    tar_name = installfile_download(url,download_dir)       ##下载安装文件

    ##3、解压到指定目录并建立软链接
    basedir = unpackage(tar_name,install_dir)               ##解压文件到指定安装目录
    dir_link(basedir,link_path)                             ##建立软链接
    create_datadir(data_dir)                                ##建立数据文件目录

    ##4、初始化程序
    cmd = format_init_command(basedir, data_dir)
    print('执行初始化....')
    shell_call(cmd)
    print('初始化完成')

    ###5、初始化参数文件
    config_init()        

    ###6、配置启动命令
    command_init(basedir)
    print('恭喜！mysql安装完成！')

if __name__ == '__main__':
    main()
