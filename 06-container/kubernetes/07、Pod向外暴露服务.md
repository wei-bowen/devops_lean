## 通过Service将Pod端口暴露给外部访问
暴露端口的方式可以是端口转发、service、ingress,其中service又分为ClusterIP/NodePort/LoadBalancer

### 实验准备。
先创建一个kubia应用，配置3个Pod(同时对外服务，返回各自主机名，方便查看负载转发效果)
```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: kubia
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kubia
  template:
    metadata:
      labels:
        app: kubia
    spec:
      containers:
      - image: luska/kubia
        name: main
        ports:
        - containerPort: 8080
```

执行`kubectl get pods -o wide -l app=kubia` 可以看到

```shell
NAME          READY   STATUS    RESTARTS   AGE     IP               NODE        NOMINATED NODE   READINESS GATES
kubia-gbrhf   1/1     Running   0          4h      10.244.169.164   k8s-node2   <none>           <none>
kubia-jg4nk   1/1     Running   0          3h54m   10.244.36.90     k8s-node1   <none>           <none>
kubia-jzq82   1/1     Running   0          4h      10.244.36.89     k8s-node1   <none>           <none>
```

新建一个curl应用用于访问集群Pod
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: centos
spec:
  containers:
  - image: centos
    name: main
    command: ["sleep","9999999"]
```
创建后执行
```shell
kubectl exec centos -- curl -s http://10.244.169.164:8080           ## 获得结果You've hit kubia-gbrhf
kubectl exec centos -- curl -s http://10.244.36.90:8080             ## 获得结果You've hit kubia-jg4nk
kubectl exec centos -- curl -s http://10.244.36.89:8080             ## 获得结果You've hit kubia-jzq82
```
可以看到访问不同IP时会返回其Pod的NAME

### 1、端口转发
- **原理**：类似iptables，将本机上的某一个端口的流量转发到一个指定的Pod的端口上(这个Pod可以是其他机器上的)。
- **实现**：我们在master节点上执行`kubectl port-forward kubia-gbrhf 80:8080`   将master节点上的80 端口映射到pod(kubia-gbrhf)的8080端口上
- **效果**：此时再curl http://master节点IP:80 时,流量自动跳转到kubia-gbrhf的8080端口上,获得返回结果You've hit kubia-gbrhf

### 2、Service之ClusterIP
- **原理**：虚拟一个IP及端口(IP自动虚拟生成的不可ping，网段由kubeadm初始化集群时指定,监听端口自行指定。)，当有集群网络内的流量(外部网络将无法访问)指向该虚拟IP的端口时，将被转发到指定的POD端口上。<br>
![](https://github.com/wei-bowen/devops_lean/blob/main/images/ClusterIP.jpeg)

- **实现**：
```shell
kubectl expose replicaset kubia --name=kubia-http --port=80 --target-port=8080 --dry-run=client -o yaml
```
```yaml
##yaml定义如下
metadata:
  name: kubia-http
spec:
  ports:
  - port: 80
    protocol: TCP
    targetPort: 8080
  selector:
    app: kubia
```
- expose暴露
- --name 指定服务名称
- --port=指定创建的服务监听的窗口
- --target-port= 指定服务收到请求后，转发到资源的哪个窗口

创建完成后执行`kubectl get service kubia-http -o wide`可以看到
```
NAME         TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE    SELECTOR
kubia-http   ClusterIP   10.108.107.55   <none>        80/TCP    2m3s   app=kubia
```
- CLUSTER-IP: 给服务在集群网络中分配的虚拟网络IP，跟端口配合监听来自集群内的访问，其他资源访问`telnet 10.108.107.55 80`  可通
- PORT(S)：第一个port跟CLUSTER-IP配合监听集群内部访问
- SELECTOR：服务是与Pod通过标签选择器进行绑定的，所以要求Pod必须带有标签
- **效果**：
连续多次执行`kubectl exec centos -- curl -s http://10.108.107.55:80` 时，请求将被转发到后端带有app=kubia的pod的8080端口上,可以看到会三个Pod都有机会访问到。

### Service之NodePort
- **原理**：
可以理解是clusterIP+端口转发。除了在集群网络内虚拟一个clusterIP以外，还会在pod所在的node机器上打开一个随机端口将监听到的流量转发到clusterIP上<br>
![](https://github.com/wei-bowen/devops_lean/blob/main/images/NodePort%20.jpeg)
- **实现**：
 ```yaml
##kubectl expose replicaset kubia --name=kubia-nodeport --port=80 --target-port=8080 --type=NodePort --dry-run=client -o yaml
apiVersion: v1
kind: Service
metadata:
  creationTimestamp: null
  name: kubia-nodeport
spec:
  ports:
  - port: 80
    protocol: TCP
    targetPort: 8080
    nodePort: 33333               ##这个可以不指定，由系统自动分配
  selector:
    app: kubia
  type: NodePort
 ```
 执行`kubectl get svc kubia-nodeport -o wide`可以看到
 ```shell
NAME             TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE   SELECTOR
kubia-nodeport   NodePort   10.97.243.47   <none>        80:31961/TCP   43s   app=kubia
 ```
 PORT(S) 80:31961/TCP :   80是服务的监听端口,31961是node节点打开的转发端口
 - **效果**：
 此时执行`kubectl exec centos -- curl -s http://10.97.243.47:80` 效果与上面clusterIP效果是一样的。
 在集群网络外,直接执行`curl -s http://node节点IP:31961` 访问将会转发到http://10.97.243.47:80 ，获得同样效果。

### 2、Service之LoadBalancer
- **原理：** 可以理解是在NodePort的基础上再起一个负载均衡服务。外部用户访问该服务时会通过均衡算法转发到节点的NodePort上，然后NodePort再转发到clusterIP服务上，再转Pod端口。
![](https://github.com/wei-bowen/devops_lean/blob/main/images/LoadBalancer.jpg.jpeg)
 - **实现：**
 ```yaml
 #kubectl expose replicaset kubia --name=kubia-balancer --port=80 --target-port=8080 --type=LoadBalancer --dry-run=client -o yaml
 apiVersion: v1
kind: Service
metadata:
  name: kubia-balancer
spec:
  ports:
  - port: 80
    protocol: TCP
    targetPort: 8080
  selector:
    app: kubia
  type: LoadBalancer
 ```
 执行`kubectl get svc kubia-balancer -o wide`可以看到
 
 ```
NAME             TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE    SELECTOR
kubia-balancer   LoadBalancer   10.96.113.67   <pending>     80:32183/TCP   2m7s   app=kubia
 ```
 - **效果：**
 此时看到EXTERNAL-IP不再是为空的状态，而是pending准备中。这是因为实在私网中搭建的k8s集群，并没有配置自动起给分配负载均衡地址的服务。<br>
 假如你使用的是公有云，例如阿里云ACK，就会自动向云平台申请一个LBS，并分配一个负载均衡的IP：EXTERNAL-IP。有兴趣也可以自己研究在私网配置负载均衡服务，参考[为私有Kubernetes集群创建LoadBalancer服务](https://www.jianshu.com/p/263185800214)<br>
 此时在外网使用http://EXTERNAL-IP  就可以自动负载均衡到节点的NodePort. 也具备其他和NodePORT一样的访问方式。

### 使用Ingress暴露服务
- **原理：** 更高级别形式的负载均衡，类似nginx的和反向代理负载均衡。LoadBalancer只能基于四层的转发，当我们的集群网络中由多个需要被外部网络访问的网站时，我们就需要为每一个网站分配一个LoadBalancer服务，消耗多个公网IP。而如果配置了Ingress服务，就可以基于七层协议进行即域名进行转发，只需要一个Ingress消耗一个公网IP。 <br>
![](https://github.com/wei-bowen/devops_lean/blob/main/images/Ingress.jpg.jpeg)
 - **实现:** 下面只是一个大概的示范
 ```yaml
 apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: web-forward
spec:
  rules:
  - host: kubia.weibw.com                     ##定义一个域名，当ingress的IP:端口接受到请求头和目录时，转发到指定的服务上
    http:
      paths:                                  ##即 curl请求http://kubia.weibw.com/时会被转发到服务kubia-loadbalan
      - path: /
        backend:
          serviceName: kubia-loadbalan
          servicePort: 80
  - host: fortune.weibw.com                   ##配置多条转发时可以基于host,也可以基于path
    http:
      paths:
      - path: /
        backend:
          serviceName: fortune-http
          servicePort: 80
       - path: /heathy                    ##这个是一个示例，可以将http://fortune.weibw.com/heathy 转发到fortune-heath-check服务的8585端口
         backend:
          serviceName: fortune-heath-check
          servicePort: 8585
 ```
 执行`kubectl get ingresses web-forward -o wide`可以看到
 ```
NAME          HOSTS                               ADDRESS       PORTS   AGE
web-forward   kubia.weibw.com,fortune.weibw.com   47.96.31.87   80      10m
```
添加47.96.31.87 kubia.weibw.com和47.96.31.87 fortune.weibw.com两条解析后，输入解析的网址即可自动转发到不同的服务上。
>**本地ingress置备器** 
`wget https://raw.githubusercontent.com/kubernetes/ingress-nginx/nginx-0.30.0/deploy/static/mandatory.yaml`
镜像换成国内镜像`lizhenliang/nginx-ingress-controller:0.30.0`即可,template.spec下配置一个hostNetwork: true即可绑定到宿主机网络上。<>
原理大概就是起一个nginx的pod，然后该Pod使用了宿主机的80/443的监听。当我们创建ingress规则时，这个pod将在其nginx.conf配置文件中写上转发规则。然后我们访问该Pod的宿主机的80/443端口时，Pod根据接受的host请求，按照规则去转发给后端的services

### 创建服务时的其他常用可选项
```
.....
spec:
  session-affinity: ClientIP      ##会话亲和性，来自同一个客户端IP的请求将会始终被转发到同一个Pod上
  externalTrafficPolicy: Local    ##节点端口的转发策略，当节点端口收到访问请求时，始终将请求转发到本节点的Pod上，避免转发到其他节点浪费流量。
```
>**endpoint**
服务并非和Pod直连，而是通过endpoint。执行`kubectl describe svc kubia-http` 我们可以看到一条属性：
`Endpoints:         10.244.169.164:8080,10.244.36.89:8080,10.244.36.90:8080`<br>
也可以直接执行`kubectl get ep kubia-http`查看该endpoint资源的信息（ep与svc同名） <br>
ep用于存储Pod的IP端口，当客户端连接到服务时，服务代理从中ep记录的IP端口中选择一个进行重定向。 <br>
ep和服务可以单独进行定义。解耦的好处：svc选择ep,ep选择Pod，svc就不必必须通过标签选择器去选择Pod
```yaml
##先创建无选择器的SVC
apiVersion: v1
kind: Service
metadata:
  name: external-svc
spec:
  ports:
  - port: 80
##创建同名ep即可自动关联
apiVersion: v1
kind: Endpoints
metadata:
  name: external-svc
subsets:
  - addresses:
    - ip: 11.11.11.11
    - ip: 22.22.22.22
    ports:
    - port: 80
```
### 发现服务  
- 1、创建服务时记录服务的IP和端口，以后客户端需要访问Pod时再告知。比较麻烦，要记住服务-Pod的对应关系
- 2、通过查看资源的环境变量发现。`kubectl exec fortune env | grep SERVICE`
- 3、通过DNS发现： kube-system空间下有一个kube-dns的dns服务器，会存有解析所有服务的记录。当我们创建pod时，会默认指定其为dns服务器。服务只需要预先知道服务名称端口等信息即可，不必等到IP分配。访问格式为：服务名.所在命名空间.scv.cluster.local. 如果是在同一命名空间下的话只需要服务名字即可访问。例如访问http://kubia-http 即可跳转到kubia-http服务的访问接口。理论上是要指定服务端口的，但是如果使用了标准端口就可以省略。

### 使用headless服务来发现独立的Pod
k8s允许客户通过DNS查找发现Pod的IP
- 创建headless服务,其实就是一种不分配集群IP的的clusterIP
```yaml
##kubectl expose rs kubia --name=kubia-headless --type=ClusterIP --cluster-ip=none --port=80 --target-port=8080 --dry-run=client -o yaml
apiVersion: v1
kind: Service
metadata:
  name: kubia-headless
spec:
  clusterIP: None
  ports:
  - port: 80
    targetPort: 8080
  selector:
    app: kubia
  type； ClusterIP               ##不指定默认就是ClusterIP,命令行也是
```
创建完成后，在集群网络内使用dns解析即可返回服务背后所有就绪的Pod
```
[root@centos /]# nslookup kubia-headless1
Server:         100.100.2.138
Address:        100.100.2.138#53

** server can't find kubia-headless1: NXDOMAIN

[root@centos /]# nslookup kubia-headless1
Server:         100.100.2.138
Address:        100.100.2.138#53

Non-authoritative answer:
Name:   kubia-headless1.default.svc.cluster.local.c713dd1f4ce8a499081cb99c835a69d91
Address: 192.168.40.247
Name:   kubia-headless1.default.svc.cluster.local.c713dd1f4ce8a499081cb99c835a69d91
Address: 192.168.40.246
Name:   kubia-headless1.default.svc.cluster.local.c713dd1f4ce8a499081cb99c835a69d91
Address: 192.168.40.248
** server can't find kubia-headless1.default.svc.cluster.local.c713dd1f4ce8a499081cb99c835a69d91: NXDOMAIN
```
以上仅包含了就绪的Pod，如果需要同时返回未就绪Pod，定义Service的时候要添加注解
```yaml
metadata
  annotations:
    service.alpha.kubernetes.io/tolerate-unready-endpoints: "true"
   name: kubia-headless
spec:
  ........
```
