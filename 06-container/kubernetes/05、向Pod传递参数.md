## 向容器传递参数
### 实验准备
>准备一个需要传入参数的镜像luksa/fortune:args
写一个脚本，调用fortune程序定时往一个文件写一句外国名言
```shell
#!/bin/bash
trap "exit" SIGINT
INTERVAL=$1
echo "Configured to generate new fortune every $INTERVAL seconds"
mkdir -p /var/htdocs
while :
do 
   echo $(date) Writing fortune to /var/htdocs/index.html
   /usr/bin/fortune > /var/htdocs/index.html
   sleep $INTERVAL
done
```
再建一个Docker镜像，基于乌班图，安装好fortune程序，然后按照传入的时间间隔执行上面哪个脚本。
```groovy
FROM ubuntu
RUN apt-get update ; apt-get -y install fortune
ADD fortuneloop.sh /bin/fortuneloop.sh
ENTRYPOINT ["/bin/fortuneloop.sh"]
CMD ["10"]
```
以上的脚本是为了帮助理解原理，实际操作直接下载镜像luksa/fortune:args即可 <br>
执行`docker run -it luksa/fortune:args`就能看到每隔10秒写名言
```shell
[root@k8s-master ~]# docker run -it luksa/fortune:args
Unable to find image 'luksa/fortune:args' locally
args: Pulling from luksa/fortune
.....
Configured to generate new fortune every 10 seconds
Mon Sep 21 12:58:34 UTC 2020 Writing fortune to /var/htdocs/index.html
Mon Sep 21 12:58:44 UTC 2020 Writing fortune to /var/htdocs/index.html
.....
```
>再准备一个直接从系统变量中读取参数的镜像luksa/fortune:env
相比上面的镜像，删除了`INTERVAL=$1`,即不再主动传入参数。
```shell
#!/bin/bash
trap "exit" SIGINT
echo "Configured to generate new fortune every $INTERVAL seconds"
mkdir -p /var/htdocs
while :
do 
   echo $(date) Writing fortune to /var/htdocs/index.html
   /usr/bin/fortune > /var/htdocs/index.html
   sleep $INTERVAL
done
```
### 1、Pod建立时传入参数
上面建立的容器默认是10秒打印一句名言，我们可以在定义Pod可以将docker镜像的ENTRYPOINT和CMD覆盖，格式如下
```yaml
......
spec:
  containers:
  - image: luksa/fortune:args
    command: ["/bin/command"]                       ##等同于ENTRYPOINT
    args: ["args1","args2","args3"]                 ##等同于CMD，采用上面的列表形式也可
```
操作中我们只要指定args，即可实现15秒打印一次名言警句
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fortune15s
spec:
  containers:
  - image: luksa/fortune:args
    args: ["15"]                  ##args 传入参数即可如果要传入多个参数 则是   args:
    name: html-generator                                                    - args1
    volumeMounts:                                                           - args2
    ....                                                                    - .....
     ...
```
### 2、为容器设置环境变量
Pod定义时传入环境变量，代码如下：
```yaml
spec:
  containers:
  - image: luksa/fortune:env
    name: html-generator
    env:
    - name: INTERVAL
      value: 30                                 ##在这里把环境变量定义进去。多个变量多个- 写入
    - name: time
      value: "$(INTERVAL)s"                     ##引用其他环境变量，这样time="30s"  此处是多余的，只是演示知识点
    ....
```
### 3、利用ConfigMap/secret传递参数
- ConfigMap/secret都是以key-value键值对的形式存储条目
- ConfigMap/secret既支持直接读取条目，也支持以文件的形式进行挂载
- ConfigMap/secret可以通过 --from-literal=key=value 添加1~n条条目，也支持--from-file=<key=>文本文件添加条目，如果key省略则将文件名作为key。还支持--from-file=文件夹添加条目，文件夹下所有文件都被添加，key是文件名，value是文件内容。

**示例场景**：起一个mysql应用，指定root密码qw1203和初始化配置文件my.cnf(指定33106端口替代默认的3306端口),同时创建一个zabbix用户，密码zabbix1203，配一个zabbix数据库
- 1、非敏感数据使用configmap存储

`kubectl create configmap mysql-config --from-literal=MYSQL_DATABASE=zabbix --from-literal=MYSQL_USER=zabbix --from-file=my.cnf --dry-run=client -o yaml` 
```yaml
apiVersion: v1
data:
  MYSQL_DATABASE: zabbix
  MYSQL_USER: zabbix
  my.cnf: "[client]\nport = 33106\nsocket = /tmp/mysql.sock\n\n[mysqld]\nport = 33106\ninit-connect='SET
    NAMES utf8'\nbasedir=/usr/local/mysql                      \t\t    #根据自己的安装目录填写
    \ndatadir=/opt/mysql/data                               #根据自己的mysql数据目录填写\nsocket=/tmp/mysql.sock\nmax_connections=200
    \                            \t    # 允许最大连接数\ncharacter-set-server=utf8                   \t\t
    \     # 服务端使用的字符集默认为8比特编码的latin1字符集\ndefault-storage-engine=INNODB             \t\t
    \       # 创建新表时将使用的默认存储引擎\nexplicit_defaults_for_timestamp=true\n#\n## include
    all files from the config directory\n##\n#!includedir /etc/my.cnf.d\n"
kind: ConfigMap
metadata:
  name: mysql-config
````
- 2、敏感数据使用secret存储

secret用法 `kubectl create secret [flag] 名称 [option]` 基本与configMap相同，多了个flag. 有三个选项。docker-registry(创建一个给 Docker registry 使用的 secret)
  generic(从本地 file, directory 或者 literal value 创建一个 secret)、tls（创建一个 TLS secret） <br>
此处创建本地secret
`kubectl create secret generic mysql-passwd --from-literal=MYSQL_ROOT_PASSWORD=qw1203 --from-literal=MYSQL_PASSWORD=zabbix1203 --dry-run=client -o yaml`
```yaml
apiVersion: v1
data:
  MYSQL_PASSWORD: emFiYml4MTIwMw==              ##yaml定义文件中，数据需要经过base64编码加密。 echo -n "qw1203" | base64
  MYSQL_ROOT_PASSWORD: cXcxMjAz
kind: Secret
metadata:
  name: mysql-passwd
```
- 在Pod中引用这些数据
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mysql
  labels:
    app: mysql
spec:
  containers:
  - name: mysql
    image: mysql/mysql-server
    ports:
    - containerPort: 33106
    env:
    - name: MYSQL_ROOT_PASSWORD
      valueFrom:
        secretKeyRef:
          name: mysql-passwd
          key: MYSQL_ROOT_PASSWORD
    - name: MYSQL_DATABASE
      valueFrom:
        configMapKeyRef:
          name: mysql-config
          key: MYSQL_DATABASE
    - name: MYSQL_USER
      valueFrom:
        configMapKeyRef:
          name: mysql-config
          key: MYSQL_USER
    - name: MYSQL_PASSWORD
      valueFrom:
        secretKeyRef:
          name: mysql-passwd
          key: MYSQL_PASSWORD
    volumeMounts:
    - name: my-cnf                        ##指定要挂载的卷
      mountPath: /etc/my.cnf              ##如果是挂载的卷是单个文件，就需要指定挂载成哪个文件，如果是文件夹，对应的，这里指定文件夹名称
      subPath: my.cnf                     ##挂载的是单个文件还要指定卷中的文件名称
  volumes:                                ##卷挂载的话，config/secret变动时，卷跟着变动，如果是读成变量的话则不会
  - name: my-cnf
    configMap:
      name: mysql-config
      defaultMode: "6660"                 ##非必须，设定默认文件属性
      - key: my.cnf                       ##指定了单条目的话，就有为其单独设定key名称
        path: my.cnf                      ##同时还要指定存储在哪个文件中
```
`kubectl exec -it mysql-server -- bash`进入容器内即可验证数据库root密码1203,且创了一个zabbix，可以用zabbix/zabbix1203登陆
- configMap/secret其他读法
**使用envFrom一次性读取所有参数**
```yaml
...
spec:
  containers:
  - name: mysql
    image: mysql/mysql-server
    ports:
    - containerPort: 33106
    envFrom:
    - configMapRef:
      prefix：                       ## 可以为configMap中读到的条目添加前缀，也可以不要这个
        name: mysql-config           ## 注意，条目的key不允许含有-破折号，非法不能导入，但不会报错
    - secretRef:
        name: mysql-passwd
 .....
```
**以projected形式挂载secret**
```yaml
spec:
  volumes:
  - name: mysql-conf
    projectd:
      sources:
      - secret:
          name: mysql-passwd
      - configMap:
          name: mysql-config
```
**secret的其他用法**
- 1、创建TLS类型的secret
`kubectl create secret tls tls-secret --cert=tls.cert --key=tls.key` (cert和key文件是openssl等软件做好的，用于加密认证的)
```yaml
...
kind: Ingress
metadata:
  name: test
spec:
 tls:
 - host:
   - test.weibw.cn
   secretName: tls-secret        ##即可通过TLS连接来访问服务

```
- 2、创建用于Docker镜像仓库鉴权的Scret
`kubectl create secret docker-registry 自定义secret名称 --docker-username=DockerHub用户名 --docker-password=密码 --docker-email=邮箱地址`
然后可以吧DockerHub主目录下的.dockercfg文件拉下来
```yaml
apiVersion: vi
kind: Pod
metadata:
  name: tesy-poe
spec:
  imagePullSecrets:
  - name: 自定义secret名称            ##跟上面创建的secret名称对应.必须经过鉴权才能拉取私人的镜像
  containers:
  - image: DockerHub用户名/私人镜像名称:tag
    name: main
.....
```
### Downward API
当Pod中运行的程序需要知道Pod的IP地址等(在Pod被创建之前无法被预置的信息)时,可以通过Downward API给这些进程暴露Pod的元数据。可以暴露的信息包括：
- **Pod的名称**：metadata.name
- **Pod的IP地址**：status.podIP
- **Pod所在的命名空间**：metadata.namespace
- **Pod运行节点的名称**：spec.nodeName
- **Pod运行所归属的服务账户的名称**：spec.serviceAccount
- **每个容器请求的CPU和内存的使用量**：reources.request
- **每个容器可以使用的CPU和内存的限制**：limits.memory
- **Pod的标签**
- **Pod的注解**
以上信息都可以在创建Pod后通过`kubectl get pod PodName -o yaml`获取
>**1、通过环境变量暴露元数据**
具体用法可以参照`kubectl explain pod.spec.containers.env.valueFrom`.其中属性数据使用的是`pod.spec.containers.env.valueFrom.fieldRef`，资源则是`kubectl explain pod.spec.containers.env.valueFrom.resourceFieldRef`
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: downward
spec:
  containers:
  - name: main
    image: busybox                          ##如果是虚拟机跑k8s,处理器的虚拟化Intel..选项要勾选
    command: ["sleep","99999999"]
    resources:
      requests:
        cpu: 15m
        memory: 100Ki
      limits:
        cpu: 100m
        memory: 4Mi
    env:
    - name: POD_NAME
      valueFrom:
        fieldRef:
          fieldPath: metadata.name
    - name: POD_NAMESPACE
      valueFrom:
        fieldRef:
          fieldPath: metadata.namespace
    - name: POD_ID
      valueFrom:
        fieldRef:
          fieldPath: status.podIP
    - name: NODE_NAME
      valueFrom:
        fieldRef:
          fieldPath: spec.nodeName
    - name: SERVICE_ACCOUNT
      valueFrom:
        fieldRef:
          fieldPath: spec.serviceAccountName
    - name: CONTAINER_CPU_REQUEST_MILLICORES
      valueFrom:
        resourceFieldRef:
          resource: requests.cpu
          divisor: 1m
    - name: CONTAINER_MEMORY_REQUEST_KIBIBYTES
      valueFrom:
        resourceFieldRef:
          resource: limits.memory
          divisor: 1Ki
```
执行`kubectl exec downward -- env` 即可看到环境变量已正确获取Pod的元数据
```
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
HOSTNAME=downward
CONTAINER_CPU_REQUEST_MILLICORES=15
CONTAINER_MEMORY_REQUEST_KIBIBYTES=4096
POD_NAME=downward
POD_NAMESPACE=default
.....
HOME=/root
```
>**2、通过downwardAPI卷来传递元数据**
元数据均支持以卷的形似挂载。标签和注解只能以卷的形式挂载。用法可以`kubectl explain pod.spec.volumes.downwardAPI`,例子：
```yaml
...
spec:
  volumes:
  - name: downward-env
    downwardAPI：
      items:                                    ##卷内将包含多个文件
      - path: pathName
        mode: 644
        fieldRef:
          fieldPath: metadata.name
      - path: pathName2
        mode: 421
        resourceFieldRef:
          containerName: CtnerName
          resource:: limits.memory
          .....
```
**示例：**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: downward-volume
  labels:                       ##相比上一个yaml多了标签和注释，后面将暴露这些信息
    foo: bar
  annotations:
    key1: value1
    key2: |
      multi
      line
      value
spec:
  containers:
  - name: main
    image: busybox
    command: ["sleep","99999999"]
    resources:
      requests:
        cpu: 15m
        memory: 100Ki
      limits:
        cpu: 100m
        memory: 4Mi
    volumeMounts:
    - name: downward
      mountPath: /etc/downward
  volumes:
  - name: downward
    downwardAPI:
      items:
      - path: "POD_NAME"
        fieldRef:
          fieldPath: metadata.name
      - path: "POD_NAMESPACE"
        fieldRef:
          fieldPath: metadata.namespace
      - path: "labels"
        fieldRef:
          fieldPath: metadata.labels
      - path: "annotations"
        fieldRef:
          fieldPath: metadata.annotations
      - path: "CONTAINER_CPU_REQUEST_MILLICORES"
        resourceFieldRef:
          containerName: main
          resource: requests.cpu
          divisor: 1m
      - path: "CONTAINER_MEMORY_REQUEST_KIBIBYTES"
        resourceFieldRef:
          containerName: main
          resource: limits.memory
          divisor: 1
 ```
 执行命令查看
 ```shell
[root@k8s-master ~]# kubectl exec downward-volume -- ls -lL /etc/downward
total 24
-rw-r--r--    1 root     root             2 Sep 23 15:03 CONTAINER_CPU_REQUEST_MILLICORES
-rw-r--r--    1 root     root             7 Sep 23 15:03 CONTAINER_MEMORY_REQUEST_KIBIBYTES
-rw-r--r--    1 root     root            15 Sep 23 15:03 POD_NAME
-rw-r--r--    1 root     root             7 Sep 23 15:03 POD_NAMESPACE
-rw-r--r--    1 root     root          1467 Sep 23 15:03 annotations
-rw-r--r--    1 root     root             9 Sep 23 15:03 labels
 ```
 **此时我们可以执行`kubectl edit pod downward` 和 `kubectl edit pod downward-volume` 分别对它们的注释annotions进行改动 <br>
 然后再执行`kubectl exec downward --env`和`kubectl exec downward-volume -- cat /etc/downward/annotations` 查看标签。
 发现卷挂载的发生更新，环境变量暴露的没有更新。**
### ServiceAccountToken
