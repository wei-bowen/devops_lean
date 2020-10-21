#### Statefulset与ReplicaSet区别
- Statefulset控制的Pod挂掉以后，新建的Pod与原来的具有相同的名称、网络标识和状态
- Statefulset创建的Pod每一个都可以拥有一组独立的数据卷(持久化状态)，并且与Pod解耦
- Statefulset创建的Pod都有一个从零开始的顺序索引，而非ReplicaSet那样无序
- Statefulset扩缩容的结果是可预知的，新生的Pod一定是最新的索引，被删除的也是最高的。
- Statefulset创建的Pod在被缩容释放后，起绑定的PVC/PV将会保留。然后跟重新创建的Pod(标号一致)绑定

### 使用StatefulSet
>**创建3个持久化存储**
```shell
mkdir -p /data/nfs_share/pv-{a,b,c}                     ##创建3个目录用于共享
```
定义一个List对象，包含多个资源
```
kind: List
apiVersion: v1
items:
- apiVersion: v1
  kind: PersistentVolume
  metadata:
    name: pv-a
  spec:
    accessModes:                                 ##访问模式，可多选
    - ReadWriteOnce                              ##允许单用户读写模式引用
    capacity:
      storage: 1Gi                               ##大小为1G
    nfs:
      server: 192.168.0.77              
      path: /data/nfs_share/pv-a
    persistentVolumeReclaimPolicy: Recycle       ##声明释放后，空间回收
- apiVersion: v1
  kind: PersistentVolume
  metadata:
    name: pv-b
  spec:
    accessModes:                                 
    - ReadWriteOnce                              
    capacity:
      storage: 1Gi                               
    nfs:
      server: 192.168.0.77              
      path: /data/nfs_share/pv-b
    persistentVolumeReclaimPolicy: Recycle       
- apiVersion: v1
  kind: PersistentVolume
  metadata:
    name: pv-c
  spec:
    accessModes:                                 
    - ReadWriteOnce                              
    capacity:
      storage: 1Gi                               
    nfs:
      server: 192.168.0.77              
      path: /data/nfs_share/pv-c
    persistentVolumeReclaimPolicy: Recycle       
```

>**创建headless service**
- 用于再有状态的Pod之间提供网络标识的headless Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: kubia
spec:
  clusterIP: None
  selector:
    app: kubia
  ports:
  - name: http
    port: 80
```

>**创建StatefulSet**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: kubia
spec:
  serviceName: kubia
  selector:
    matchLabels:
      app: kubia
  replicas: 2
  template:
    metadata:
      labels:
        app: kubia
    spec:
      containers:
      - image: luksa/kubia-pet      ##这个容器会将POST请求收到的的body存储到一个文件中，再Get请求中返回主机名和数据文件的内容
        name: kubia
        ports:
        - name: http
          containerPort: 8080
        volumeMounts:
        - name: data 
          mountPath: /var/data 
  volumeClaimTemplates:             #pvc模板
  - metadata:
      name: data
    spec:
      resources:
        requests:
          storage: 1Gi
      accessModes:
      - ReadWriteOnce
```
>**通过API服务器与Pod通信**
```shell
kubectl proxy &
curl localhost:8001/api/v1/namespaces/default/pods/kubia-0/proxy/
##获取结果
You've hit kubia-0
Data stored on this pod: No data posted yet
##发送POST请求
curl -X POST -d "Hey,I am here ! 20200924 21:57" localhost:8001/api/v1/namespaces/default/pods/kubia-0/proxy/
curl localhost:8001/api/v1/namespaces/default/pods/kubia-0/proxy/                   ##可以获取到##↓
You've hit kubia-0
Data stored on this pod: Hey,I am here ! 20200924 21:57
##删除Pod再观察
kubectl delete po kubia-0           ##观察会发现StatefulSet会重建一个一样的Pod，再次访问得到一样的数据
```

>**创建一个常规Cluster IP Service用于访问**
```yaml
apiVersion: vi
kind: Service
metadata:
   name: kubia-public
spec:
   selector:
     app: kubia
   ports:
   - port: 80
     targetPort: 8080
```
`curl localhost:8001/api/v1/namespaces/default/services/kubia-public/proxy/`会随机分配到任意Pod

### 在StatefulSet中发现伙伴节点
- SRV记录：用来指向提供指定服务的服务器的主机名和端口号
`dig SRV kubia.default.svc.cluster.local` 可以获取到：
```shell
;; ADDITIONAL SECTION:
kubia-0.kubia.default.svc.cluster.local. 30 IN A 10.244.36.80
kubia-1.kubia.default.svc.cluster.local. 30 IN A 10.244.169.147
```

> **更新StatefulSet**
```shell
kubectl edit statefullset kubia      ##可以直接修改replicas
```
