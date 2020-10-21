**pod的特性：**
- 可以认为是一个虚拟的逻辑主机，是k8s基本构件
- Pod无法跨节点
- pod可以包含多个容器
- Pod在相同命名空间namespace下互通
- Pod内的容器共享一个IP和端口空间，所以Pod容器不应采用相同端口，会引起冲突
- Pod应该包含一组紧密耦合的容器组，支持同时伸缩容

>**查看pod资源**
```shell
kubectl get pods                  ##查看当前默认命名空间内的所有pod资源 
kubectl get pods -n kube-system   ##查看指定命名空间内的pod资源 
kubectl get pods -A               ##查看所有命名空间内的Pod资源 
kubectl get pod kubia             ##查看指定pod kubia的相关信息 
kubectl get pod kubia -o wide     ##查看详细信息 
kubecte get pod kubia -o yaml     ##以yaml格式输出pod的定义信息，同样支持json 
kubectl get pods -l app=kubia     ##指定标签搜寻pod，可以指定多个标签，逗号隔开
kubectl get pods -L=app           ##查看带有标签app的pod(无论标签是否赋值)
kubectl describe pod kubia        ##查看指定Pod的详细定义+状态信息
kubectl logs kubia                ##查看资源日志(不需要指定资源类型)
kubectl logs kubia --previous     ##原来的容器崩溃后控制器会自动重建一个新的pod,加上此参数可以看到pod全部历史日志，否则只能看到新容器启动后的日志
kubectl logs kubia -c nginx       ##查看资源内的容器日志
```
>**运行第一个pod**
```shell
kubectl run kubia --image=luksa/kubia --port=8080 -n default
```
- kubectl run 后接pod名称，运行一个pod
- --iamge= 指定要运行的容器
- --port= 指定容器监听的端口
- -n 指定namespace，可以不指定，默认就是default
>**使用YAML文件创建port**
```shell
kubectl explain pod                                                        ##查看创建一个pod所需的描述字段
kubectl explain pod.spec                                                   ##查看Pod所需的spec字段的详细描述
kubectl explain pod.spec.containers                                        ##查看更底层的对象
kubectl get po kubia -o yaml                                               ##通过查看一个已存在的pod的定义yaml格式的描述作为参照
kubectl run kubia --image=luksa/kubia --port=8080 --dry-run=client -o yaml ##--dry-run=client尝试创建而不实际创建，-o yaml以yaml格式输出创建结果，可以重定向到文件，加以修改后创建
kubectl create -f kubia.yaml                                               ##指定从kubia.yaml创建pod，create可以用apply代替
```
**最终的kubia.yaml格式如下**
```yaml
apiVersion: v1                                                             #使用的kubernetes API版本，可以使用kubectl explain pod看到
kind: Pod                                                                  #创建的kubernetes资源类型
metadata:                                                                  #Pod的元数据，名字、标签、注解等
  labels:                                                                  #标签可以设置多个，对齐即可
    run: kubia                        
  name: kubia
spec:                                                                      #Pod的规格内容，如运行的程序列表、监听的端口、挂载的目录等
  containers:
  - image: luksa/kubia                                                     #运行的docker容器名称，可以是多个，每个都单独一个-image
    name: kubia                                                            #容器的自定名称
    ports:                                                                 #容器的对外监听端口，可以是多个，每个都单独一个- containerPort
    - containerPort: 8080
       protocol: TCP                                                       #端口监听的协议类型，可以不指定，默认为TCP
```
>**利用标签对Pod进行分类，区分访问**
```shell
kubectl get pods --show-labels                                             #查看pod的标签
kubectl get po -l app                                                      #列出包含标签env的Pod，无论其值如何
kubectl get po -l !"app"                                                   #取反，列出不包含标签app的pod
kubectl get po -l app=kubia,env=statle                                     #列出符合标签条件的pod，多个条件逗号隔开
kubectl get po -l app!=kubia
kubectl get po -l app in (v1,app)
kubectl get po -l app notin (v1,app)
kubectl get pods -L run                                                    #列出所有pods，在原来数据项的基础上加上一列run并填上对应的值
```
>**将pod部署到指定标签的节点上**
```yaml
##在yaml定义文件的spec属性下添加nodeSelector
sepc
  nodeSelector	
    gpu: "true"                                                            #添加选择器，要求部署在标签gpu值为true的节点机器上
    os: centos                                                                    #node有默认主机名标签如kubernetes.io/hostname=k8s-node1，可以通过该标签部署到指定机器
                                                                             
```
>**为pod添加注解(跟label类似，也是键值对，但不可用于筛选)**
```yaml
##yaml定义文件的metadata下添加
metadata:
  annotations:
    key1: valuea
    key2: valueb
##或者命令行添加(如果已存在则会直接覆盖)
kubectl annotate pod nfspath key1="valuea",key2="valueb"
```
>**使用namespace对pod资源进行分组**
```shell
kubectl get namespace                                 ##查看所有命名空间，其他类似可选项类似pod，namespace可简写为ns
kubectl create ns test --dry-run=client -o yaml       ##创建新的ns
```
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: test
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
