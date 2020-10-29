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
当多个pod都占用了超过其requests申请资源，导致节点资源不足时，节点将按其requests申请量按比例分配。<br>
PS:容器内指定top命令，看到的时容器被分配到的资源，并非节点的资源
### Pod的QoS机制
当节点资源超过节点上所有Pod的使用量，出现资源不足时，k8s将按照QoS等级重新分配，优先分配给最高优先级，优先杀掉最低优先级。如果QoS等级相同时杀掉超用比例最高的<br>
`kubectl describe pod podName`可以查看status.qosClass字段
- BestEffort(最低优先级)：没有设置requests和limit字段的Pod
- Burstable
- Guaranteed(最高优先级)：每个容器都配置了相同的limits和requests的Pod
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
