## 应用内访问Pod元数据及其他资源

### 从DownwardAPI传递元数据

 
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
