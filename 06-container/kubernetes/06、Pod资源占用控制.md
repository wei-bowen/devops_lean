## Pod资源使用控制
### 为Pod申请资源
`kubectl describe node k8-node1`可以查看到节点的资源总量Capacity、剩余可申请量Allocatable、已被申请的资源量Allocated resources等信息<br>
Pod资源的请求量和使用限制是在容器层面进行控制的。pod.spec.containers.resources
```
apiVersion: v1
kind: Pod
metadata:
  name: podName
spec:
  containers:
  - image: imageName
    ...
    resources:
      requests:                 ##指定Pod资源需求的最小值，调度器在决定将Pod调度到哪个节点时将会考虑节点剩余可用资源(节点上的总资源减去所有Pod申请的资源，而非实际剩余已用资源)
        cpu: 200m               ##1/5核，1000m是1核
        memory: 10Mi            ##10MB内存
      limits:                   ##指定Pod资源使用的最大值。如果指定了limits但是不指定request，request将被默认设置为和limits一样
        cpu: 1                  ##最多允许使用1核
        memory: 50Mi            ##
      ...
```
- 调度的时候,kube-sheduler会按照requests的值进行计算。但是真正设置Cgroups限制的时候，kubelet会按照limits值进行设置
- 当多个pod都占用了超过其requests申请资源，导致节点资源不足时，节点将按其requests申请量按比例分配。
- 节点cpu不足时Pod会“饥饿”，但是内存不足时将会被OEM杀掉
PS:容器内指定top命令，看到的时容器被分配到的资源，并非节点的资源
### Pod的QoS机制
当节点资源超过节点上所有Pod的使用量，出现资源不足时，k8s将按照QoS等级重新分配，优先分配给最高优先级，优先杀掉最低优先级。如果QoS等级相同时杀掉超用比例最高的<br>
`kubectl describe pod podName`可以查看status.qosClass字段
- BestEffort(最低优先级)：没有设置requests和limit字段的Pod
- Burstable
- Guaranteed(最高优先级)：每个容器都配置了相同的limits和requests的Pod。此级别的Pod会通过cpuset的方式绑定到某个cpu的核上，不再共享其他cpu的算力，减少cpu进行上下文切换的次数，性能得到提升
### 配置命名空间内Pod的默认资源限制
通过LimitRange资源进行限定
```yaml
apiVersion: v1
kind: LinitRange
metadata:
  name: example
  namespace: default                      ##指定适用在哪个命名空间下
spec:
  limits:
  - type: Pod
    min:                                  ##指定整个Pod资源请求量之和最小值
      cpu: 50m
      memoory: 5Mi
    max:                                  ##指定整个Pod资源请求量之和最大值
      cpu: 1
      memory: 1Gi
  - type: Container
    defaultRequest:                       ##容器没有指定request时的默认值
      cpu: 100m
      memory: 10Mi
    default:                              ##容器没有指定limit时的默认值
      cpu: 200m
      memory: 100Mi
    min:                                  ##容器request和limit的最大值最小值
      ...
    max:
      ...
    maxLimitRequestRatio:                 ##limit/request的最大比值
      cpu: 4
      memory: 10
  - type: PersistentVolumeClaim           ##指定申请的存储最大最小值
    min:
      storage: 1Gi
    max:
      storage: 10Gi 
```
### 限定命名空间的可用资源总数
- ResourceQuota插件会检查要创建的Pod是否会引起总资源量意出，如果是，部署请求将会被拒绝。ResourceQuota仅影响即将要部署的Pod，不影响已经部署的Pod
- 创建ResourceQuota必须现有LimitRange，否则没有默认指定的资源需求，pod创建时如果不指定需求，将会被拒绝
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: resouce-limit
  namespace: default
spec:
  hard:                                 ##定义了命名空间下所有pod可申请/使用的资源总量
    requests.cpu: 400m
    requests.cpu: 200Mi
    limits.cpu: 600m
    limits.memory: 500mi
    requests.storage: 500Gi             ##可生命的存储总量
    ssd.storageclass.storage.k8s.io/requests.storage: 300Gi         ##以ssd命名的StorageClass的可申请的存储量
    ssd.storageclass.storage.k8s.io/persistentvolumeclaims: 2       ##可申请的pvc数量
    standard.storageclass.storage.k8s.io/requests.storage: 300Gi
    pod: 10
    replicationcontrollers: 5
    configmap: 5
    persistentvolumeclaims: 3
    services: 5
    services.loadbalancers: 3
    services.nodeport: 2
    ...
  scopes:              ##指定作用范围
  - BestEffort  
  - Burstable
  scopeSelector：      ##就3个QoS等级，没必要用选择器了
```
`kubectl descrbe quota`可以查看配额使用情况
### 监控Pod的资源使用量
- 节点组件kubelet内置了一个名为cAdvisior的agent,跟随kubelet一起启动，可以搜集节点上所有Pod的资源使用情况。可以通过安装
- Metrics Server是一个集群范围的资源使用情况数据聚合器。作为一个应用部署在集群中，从每个节点的kubelet的Summary API收集指标(其中包含了cAdvisior和kubelet本身汇总的信息)。Metrics Server通过聚合器注册在Master APIServer中。



