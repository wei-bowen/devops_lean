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
### 3、设置Node污点和Pod容忍度来阻止Pod调度到特定节点
>**设置节点污点**
- 以master节点为例，执行`kubectl describe nodes k8s-master | grep Taints`可以看到污点Taints
```
Taints:             node-role.kubernetes.io/master:NoSchedule     ##污点的格式是`key=<value>:<effect>` 污点名称=<污点值>:<污点影响度>，这事是缺省了value的污点
```
**影响度effect**<br>
- NoSchedule:不容忍则不能调度在此节点<br>
- PreferNoSchedule:尽量阻止调度这个节点上，如果没有其他节点可以调度的话依然可以调度到这里<br>
- NoExecute:不仅禁止不容忍的Pod调度到此节点，已经调度的但是没容忍的也会被驱逐。<br>

- 随便找一个在master节点上的pod,执行`kubectl describe pod kube-proxy-9nhv4 -n kube-system`可以看到容忍度Tolerations
```
Tolerations:     
                 CriticalAddonsOnly
                 node.kubernetes.io/disk-pressure:NoSchedule
                 node.kubernetes.io/memory-pressure:NoSchedule
                 node.kubernetes.io/network-unavailable:NoSchedule
                 node.kubernetes.io/not-ready:NoExecute
                 node.kubernetes.io/pid-pressure:NoSchedule
                 node.kubernetes.io/unreachable:NoExecute
                 node.kubernetes.io/unschedulable:NoSchedule
```
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
      - effect: NoExecute
        key: node.alpha.kubernetes.io/notReady          ##当所在节点处于notReady状态
        operator: Exists
        tokerationSeconds: 300                          ##持续300时，Pod被重新调度
      - effect: NoExecute
        key: node.alpha.kubernetes.io/unreachable       
        operator: Exists                                ##当污点无value时，可以用Exists匹配污点
        tokerationSeconds: 300
```
>**删除污点**

`kubectl taint node k8s-node1 node-type-`

### 4、使用节点亲缘性将Pod调度到特定节点上
**每个Pod可以自定义自己的节点亲缘性规则，指定硬性限制或者偏好。如果指定偏好，Pod将被优先调度到偏好节点上，无法实现时才调度到其他节点**
**给节点分别打两个标签，便于后续验证效果**
```
kubectl get nodes -L share-type -L availability-zone
NAME         STATUS   ROLES    AGE   VERSION   SHARE-TYPE   AVAILABILITY-ZONE
k8s-master   Ready    master   24h   v1.18.0                
k8s-node1    Ready    <none>   24h   v1.18.0   dedicated    zone1
k8s-node2    Ready    <none>   24h   v1.18.0   shared       zone2
```
>**强制性节点亲缘性规则**
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
>**优先性节点亲缘性**
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

>**Pod非亲缘性**
### 5、
