## 通过Service将Pod端口暴露给外部访问
暴露端口的方式可以是端口转发、service、ingress,其中service又分为ClusterIP/NodePort/LoadBalancer

### 端口转发
**原理**：类似iptables，将本机上的某一个端口的流量转发到一个指定的Pod的端口上(这个Pod可以是其他机器上的)。
**实现**：`kubectl port-forward kubia 8888:80`
**效果**：curl 本机IP:8888 时,流量自动跳转到kubia的80端口上

### Service之ClusterIP
**原理**：虚拟一个IP及端口(IP自动虚拟生成的不可ping，网段由kubeadm初始化集群时指定,监听端口自行指定。)，当有集群网络内的流量(外部网络将无法访问)指向该虚拟IP的端口时，将被转发到指定的POD端口上。
![](https://github.com/wei-bowen/devops_lean/blob/main/images/ClusterIP.jpeg)
**实现**：
```shell
kubectl expose pod fortune --name=fortune-http --port=80 --target-port=80 --session-affinity= ClientIP   
```
```yaml
##yaml定义如下
apiVersion: v1
kind: Service
metadata:
  labels:
    app: fortune
  name: fortune-http
spec:
  sessionAffinity= ClientIP   
  ports:
  - port: 80                            ##可以配置多个端口转发，每个端口一个- port
    name: http                          ##非必填项，为该转发设置别名
    protocol: TCP
    targetPort: 80                      ##如果在Pod定义中对容器端口进行了命名，如Pod将80端口命名为http，此处可以填上端口名http
  selector:
    app: fortune
```
- expose暴露
- -name 指定服务名称
- --port=指定创建的服务监听的窗口
- --target-port= 指定服务收到请求后，转发到资源的哪个窗口
- --session-affinity:非必选项。指定将来自同一个IP的所有请求转发至同一个Pod上(多Pod应用时适用)
**效果**：
创建完成后执行 kubectl get svc -o wide 可以看到
```
NAME           TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE   SELECTOR
fortune-http   ClusterIP   10.97.149.76   <none>        80/TCP    65s   app=fortune
```
- CLUSTER-IP: 给服务在集群网络中分配的虚拟网络IP，跟端口配合监听来自集群内的访问，其他资源访问telnet 10.97.149.76 80  可通
- PORT(S)：第一个port跟CLUSTER-IP配合监听集群内部访问
- SELECTOR：服务是与Pod通过标签选择器进行绑定的，所以要求Pod必须带有标签
curl http://10.97.149.76：80 时，请求将被转发到后端带有app=fortune的pod的80端口上。

### Service之NodePort
**原理**：可以理解是clusterIP+端口转发。除了在集群网络内虚拟一个clusterIP以外，还会在pod所在的node机器上打开一个随机端口将监听到的流量转发到clusterIP上
![](https://github.com/wei-bowen/devops_lean/blob/main/images/NodePort.jpeg)
**实现**：
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

```
NAME          READY   STATUS    RESTARTS   AGE     IP                 NODE     NOMINATED NODE   READINESS GATES
kubia-hztvx   1/1     Running   0          2m12s   192.168.40.246   k8s-node1   <none>           <none>
kubia-s5fbn   1/1     Running   0          2m12s   192.168.40.248   k8s-node1   <none>           <none>
kubia-tc2hz   1/1     Running   0          2m12s   192.168.40.247   k8s-node2   <none>           <none>
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
创建后执行`kubectl exec -it curl bash`进入容器内部，执行`curl 192.168.40.246/7/8：8080`均可正确返回容器hostname

然后起一个NodePort类型的Service
 ```yaml
##kubectl expose rs kubia --port=80 --target-port=8080 --name=kubia-http --type=nodePort --dry-run=client -o yaml
apiVersion: v1
kind: Service
metadata:
  name: kubia-http
spec:
  type: NodePort
  ports:
  - port: 80                ##指定服务打开的端口
    protocol: TCP
    targetPort: 8080
    nodePort: 30123         ##指定节点打开的端口，不指定时分配随机端口
  selector:
    app: kubia
 ```
 **效果**：
 执行`kubectl get svc kubia-http`可以看到
 
 ```
 NAME           TYPE           CLUSTER-IP     EXTERNAL-IP      PORT(S)        AGE    SELECTOR
kubia-http     NodePort       http://172.19.12.50   <none>    80:30123/TCP    70s    app=kubia
 ```
 
 - CLUSTER-IP：分配的服务IP ，此时集群网络内访问 http://http://172.19.12.50 将会轮流转发到3个kubia的Pod上
 - PORTS： 前是服务的端口，后面是节点打开的端口。此时可以在k8s集群外(宿主机网络内)通过 http://节点IP:30123访问节点上的Pod

### Service之LoadBalancer
 **效果**：
 >**使用负载均衡对外暴露服务**
 ```yaml
 #kubectl expose rs kubia --name=kubia-loadbalan --type=LoadBalancer --port=80 --target-port=8080 --dry-run=client -o yaml
 apiVersion: v1
kind: Service
metadata:
  name: kubia-loadbalan
spec:
  ports:
  - port: 80
    protocol: TCP
    targetPort: 8080
  selector:
    app: kubia
  type: LoadBalancer
 ```
 
 执行`kubectl get svc kubia-loadbalan`可以看到
 
 ```
 NAME               TYPE           CLUSTER-IP    EXTERNAL-IP     PORT(S)        AGE
kubia-loadbalan   LoadBalancer     172.19.6.52   47.98.111.196   80:30146/TCP   23s
 ```
 
 假如你使用的是公有云，例如阿里云ACK，会发现相对与NodePort，多了一个EXTERNAL-IP。这是云平台给服务开通的一个负载均衡服务的IP(如果是自己的机器，就需要自己配了) <br>
 此时在外网使用http://EXTERNAL-IP  就可以自动负载均衡到3个Pod. 原来的基础功能与NodePORT一致
 
 >**使用Ingress暴露服务**
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
>**让Ingress处理TLS传输**
- 1、创建私钥和证书
```
openssl genrsa -out tls.key 2048

```
openssl签发证书有点问题，先不研究了，掠过

**------------------------------使用headless服务来发现独立的Pod---------------------------------------**
k8s允许客户通过DNS查找发现Pod的IP
- 创建headless服务,其实就是一种clusterip为None的clusterIP
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
>**发现服务**  
- 1、创建服务时记录服务的IP和端口，以后客户端需要访问Pod时再告知。比较麻烦，要记住服务-Pod的对应关系
- 2、通过查看资源的环境变量发现。`kubectl exec fortune env | grep SERVICE`
- 3、通过DNS发现  书里面讲的比较复杂，待研究
>**endpoint**
服务并非和Pod直连，而是通过endpoint。执行`kubectl describe svc fortune-http` 我们可以看到一条属性：Endpoints: 10.244.36.65:80 <br>
也可以直接执行`kubectl get ep kubia-http`查看改endpoint资源的信息（ep与svc同名） <br>
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
**------------------------------ExternalName---------------------------------------**
大意是创建一个域名形式而非IP的svc，用于绑定。Pod局域网DNS解析怎么弄我还不清楚，配置未生效.  请确认您已开通 PrivateZone 服务
```yaml
##ep配置
apiVersion: v1
kind: Endpoints
metadata:
  name: external-svc
subsets:
  - addresses:
    - ip: 192.168.40.246
    ports:
    - port: 8080
  - addresses:
    - ip: 192.168.40.247
    ports:
    - port: 8080
  - addresses:
    - ip: 192.168.40.248
    ports:
    - port: 8080
##svc配置
apiVersion: v1
kind: Service
metadata:
  labels:
    app: external-svc
  name: external-svc
spec:
  externalName: test.weibw.cn
  ports:
  - port: 80
  type: ExternalName
  ```
