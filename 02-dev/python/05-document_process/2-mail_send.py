# _*_ coding=utf-8 _*_
# author:韦博文
# date:2019/1024
# content:使用标准库smtplib与mime发送邮件

'''
步骤：
    1】连接到SMTP服务器
    2】发送SMTP的“hello”消息
    3】登陆到SMTP服务器
    4】发送电子邮件
    5】关闭SMTP服务器的链接
'''
import smtplib
from email.mime.multipart import MIMEMultipart

s = smtplib.SMTP_SSL("smtp.163.com")
s.connect("smtp.163.com",465)
s.ehlo()
#s.starttls()            ##转成加密会话，非必需
s.login('wbw_1991@163.com','1203wy')

mail_msg = MIMEMultipart()
mail_msg['Subject'] = '测试邮件'
mail_msg['From'] = '韦博文的阿里云服务器'
mail_msg['To'] = "bowen.wei@crgecent.com"
mail_msg.attach('随便发点内容')
sender = 'wbw_1991@163.com'
receiver_list = ['bowen.wei@crgecent.com']
s.sendmail(sender, receiver_list, mail_msg.as_string())  # 发送邮件
s.quit()