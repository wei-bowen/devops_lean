# _*_ coding=utf-8 _*_
# author:韦博文
# date:2019/10/16
# content:linux系统监控实战

import socket
from datetime import datetime
import jinja2
import psutil
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def sendmail(subject, msg, receiver_list, sender, smtpaddr,port,password):
    mail_msg = MIMEMultipart()
    mail_msg['Subject'] = subject
    mail_msg['From'] = sender
    mail_msg['To'] = ','.join(receiver_list)
    mail_msg.attach(MIMEText(msg, 'html', 'utf-8'))
    if port == 22 :
        s = smtplib.SMTP()
    else:
        s = smtplib.SMTP_SSL(host=smtpaddr)
    s.connect(smtpaddr,port)                # 连接smtp服务器
    s.ehlo()
    print('ehlo成功')
    print('startsl成功')
    s.login(sender, password)  # 登录邮箱
    print('登陆成功，开始发送。。。')
    s.sendmail(sender, receiver_list, mail_msg.as_string())  # 发送邮件
    s.quit()

def render(tpl_path,**kwargs):
    path,filename = os.path.split(tpl_path)
    return jinja2.Environment(
        loader = jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(**kwargs)

def bytes2human(n) :
    symbols = ('K','M','G','T','P','E','Z','Y')
    prefix = {}
    for i , s in enumerate(symbols) :
        prefix[s] = 1<< (i+1) * 10
    for s in reversed(symbols) :
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value,s)
    return "%sB" % n

def get_cpu_info():
    cpu_count = psutil.cpu_count()
    cpu_percent = psutil.cpu_percent(interval=1)
    return dict(cpu_count=cpu_count,cpu_percent=cpu_percent)

def get_memory_info():
    virtual_mem = psutil.virtual_memory()

    mem_total = bytes2human(virtual_mem.total)
    mem_persent = virtual_mem.percent
    mem_free = bytes2human(virtual_mem.free + virtual_mem.buffers + virtual_mem.cached)
    mem_used = bytes2human(virtual_mem.total * virtual_mem.percent)

    return dict(mem_total=mem_total,mem_persent=mem_persent,mem_free=mem_free,mem_used=mem_used)

def get_disk_info():
    disk_usage = psutil.disk_usage('/')

    disk_total = bytes2human(disk_usage.total)
    disk_persent = disk_usage.percent
    disk_free = bytes2human(disk_usage.free)
    disk_used = bytes2human(disk_usage.used)

    return dict(disk_total=disk_total,disk_persent=disk_persent,disk_free=disk_free,disk_used=disk_used)

def get_boot_info() :
    boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M%S")
    return dict(boot_time=boot_time)

def collect_monitor_date():
    date = {}
    date.update(get_boot_info())
    date.update(get_cpu_info())
    date.update(get_memory_info())
    date.update(get_disk_info())
    return date

def main():

    hostname = socket.gethostname()
    data = collect_monitor_date()
    data.update(dict(hostname=hostname))

    content = render('monitor.html',**data)
    print(content)
    print(os.getcwd())
    print(content)
    print('hello')

    sender = "wbw_1991@163.com"
    smtpaddr = "smtp.163.com"
    receiver_list = ["wbw_1991@163.com", "bowen.wei@crgecent.com"]
    subject = '服务器巡检结果'     # @subject:邮件标题
    password = "1203wy"
    port = 465      ##使用第三方邮件一般默认使用25端口，阿里云服务器封禁25可以改走SSL465端口

    sendmail(subject, content, receiver_list, sender, smtpaddr, port, password)

if __name__ == '__main__':
    main()