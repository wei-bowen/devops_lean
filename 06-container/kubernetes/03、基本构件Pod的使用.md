**pod的特性：**
- 可以认为是一个虚拟的逻辑主机，是k8s基本构件
- Pod无法跨节点
- pod可以包含多个容器
- pod中的容器可以声明共享同一个Volume
- Pod在相同命名空间namespace下互通
- Pod内的容器共享一个IP和端口空间，所以Pod容器不应采用相同端口，会引起冲突
- Pod应该包含一组紧密耦合的容器组，支持同时伸缩容
- Pod创建时最先创建一个特殊容器infra(k8s.gcr.io/pause)，后面创建的容器再去共享它的网络和存储。

>**运行第一个pod**
```shell
kubectl run kubia --image=luksa/kubia --port=8080
```
- kubectl run 后接pod名称，运行一个pod
- --iamge= 指定要运行的容器
- --port= 指定容器监听的端口
- -n 指定namespace，可以不指定，默认就是default

**最终的kubia.yaml格式如下**
```yaml
apiVersion: v1                                                             #使用的kubernetes API版本，可以使用kubectl explain pod看到,必需
kind: Pod                                                                  #创建的kubernetes资源类型,必需
metadata:                                                                  #Pod的元数据，名字、标签、注解等
  labels:                                                                  #标签可以设置多个，对齐即可
    run: kubia                        
  name: kubia                                                              #Pod名称,必需
spec:                                                                      #Pod的规格内容，如运行的程序列表、监听的端口、挂载的目录等
  containers:
  - image: luksa/kubia                                                     #运行的docker容器名称，可以是多个，每个都单独一个-image
    name: kubia                                                            #容器的自定名称
    ports:                                                                 #容器的对外监听端口，可以是多个，每个都单独一个- containerPort
    - containerPort: 8080
       protocol: TCP                                                       #端口监听的协议类型，可以不指定，默认为TCP
```
Pod常用的属性有：
```
apiVersion: v1
kind: Pod
metadata:
  annotations:                      ##Pod注释
    key: value
  labels:                           ##Pod标签，用于筛选
    key: value
  clusterName: kube                 ##集群名称，默认可不写
  name: kobe                        ##pod名称
  namespace: default                ##运行的namespace，默认不写，在default命名空间内运行
spec:
  activeDeadlineSeconds: 10         ##10秒为启动成功即标记失败
  affinity:                         ##亲和性,调度策略，14章将到         
  containers:                       ##容器组。必须字段
  hostAliases:                      ##主机名解析，内容在pod初始化时写入/etc/host文件中
  hostname:                         ##容器主机名
  initContainers:                   ##初始化容器,pod启动时最先启动的容器
  nodeName:                         ##指定部署在哪个节点上
  nodeSelector:                     ##节点选择策略
  restartPolicy:                    ##重启策略
  serviceAccount:                   ##服务账户
  tolerations:                      ##污点容忍
  volumes:                          ##磁盘挂载
```
>**将pod部署到指定标签的节点上**
```yaml
##在yaml定义文件的spec属性下添加nodeSelector
sepc
  nodeSelector	
    gpu: "true"                                                            #添加选择器，要求部署在标签gpu值为true的节点机器上
    os: centos                                                             #node有默认主机名标签如kubernetes.io/hostname=k8s-node1，可以通过该标签部署到指定机器
                                                                             
```
>**为pod添加host解析**
即在/etc/hosts中添加内容
```yaml
apiVersion: v1
kind: Pod
...
spec:
  hostAliases:
  - ip: "10.1.2.3"
    hostnames:
    - "foo.remote"
    - "bar.remote"
...
```
>**指定运行的containers**
- image
```yaml
...
spec:
  containers:
  - image: nginx                        ##一个image一个容器
    name: main
    imagePullPolicy: Never              ##容器拉取策略,Always, Never, IfNotPresent,默认是Always           
    command: ["/bin/bash"]
    args: ["args1","args2","args3"] 
    env:
    - name: who
      value: hi
    envFrom：
    ...                                 ##容器传参，第7章会讲到
    lifecycle：                         ##触发器
      postStart:                        ##启动后执行
        exec:
          command: ["/bin/sh", "-c", "echo Hello from the postStart handler > /usr/share/message"]
      preStop:                          ##即将停止时执行
        exec:
          command: ["/usr/sbin/nginx","-s","quit"]
    livenessProbe：                      ##存活探针
    readinessProbe：                     ##就绪探针
    startupProbe:                        ##启动探针
    ports:
    - containerPort: 8080
      protocol: TCP                      ##默认TCP,支持UDP,SCTP
      name: http-port                    ##默认不写，指定别名，用于其他地方引用
    resources：                          ##为容器申请资源，12章Pod资源使用控制讲到
    stin: true
    tty: ture
    volumeMounts:                        ##磁盘挂载，要跟spec中定义的volumes配合
  - image: image2                        ##多个镜像
    .....
```
>**保持pod的健康**
***可以为pod添加存活探针(liveness probe)，通过探针定期检测容器是否在运行，如果探测失败将重启容器(image级别，非pod级别)
- 1、HTTP GET探针。对指定端口和路径执行HTTP GET请求，相应代码2/3XX认为探测成功，否则失败
```yaml
##yaml定义文件的spec.containers.image下添加,如
spec:
  containers:
  - images: nginx
    name: webserver1
    livenessProbe:                                   ##添加httpget类型的存活探针,对容器的80端口下的heath目录检测，如http://127.0.0.1:80/helthy
      httpGet:
        path: /heathy
        port: 80
      initialDelaySeconds: 15                        ##容器启动后延迟15秒再探测。如果服务启动有延迟，探测的太早会导致失败从而不断重启容器

```
- 2、TCP套接字探针。尝试与容器指定端口建立TCP连接，连接成功则代表探测成功。
```
待完善
```
- 3、Exec探针。容器内执行指定命令，执行后退出状态码为0则探测成功
```
待完善
```
***除了存活探针，还需要就绪探针***
启动容器时，为k8s配置一个等待时间，时间到了就执行第一次就绪检查，就绪了才对外提供服务。如果为就绪继续周期性探测，而不是删除
配置方法类似存活探针。例如exec就绪探针
```yaml
spec:
  containers:
  - image: luksa/kubia
    name: kubia
    readinessProbe:
      exec:
        command:              ##通过执行ls /var/ready查看文件是否存在来判定Pod是否就绪。未就绪就不是running，无法被访问
        - ls
        - /var/ready
```

>**停止和删除pod**
```shell
kubectl delete po kubia
kubectl delete -l app=kubia                           ##删除指定标签的pod
kubectl delete ns test                                ##删除namespace的同时会删除其下所有pod
kubectl delete po --all                               ##删除当前命名空间下的所有pod，保留ns
kubectl delete all --all                              ##删除除ns外所有资源
```
