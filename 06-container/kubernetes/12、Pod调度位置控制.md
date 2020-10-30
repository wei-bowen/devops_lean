## 如何影响Pod被调度到哪个节点
### 1、直接通过nodename指定节点
```yaml
...
spec:
  nodeName: k8s-master
  containers:
  - image: nginx
    .....
```
### 2、nodeSlector，根据设定的规则通过标签筛选来选择节点
```yaml
...
spec:
  nodeSelector:               
    os: centos
  containers:
  - image: nginx
    ....
```
或者在控制器模板中使用selector
```yaml
...
kind: Deployment
metadata: 
  name: dev-app
spec:
  selector:
    matchExpressions:
    - {key: os,operator: In,values: [value1,value2]}
    matchLabels:
      os: centos
  tmplate:
  ...
```
### 3、设置Node污点和Pod容忍度来阻止Pod调度到特定节点
>**污点**
- 以master节点为例，执行`kubectl describe nodes k8s-master | grep Taints`可以看到污点Taints
```
Taints: node-role.kubernetes.io/master:NoSchedule     ##污点的格式是`key=<value>:<effect>` 污点名称=<污点值>:<污点影响度>，这事是缺省了value的污点
```
**影响度effect**<br>
- NoSchedule:不容忍则不能调度在此节点<br>
- PreferNoSchedule:尽量阻止调度这个节点上，如果没有其他节点可以调度的话依然可以调度到这里<br>
- NoExecute:不仅禁止不容忍的Pod调度到此节点，已经调度的但是没容忍的也会被驱逐。<br>

>**打污点**
- 示例，给node1打个污点，限定只能部署生产应用
`kubectl taint node k8s-node1 node-type=production:NoSchedule` <br>
然后创建一个3节点的deployment，replicaset也行
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: test
  name: test
spec:
  replicas: 3
  selector:
    matchLabels:
      app: test
  template:
    metadata:
      labels:
        app: test
    spec:
      containers:
      - image: busybox
        imagePullPolicy: Always
        name: busybox
        command: ["sleep","99999"]
```
执行`kubectl apply -f test-dp.yaml`开始部署，然后`kubectl get pod`可以看到
```
NAME                    READY   STATUS              RESTARTS   AGE   IP               NODE        NOMINATED NODE   READINESS GATES
test-76658cf858-78fjf   0/1     ContainerCreating   0          11s   <none>           k8s-node2   <none>           <none>
test-76658cf858-chbm6   0/1     ContainerCreating   0          11s   <none>           k8s-node2   <none>           <none>
test-76658cf858-llg9p   0/1     ContainerCreating   0          11s   <none>           k8s-node2   <none>           <none>
```
全部调度在2节点上
>**设置Pod容忍度**
重新设定deployment中Pod的容忍度
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: test
  name: test
spec:
  replicas: 3
  selector:
    matchLabels:
      app: test
  template:
    metadata:
      labels:
        app: test
    spec:
      containers:
      - image: busybox
        imagePullPolicy: Always
        name: busybox
        command: ["sleep","99999"]
      tolerations:
      - key: node-type
        operator: Equal
        value: production
        effect: NoSchedule
```
这样Pod就可以调度到node1上了
>**配置节点失效后Pod重新调度最长等待时长**
```yaml
      tolerations:
      - key: node.alpha.kubernetes.io/notReady          ##当所在节点处于notReady状态
        operator: Exists
        effect: NoExecute
        tokerationSeconds: 300                          ##持续300时，Pod被重新调度
      - key: node.alpha.kubernetes.io/unreachable       ##当所在节点处于unreachable状态
        operator: Exists                                ##当污点无value时，可以用Exists匹配污点
        effect: NoExecute
        tokerationSeconds: 300
```
>**删除污点**

`kubectl taint node k8s-node1 node-type-`

### 3、使用节点亲缘性将Pod调度到特定节点上
亲缘性有3种，是否亲缘的依据都是标签
- Pod.spec.affinity.nodeAffinity    节点亲缘性
- Pod.spec.affinity.podAffinity     Pod亲缘性
- Pod.spec.affinity.podAntiAffinity Pod排斥性
每种亲缘性下面都有是2个调度条件，都是调度之前影响，不影响已经调度好的Pod
- requiredDuringSchedulingIgnoredDuringExecution    符合条件才调度。
- preferredDuringSchedulingIgnoredDuringExecution   最好符合条件再调度,实在没地方去也可以调度。
>**2.3、在控制器模板中使用强制性节点亲缘性规则**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: testdp1
  name: testdp1
spec:
  replicas: 5
  selector:
    matchLabels:
      app: testdp1
  template:
    metadata:
      labels:
        app: testdp1
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:           ##调度要求，不影响已执行的Po。 不存在符合两个条件的Node，将无法完成调度
            nodeSelectorTerms:  
              - matchExpressions:
                - key: availability-zone
                  operator: In
                  values:
                  - zone1
                - key: share-type
                  operator: In
                  values:
                  - shared
      containers:
      - image: busybox
        imagePullPolicy: Always
        name: busybox
        command: ["sleep","99999"]
```
>**2.4、优先性节点亲缘性**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: testdp2
  name: testdp2
spec:
  replicas: 5
  selector:
    matchLabels:
      app: testdp2
  template:
    metadata:
      labels:
        app: testdp2
    spec:
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 80                      ##80%的比重给availability-zone in ("zone1")的node,也就是4个Pod
            preference:
              matchExpressions:
              - key: availability-zone
                operator: In
                values:
                - zone1
          - weight: 20
            preference:
              matchExpressions:
              - key: share-type
                operator: In
                values:
                - shared
      containers:
      - image: busybox
        imagePullPolicy: Always
        name: busybox
        command: ["sleep","99999"]
```
>**Pod亲缘性**
适用场景： 希望后端的应用与数据库应用靠的够近，方便读取数据
- 1、强制性Pod亲缘性
```yaml
...
spec:
  affinity:
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - topologyKey: kubernetes.io/hostname        ##主机的标签。hostname最常用，除此之外还有地域、网段等标签，主要看主机配了哪些
        labelSelector:                             ##根据Pod标签选择器找到合适的Pod,获取该Pod所在主机的topologyKey(此处指定了hostname)，然后部署到拥有相同hostname的主机上
          matchLabels:
            os: centos
          matchExpressions:
            - {key: os,operator: In,values: [value1,value2]}
        namespaces: default                   ##默认是当前要部署的Pod所在命名空间下进行匹配，也可以指定其他命名空间去匹配
        ...
```
- 2、优先性Pod亲缘
```yaml
...
spec:
  affinity:
    podAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 80
        podAffinityTerm:
        - topologyKey: kubernetes.io/hostname
          labelSelector:                            
            matchLabels:
              os: centos
            matchExpressions:
            - {key: os,operator: In,values: [value1,value2]}
          namespaces: default
```
>**Pod非亲缘性**
适用场景：希望前端的应用分散开来，可以做到容灾，避免一起宕机
用法与Pod亲缘性一模一样，只是字段有点变化。可以自行`kubectl explain po.spec.affinity.podAntiAffinity`查看
