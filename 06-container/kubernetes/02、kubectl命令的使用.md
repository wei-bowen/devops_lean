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

kubectl get 资源类型 <名称> <可选项>
- -o wide             ##o=output  输出详细信息
- -n kube-system      ##指定查看某个namespce下的资源，默认时default命名空间
- -A                  ##查看所有namespace下资源
- -o yaml             ##yaml格式输出
- -l app=kubia        ##按标签筛选，只看带有标签app且值为kubia的资源。值可以缺省，只过滤带有某个标签的资源
- -L app              ##输出结果中加一个标签列，列名是标签名字，列的值是标签的值
- -c imagename        ##指定查看Pod中的某个容器
- --previous          ##查看pod的历史信息。Pod有可能被重新调度过，不加此选项只能看到最后一次调度的信息
- --show-labels       ##打印资源的标签信息
>**获取资源详细信息**

kubectl describe 资源类型 名称 <br>
`kubectl describe node k8s-node1`

kubectl logs Pod名称  查看Pod日志<br>
`kubectl logs nginx`


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
>**为资源添加标签**

kubectl label 资源类型 名称 标签=值，例如`kubectl lable node k8s-node1 env=dev`

>**删除资源**
```shell
kubectl delete 资源类型  名称
kubectl delete -f 资源定义yaml文件
```
