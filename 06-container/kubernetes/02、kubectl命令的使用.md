>**安装命令快速补全**
```shell
yum install -y bashcompletion
source <(kubectl completion bash)
```
>**展示集群信息**
```shell
kubectl cluster-info
kubectl get cs                ##compose status
```



>**获取帮助**
```shell
kubectl --help                        ##查看kubectl所有可用选项
kubectl get --help                    ##查看kubectl get可用选项
kubectl explain pod                   ##查看资源元数据的数据项，后面写yaml文件会用到
```

>**查看资源状态**

kubectl get 资源类型 名称
```shell
kubectl get nodes                     ##get查看资源状态，有node、pod、replication、deployment、service、ingress、
kubectl get pods -o wide              ## -o wide 显示更详细信息，如所在节点位置、标签等
kubectl get service -o wide -w        ## -w 动态刷新状态
kubectl get ingress -o wide -o yaml   ## -o yaml 将资源状态已yaml格式输出到终端，还支持json格式
kubectl get pods -n default           ## -n指定命名空间，查看该namespace下所有pod资源
kubect
....
```
>**获取资源详细信息**

kubectl get 资源类型 名称
`kubectl describe node k8s-node1`

>**创建资源**
```shell
#部署第一个kubernetes应用
kubectl run kubia --image=luksa/kubia --port=8080 --generator=run/v1 --dry-run=client -o yaml

-  kubectl run 后接pod名称，运行一个pod
-  --iamge=   指定要运行的容器
-  --port=    指定容器监听的端口
-  --dry-run=client     不实际运行，只是测试语句是否能成功运行。
-  -o yaml              可以将会运行的pod元数据以yaml格式打印出来。可以重定向到文件，后续用kubectl apply -f 文件名  来执行
```
通过资源定义yaml文件创建
```shell
kubectl create -f resource.yaml
kubectl apply -f resource.yaml
```
>**删除资源**
```shell
kubectl delete 资源类型  名称
kubectl delete -f 资源定义yaml文件
```
