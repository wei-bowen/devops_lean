## 使用控制器对Pod进行调度
**某些场景下，我们期望一定数量的Pod保持运行，以应对某些计划外的变动，例如:**
- 有人手动创建了相同类型的Pod
- 有人删除/更改了现有的Pod
- 节点资源不足等意外原因导致部分Pod崩溃
本章节将介绍三个类型的控制器。
### 基础控制器ReplicaSet
ReplicaSet的工作是确保Pod的数量始终与其标签选择器匹配，如果不匹配则根据需求增减运行的Pod数量。其由以下三部分组成
- 标签选择器。根据标签选择器确定属于其控制域内的Pod。Pod也可以通过调整自身标签来退出/加入replicaset的控制域
- 副本个数。指定运行的Pod数量
- Pod模板。指定新创建的Pod的定义
>**创建一个ReplicaSet**
```yaml
#kubectl create -f kubia-rs.yaml
apiVersion: apps/v1                                               ##通过kubectl explain rs看到的是apps/v1，<<kubernetes in action>>使用的apps/v1beta2也行，暂不细究
kind: ReplicaSet
metadata:
  name: kubia
spec:
  replicas: 3                                                     ##指定保持运行的数量
  selector:                                                       ##标签选择器，如果现在已有符合标签要求的Pod则直接纳入控制域
    matchLabels:
      app: kubia
      ver: stable
  template:                                                       ##指定新创建的Pod模板。name无法指定，会按照控制器名称-随机字符进行扩展，如kubia-nsss24
    metadata:
      labels:                                                     ##定义新生Pod的标签，必须符合标签选择器定义的labels完全一致
        app: kubia
        ver: stable
    spec:
      containers:
      - image: luksa/kubia
        name: kubia
        ports:
        - containerPort: 8080
##标签选择器还可以使用逻辑表达式选择，而不是全部要求=，例如
  selector:
    matchExpressions:
      - key: app
        operator: In                ##还可以是NotIn
        values:
          - kubia
          - nginx
          - ...
       - key: ver
         operator: Exists           ##要求必须包含ver标签(无论其值如何，是否为空),同样支持DoesNotExists
     matchLabels:                   ##可以同时存在表达式选择和完全匹配，两个选择器都匹配上时才生效
       ket: ....
       ....
```
>**调整replicaset参数**
```shell     
kubectl edit rs kubia                   ##可以直接修改replicaset定义，保存后即时生效
kubectl scale rs kubia --replicas=2     ##通过调整replicaset定义的副本数量对pod进行手动伸缩，一会同步写入replicaset的定义
```
>**删除replicaset**
```shell
kubectl delete rs kubia --cascade=false   ##--cascade=false指定仅删除replicaset不删除控制域内的Pod，不指定则同时删除控制域内的Pod
```

### 使用DaemonSet在每一个节点上运行一个Pod
- DaemonSet与ReplicaSet不同，它将在每个节点上运行一个Pod，而不是在随机节点上运行指定数量的Pod
- DaemonSet也可通过标签选择器来控制只在特定的节点上运行一个Pod
>**创建一个DaemonSet**
```yaml
apiVersion: apps/v1                               ##apps/v1beta2也行
kind: DaemonSet
metadata:
  name: ssd-monitor
  labels:
    type: monitor-pod
spec:
  selector:                                       ##标签选择器对要控制的Pod进行筛选
    matchLabels:
      app: ssh-monitor
  template:
    metadata:
      labels:
        app: ssh-monitor                          ##模板中新创建的Pod标签定义一定跟上面选择器的要求一致
    sepc:
      containers:
      - image: luksa/ssd-monitor
        name: main
      nodeSelector:                               ##节点选择器
        os: centos
        disk: ssd
```
>**调整DaemonSet参数**
```shell     
kubectl edit ds ssd-monitor                   ##可以直接修改DaemonSet定义，保存后即时生效
```
>**删除DaemonSet**
```shell
kubectl delete ds kubia --cascade=false   ##--cascade=false指定仅删除DaemonSet不删除控制域内的Pod，不指定则同时删除控制域内的Pod
```
### 安排Job定期定量运行Pod
- 允许你运行一种Pod,该Pod在内部进程成功结束时，不重启容器。一旦任务完成，pod就被认为处于完成状态。
- 节点发生故障时，将按照replicaset的管理方式管理，再重启一个Pod
>**创建一个Job资源**
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-job
spec:
  parallelism: 2                      ##指定可以并行运行的Job数(将同时创建对应数量的pod)，默认不指定则为1
  activeDeadlineSeconds: 60           ##限定Pod运行时间，超过60秒则系统尝试终止Pod并将Job标记为失败，非必须指定项目
  backoffLimit: 8                     ##限定重试次数，默认为6 。超过次数系统尝试终止Pod并将Job标记为失败，非必须指定项目  
  template:
    metadata:
      labels:
        app: batch-job
    spec:
      restartPolicy: OnFailure            ##重启策略：失败时重启。   Job只能选这一个，replicaset/daemonset可选Aways
      containers:
      - image: luksa/batch-job
        name: main
```
>**创建一个定时运行的CronJob资源**
```yaml
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: batch-cronjob
spec:
  schedule: "30 12 * * 1"                 ##每周一十二点半执行,必填项
  jobTemplate:                            ##jobTemplate下的内容与要创建的Job的spec一模一样
    spec:
      parallelism: 2                      
      activeDeadlineSeconds: 60           
      backoffLimit: 8                     
      template:
        metadata:
          labels:
            app: batch-job
        spec:
          restartPolicy: OnFailure            
          containers:
          - image: luksa/batch-job
            name: main
```
