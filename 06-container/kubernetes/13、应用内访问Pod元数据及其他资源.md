## 应用内访问Pod元数据及其他资源

### 从DownwardAPI传递元数据**
当Pod中运行的程序需要知道Pod的IP地址等(在Pod被创建之前无法被预置的信息)时,可以通过Downward API给这些进程暴露Pod的元数据。可以暴露的信息包括：
- **Pod的名称**：metadata.name
- **Pod的IP地址**：status.podIP
- **Pod所在的命名空间**：metadata.namespace
- **Pod运行节点的名称**：spec.nodeName
- **Pod运行所归属的服务账户的名称**：spec.serviceAccount
- **每个容器请求的CPU和内存的使用量**：reources.request
- **每个容器可以使用的CPU和内存的限制**：limits.memory
- **Pod的标签**
- **Pod的注解**
以上信息都可以在创建Pod后通过`kubectl get pod PodName -o yaml`获取
>**1、创建一个简单的单容器,通过环境变量暴露元数据**
具体用法可以参照`kubectl explain pod.spec.containers.env.valueFrom`.其中属性数据使用的是`pod.spec.containers.env.valueFrom.fieldRef`，资源则是`kubectl explain pod.spec.containers.env.valueFrom.resourceFieldRef`
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: downward
spec:
  containers:
  - name: main
    image: busybox                          ##如果是虚拟机跑k8s,处理器的虚拟化Intel..选项要勾选
    command: ["sleep","99999999"]
    resources:
      requests:
        cpu: 15m
        memory: 100Ki
      limits:
        cpu: 100m
        memory: 4Mi
    env:
    - name: POD_NAME
      valueFrom:
        fieldRef:
          fieldPath: metadata.name
    - name: POD_NAMESPACE
      valueFrom:
        fieldRef:
          fieldPath: metadata.namespace
    - name: POD_ID
      valueFrom:
        fieldRef:
          fieldPath: status.podIP
    - name: NODE_NAME
      valueFrom:
        fieldRef:
          fieldPath: spec.nodeName
    - name: SERVICE_ACCOUNT
      valueFrom:
        fieldRef:
          fieldPath: spec.serviceAccountName
    - name: CONTAINER_CPU_REQUEST_MILLICORES
      valueFrom:
        resourceFieldRef:
          resource: requests.cpu
          divisor: 1m
    - name: CONTAINER_MEMORY_REQUEST_KIBIBYTES
      valueFrom:
        resourceFieldRef:
          resource: limits.memory
          divisor: 1Ki
```
执行`kubectl exec downward -- env` 即可看到环境变量已正确获取Pod的元数据
```
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
HOSTNAME=downward
CONTAINER_CPU_REQUEST_MILLICORES=15
CONTAINER_MEMORY_REQUEST_KIBIBYTES=4096
POD_NAME=downward
POD_NAMESPACE=default
.....
HOME=/root
```
>**2、通过downwardAPI卷来传递元数据**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: downward-volume
  labels:                       ##相比上一个yaml多了标签和注释，后面将暴露这些信息
    foo: bar
  annotations:
    key1: value1
    key2: |
      multi
      line
      value
spec:
  containers:
  - name: main
    image: busybox
    command: ["sleep","99999999"]
    resources:
      requests:
        cpu: 15m
        memory: 100Ki
      limits:
        cpu: 100m
        memory: 4Mi
    volumeMounts:
    - name: downward
      mountPath: /etc/downward
  volumes:
  - name: downward
    downwardAPI:
      items:
      - path: "POD_NAME"
        fieldRef:
          fieldPath: metadata.name
      - path: "POD_NAMESPACE"
        fieldRef:
          fieldPath: metadata.namespace
      - path: "labels"
        fieldRef:
          fieldPath: metadata.labels
      - path: "annotations"
        fieldRef:
          fieldPath: metadata.annotations
      - path: "CONTAINER_CPU_REQUEST_MILLICORES"
        resourceFieldRef:
          containerName: main
          resource: requests.cpu
          divisor: 1m
      - path: "CONTAINER_MEMORY_REQUEST_KIBIBYTES"
        resourceFieldRef:
          containerName: main
          resource: limits.memory
          divisor: 1
 ```
 执行命令查看
 ```shell
[root@k8s-master ~]# kubectl exec downward-volume -- ls -lL /etc/downward
total 24
-rw-r--r--    1 root     root             2 Sep 23 15:03 CONTAINER_CPU_REQUEST_MILLICORES
-rw-r--r--    1 root     root             7 Sep 23 15:03 CONTAINER_MEMORY_REQUEST_KIBIBYTES
-rw-r--r--    1 root     root            15 Sep 23 15:03 POD_NAME
-rw-r--r--    1 root     root             7 Sep 23 15:03 POD_NAMESPACE
-rw-r--r--    1 root     root          1467 Sep 23 15:03 annotations
-rw-r--r--    1 root     root             9 Sep 23 15:03 labels
 ```
 **此时我们可以执行`kubectl edit pod downward` 和 `kubectl edit pod downward-volume` 分别对它们的注释annotions进行改动 <br>
 然后再执行`kubectl exec downward --env`和`kubectl exec downward-volume -- cat /etc/downward/annotations` 查看标签。
 发现卷挂载的发生更新，环境变量暴露的没有更新。**
 
 ## 与Kubernetes API服务器交互
 - downwardAPI可以将Pod和容器的*自身部分*元数据传递给它们内部运行的进程
 - 需要暴露自身更多的元数据或者其他资源的元数据，就必须直接与K8s API服务直接进行交互来获取
 
 >**探究Kubernetes REST API**
- `kubectl cluster-info` 可以获取API服务的URL，例如`Kubernetes master is running at https://192.168.0.77:6443`
- `curl https://192.168.0.77:6443 -k` -k是跳过服务器证书检查环节，可以获得少量信息。不加将无法获得任何信息。因为服务器使用了HTTPS细以且需要授权，不能随意交互
- 可以创建代理服务来接受本机的HTTP连接，并处理身份认证，让我们在本机可以与真实的API服务器进行交互
```shell
[root@k8s-master ~]# kubectl proxy &
[1] 39105
[root@k8s-master ~]# Starting to serve on 127.0.0.1:8001                  ##启动了一个代理服务，监听端口是8001
[root@k8s-master ~]# curl http://127.0.0.1:8001                           ##访问代理服务，返回很多信息
{
  "paths": [
    "/api",
    "/api/v1",
    "/apis",
    "/apis/",
    "/apis/admissionregistration.k8s.io",
    "/apis/admissionregistration.k8s.io/v1",
    "/apis/admissionregistration.k8s.io/v1beta1",
....
```
- 调用第一个API：`curl 127.0.0.1:8001/apis/batch`，获得响应：
```json
{
  "kind": "APIGroup",
  "apiVersion": "v1",
  "name": "batch",
  "versions": [                                         ##返回全部可用版本
    {
      "groupVersion": "batch/v1",
      "version": "v1"
    },
    {
      "groupVersion": "batch/v1beta1",
      "version": "v1beta1"
    }
  ],
  "preferredVersion": {                                 ##建议用户使用的版本
    "groupVersion": "batch/v1",
    "version": "v1"
  }
}
```
- `curl 127.0.0.1:8001/apis/batch/v1` 列举betch/v1下的可用资源类型。job
```json
{
  "kind": "APIResourceList",
  "apiVersion": "v1",
  "groupVersion": "batch/v1",
  "resources": [
    {
      "name": "jobs",
      "singularName": "",
      "namespaced": true,
      "kind": "Job",
      "verbs": [                  ##资源对应可用的动词
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
      "name": "jobs/status",        ##资源有一个专门的应答接口来修改起状态
      "singularName": "",
      "namespaced": true,
      "kind": "Job",
      "verbs": [                   ##状态可以被恢复、打补丁、修改
        "get",
        "patch",
        "update"
      ]
    }
  ]
}
```
- `curl 127.0.0.1:8001/apis/batch/v1/jobs` 可以获取集群中的所有JOB的清单
- `curl 127.0.0.1:8001/apis/batch/v1/namespace/命名空间名称/jobs/job名称` 可以过去到该Job所有详细信息，结果等同于`kubectl get job job名称 -n 命名空间名称 -o json`

>**从Pod内部与API服务器进行交互**
- 确定API服务器的位置
- 确保是与真实的API服务器API交互，而非冒充者
- 通过API服务器的认证

**1、先建一个curl容器**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: curl
spec:
  containers:
  - image: tutum/curl
    command: [sleep,99999999]
    name: main
```
**2、连接API服务器
```shell
kubectl exec -it curl -- bash                                                 ##进入容器
env | grep SERVICEk                                                           ##可以通过环境变量获取API服务相关信息
curl https://kubernetes -k                                                    ##默认DNS就可以直接解析API服务器。但是此时跟上面提到的一样，我们要确认这事一个真实的API服务器，-k不安全
export CURL_CA_BUNDLE=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt    ##定义CA环境变量，通过CA证书认证，这个证书前面secret章节提到过挂载在这里的
curl https://kubernetes                                                       ##此时再访问即是安全的
```
**3、获得API服务器授权
```shell
export TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)       ##调用TOKEN访问
curl -H "Authorization: Bearer $TOKEN" https://kubernetes                     此时访问可获得认证
```
**4、实操：获取当前命名空间下所有Pod**
```shell
NS=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)                     ##这个文件可以获取所在namespace
curl -H "Authorization: Bearer $TOKEN" https://kubernetes/api/v1/namespaces/$NS/pods  ##涉及到身份认证，后面章节才讲。此时访问会提示权限不足
exit
kubectl create clusterrolebinding permissive-binding --clusterrole=cluster-admin --group=system:serviceaccounts ##回到master节点授予所有帐号管理员权限杰克正常访问
```
