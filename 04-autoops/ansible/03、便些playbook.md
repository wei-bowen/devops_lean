
1、语法示例(仅用于语法参考，无实际操作意义)
```yaml
---                                         ##以---开头表明这是一个yaml语法的playbook文件
- include: install_apache.yml               ##可以导入其他playbook文件，调用其变量/任务模块
  vars_files:
    - /vars/vars.file                       ##变量较多时可以卸载特定的变量文件中，然后通过var_file指定var文件的方式引入变量
- hosts: dbserver                           ##指定目标主机清单
  gather-facts: yes                         ##指定是否指定收集系统相关信息，默认为yes,可以no关掉提高部署效率
  vars:
    mysql_port: 3306                        ##自定义变量供后面使用
  remote_user: mysql                        ##指定一个远程用户去执行任务
  become: yes                               ##配合become_method: sudo ，指定使用sudo权限去执行任务
  become_method: sudo   
  tasks:                                    ##任务列表起始生命
  - name: test uname                        ##任务标题，一般起到注释的作用，也可以省略
    shell: echo {{ansible_os_family}}       ##任务信息，格式为{需要调用的模块名: 传入的参数项}获取ansible变量，包含大部分系统信息，可以用ansible -m setup查看可以获取哪些变量
    register: uname                         ##register定义一个变量，获取任务执行的返回结果
  - name: get ipv4 address                  ##获取复合系统信息⬇
    shell: echo {{ansible_eth0["ipv4"]["address"]}}
    register: ipaddress                     
    ignore_errors: True                     ##可以指定忽略错误

  - name: check if the mysql has install
    shell: ps -ef | grep mysql | grep -v grep | wc -l
    register: prc_count

  - name: install mongodb
    yum: name=mongodb-server state=present
    when:
      - prc_count.stdout_lines == '0'       ## 通过.stdout_lines读取shell命令的返回值 
      - ansible_os_family == "Debian"       ##when条件判定，条件成立时任务才会被执行
      - ipaddress == "192.168.122.134"      ##多个条件使用-列表,单个条件直接在when后面
      
  - name: install pre-soft for nginx        
    yum: name={{ item }} state=present
    with_items:                             ##使用列表循环
    - pcre
    - pcre-devel
    - openssl
    - openssl-devel

  - name: copy nginx config file
    template:
      src: /home/lxm/index.html.j2          ##指定一个jinja2模板，自动读取playbook中出现的变量对模板内容进行替换，然后复制到目标端
      dest: /usr/share/nginx/www/index.html
      mode: 644
      
  - name: create directory for nginx
    file: path=/home/oldboy/tools state=directory 
    notify:
    - get nginx install file                ##触发器,当此task成功完成对服务器的修改时，触发notifu,执行对应的handlers
  
  handlers：                                ##注意,handlers只在所有tasks执行完毕后执行，只执行一次，一般用于服务重启
  - name: get nginx install file
    get_url: url=http://download/nginx.tar.gz dest=/opt/install_file/nginx.tar.gz mode=777 user=nginx
  - name: yum install 
    yum: name=nginx state=present
```
    
2、ansible-playbook执行
    ansible-playbook [option] playbook.yml
    options:
            -T          : 简历SSH连接的超时时间
            --key-file  : 建立SSH连接的私钥文件
            -i          : 指定主机清单文件
            -f          : 并发执行的进程数,默认为5
            -C          ：测试脚本
            --step      : 每执行一个任务都停止等待用户确认
            --list-hosts: 放在playbook文件后面，列出匹配的目标服务器
