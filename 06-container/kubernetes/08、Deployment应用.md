## Deployment应用
- Deployment用于部署应用程序并以声明的方式升级应用
- Deployment通过调度replicaset去调度Pod
- Deployment升级时先起新的Pod再停老的Pod，避免服务受影响

>**创建第一个Deployment**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: kubia
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
      - image: luksa/kubia:v1
        name: nodejs
```
>**升级Deployment**
```shell
kubectl patch deployment kubia -p '{"spec":{"minReadySeconds":10}}'       ##减慢升级速度，便于观察
while true;do kubectl exec curl -- curl -s http://10.108.169.171;done     ##打开另一个窗口，持续观察
kubectl rollout status deployment kubia                                   ##也可观察deployment的升级进度，可以及时阻止失败的升级
kubectl set image deployment/kubia nodejs=luksa/kubia:v2                  ##开始升级
kubectl get rs                                                            ##可以看到两个ReplicaSet，升级实际上是调都一个新的RS，旧的逐渐被抛弃

deployment.spec.strategy.rollingUpdate.maxSurge                           ##默认25%，意思是升级过程中Pod数量最多超过预定的25%，可以指定具体数字如2，升级3个Pod应用时最多同事存在5个Pod
deployment.spec.strategy.rollingUpdate.maxUnavailable                     ##最多允许多少个Pod处于不可用状态。默认25%。四舍五入，升级四个Pod应用时最多允许1个Pod不可用，也可以指定数字
kubectl rollout pause deployment/kubia                                    ##暂停升级。已经生好的不会回滚
kubectl rollout resume deployment/kubia                                   ##恢复升级
```
>**回滚deployment版本**
```shell
kubectl rollout history deployment/kubia                                  ##查看版本历史
kubectl rollout undo deployment kubia --to-revision=1                     ##回滚到指定版本号1，如果--to-revision就会回滚到最近一个版本
deployment.spec.revisionHistoryLimit                                      ##deployment的这个属性是限定版本历史记录的数量，默认10，可以手动调整
```

>**防止失败的升级**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: kubia
  name: kubia
spec:
  replicas: 3
  progressDeadlineSeconds: 60                                             ##设定升级失败时间为60秒，默认时600秒，超时就自动回滚
  minReadySeconds: 10                                                     ##延缓升级速度
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1                                                         ##每次只升级一个
      maxUnavailable: 0                                                   ##不允许有不可用的Pod，及升级失败时就停止继续升级
  selector:
    matchLabels:
      app: kubia
  template:
    metadata:
      labels:
        app: kubia
    spec:
      containers:
      - image: luksa/kubia:v1
        name: nodejs
        readinessProbe:
          periodSeconds: 1                                                ##定义一个就绪探针，一秒钟执行一次,curl 127.0.0.0:8080
          httpGet:
            path: /
            port: 8080
```

>**Deployment弹性伸缩**
```shell
kubectl scale deployment kubia --replicas=2                               ##指定Pod数量
kubectl autoscale deployment/kubia --min=2 --max=10 --cpu-percent=80      ##自动伸缩
```
