## 初识Pod
### pod的特性
- 可以认为是一个虚拟的逻辑主机，是k8s基本构件
- Pod无法跨节点
- pod可以包含多个容器
- pod中的容器可以声明共享同一个Volume
- Pod在相同命名空间namespace下互通
- Pod内的容器共享一个IP和端口空间，所以Pod容器不应采用相同端口，会引起冲突
- Pod应该包含一组紧密耦合的容器组，支持同时伸缩容
- Pod创建时最先创建一个特殊容器infra(k8s.gcr.io/pause)，后面创建的容器再去共享它的网络和存储。

### 运行第一个pod**
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
>静态pod

k8s支持将Pod的定义YAML文件放到指定目录下，kubelet启动时即运行该Pod，无需命令行操作
`cat /var/lib/kubelet/config.yaml | grep static `默认是`staticPodPath: /etc/kubernetes/manifests`，如果没有配置则需要手动配置一下，然后重启kubelet<>
将Pod的定义YAML文件放在指定的/etc/kubernetes/manifests下即可。每个节点都可以这么操作。
### Pod相关属性数据
Pod常用的属性有：
```
apiVersion: v1                      ##调用的接口，可以通过kubectl explain pod查看,必需字段
kind: Pod                           ##资源类型。必需字段
metadata:                           ##基础数据，包含名字、标签、注解等。必需字段
  annotations:                      ##Pod注释，key-value形式
    key: value
  labels:                           ##Pod标签，key-value形式，用于筛选
    key: value
  clusterName: kube                 ##集群名称，默认可不写
  name: kobe                        ##pod名称。必需字段
  namespace: default                ##运行的namespace，默认不写，在default命名空间内运行
spec:                               ##规格数据。必需字段
  activeDeadlineSeconds: 10         ##10秒为启动成功即标记失败
  affinity:                         ##亲和性,调度策略，在《Pod调度策略》中讲到       
  containers:                       ##容器组。必需字段
  hostAliases:                      ##主机名解析，内容在pod初始化时写入/etc/host文件中
  hostname:                         ##容器主机名
  initContainers:                   ##初始化容器,pod启动时最先启动的容器
  nodeName:                         ##指定部署在哪个节点上
  nodeSelector:                     ##节点选择策略
  restartPolicy:                    ##重启策略
  serviceAccount:                   ##服务账户，在《k8s权限控制章节》讲到
  tolerations:                      ##污点容忍
  volumes:                          ##磁盘挂载，在Pod初始化时指定，在containers-image下挂
```
pod.spec.containers常用属性
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

- pod可以挂载磁盘，并给Pod内的容器挂载使用。参考[【磁盘挂载】](./04、磁盘挂载.md)
- Pod内可以接受参数传递。参考[【参数传递】](/.05、向容器传递参数.md)
- pod将运行1-n个容器。
- 容器可以指定资源需求。
### Pod规格设定示例

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
Pod启动时,容器内的/etc/hosts文件将添加两列
```
....
10.1.2.3  foo.remote
10.1.2.3  bar.remote
```
>**为Pod添加终端，接受标准输入**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: busybox
spec:
  containers:
  - name: shell
    image: busybox
    stdin: true
    tty: true
```
- 启动的pod可以通过`kubectl attch Pod名称 -c 容器名称 -it`打开容器交互shell输入指令。**注意**指令输入完成后exit容器将同时关闭，crtl+pq可以退出命令行不关闭容器。<br>
- 也可以执行`kubectl exec <-it> Pod名称 <-c 容器名称> -- 要执行的指令`

更多使用详见后续章节。
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
