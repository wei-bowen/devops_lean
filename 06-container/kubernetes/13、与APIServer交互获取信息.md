## 与Kubernetes API服务器交互
某些情况下，我们的应用需要知道其他Pod的信息，甚至是集群中其他资源的信息，就通过与API服务器进行交互来获取。

>**从Pod内部与API服务器进行交互**
- 确定API服务器的位置
- 确保是与真实的API服务器API交互，而非冒充者
- 通过API服务器的认证

### 1、确定API服务器的位置
- 外部地址：`kubectl cluster-info | awk '/master/{print $NF}'`
- 集群内部网络中的IP地址可以通过Pod的环境变量获取，在容器中执行`env | grep KUBERNETES_SERVICE`
- 集群内部直接访问htts://kubernetes即可
### 2、验证服务器身份。
- 可以通过`curl https://kubernetes -k`跳过服务器身份验证，不安全，不建议
- ca证书校验。Pod创建时会默认挂载了一个secret卷，可以通过`kubectl get pod PodName -o yaml`中查看到，挂载在`/var/run/secrets/kubernetes.io/serviceaccount/`下。指定ca文件进行校验即可。`curl --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt https://kubernetes`或者直接指定环境变量`export CURL_CA_BUNDLE=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt`即可`curl https://kubernetes`直接访问
### 3、获得API服务器的访问授权
- 直接访问API服务器是被拒绝的，涉及到权限控制的问题，后续再讲
- 集群外部网络可以通过代理的方式访问，可以通过`kubectl proxy &`启动代理，然后通过`curl http://127.0.0.1:8001`访问,此时是以集群管理员身份访问，拥有所有权限
- Pod内部可以通过指定TOKEN来获取部分权限。`export TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)`然后`curl -H "Authorization: Bearer $TOKEN" https://kubernetes`可以访问该Pod绑定的serviceaccount所拥有的权限。

### 4、与apiserver进行基本交互
`kubectl create clusterrolebinding permissive-bind --clusterrole=cluster-admin --group=system:serviceaccounts`将管理员权限赋给所有系统默认serviceaccount，暂时关闭权限控制。
<br>先了解几个基本概念：
- 在k8s中，Pod、replicaset、service等都被定义为API对象存储在Etcd中。
- API对象在Etcd中的完整路径是由API组/Version(对应Pod定义文件中的apiVersion后内容)/资源类型(对应Kind),可以通过https://apiserver的IP:端口/API组/Version/API资源类型
- 核心的API对象(pod、node、services、configMap)不属于API组，直接在https://apiserver的IP:端口/api/v1下

示例：`curl http://localhost:8001/apis/batch/v1/`可以获得batch组v1版本下所有资源对象(只有jobs)
```json
{
  "kind": "APIResourceList",            ##获得资源清单列表返回
  "apiVersion": "v1",
  "groupVersion": "batch/v1",
  "resources": [                        ##json内包含资源类型说明
    {
      "name": "jobs",
      "singularName": "",
      "namespaced": true,
      "kind": "Job",
      "verbs": [                        ##资源可以接受的动作请求
        "create",   
        "delete",
        "deletecollection",
        "get",
        "list",
        "patch",
        "update",
        "watch"
      ],
      "categories": [
        "all"
      ],
      "storageVersionHash": "mudhfqk/qZY="
    },
    {
      "name": "jobs/status",       ##资源有一个专门的REST endpoint来修改其状态
      "singularName": "",
      "namespaced": true,
      "kind": "Job",
      "verbs": [
        "get",
        "patch",
        "update"
      ]
    }
  ]
}
```
- `curl -s http://127.0.0.1:8001/apis/batch/v1/jobs`获取集群内所有jobs
```json
{
  "kind": "JobList",
  "apiVersion": "batch/v1",
  "metadata": {
    "selfLink": "/apis/batch/v1/jobs",
    "resourceVersion": "3310352"
  },
  "items": [                                                              ##集群中所有相关资源列表，如果没有jos，items里面为空
    {
      "metadata": {
        "name": "batch-job",
        "namespace": "default",
        "selfLink": "/apis/batch/v1/namespaces/default/jobs/batch-job",
        "uid": "0005e867-cf06-4faa-b1f9-5b065ade03c3",
        "resourceVersion": "3309807",
        "creationTimestamp": "2020-11-01T14:08:55Z",
        "labels": {
          "app": "batch-job",
          "controller-uid": "0005e867-cf06-4faa-b1f9-5b065ade03c3",
          "job-name": "batch-job"
        },
        ....
```
- 获取指定namespace下所有jobs`curl -s http://127.0.0.1:8001/apis/batch/v1/namespaces/default/jobs`
- 获取指定的job`curl -s http://127.0.0.1:8001/apis/batch/v1/namespaces/default/jobs/batch-job`,获取结果与`kubectl gep job batch-job -n default -o json`一致。
### 5、通过ambassador容器简化与API服务器的交互
- 原理就是在Pod内起一个kubectl proxy代理，以http方式访问代理，然后代理读取Pod内挂载的secret卷完成认证工作以https方式去访问APIServer
创建一个centos容器，带上ambassador容器
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: centos
spec:
  replicas: 1
  selector:
    matchLabels:
      os: centos
  template:
    metadata:
      name: main
      labels:
        os: centos
    spec:
      hostname: centos
      containers:
      - name: main
        image: centos
        stdin: true
        tty: true
      - name: ambassador
        image: luksa/kubectl-proxy:1.6.2
```
此时再执行`kubectl exec -it centos-ff9f84f85-6bl8p -c main -- bash `进入容器bash界面然后`curl http://127.0.0.1:8001`即可在容器内访问apiserver<br>

