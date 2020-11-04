## kubernet API服务器的安全防护
- 访问kubernetes集群的资源需要过三关：认证(Authentication)、鉴权(Authorization)、准入控制
- 普通用户访问API Server需要证书、token或者用户名加密码；Pod访问则需要ServiceAccount

### 客户端身份证认证
- HTTPS证书认证：基于CA证书签名的数字证书认证
- HTTP Token:通过Token来识别用户
- HTTP Base认证: 用户名+密码的方式

#### 示例：为wbw用户授权default命名空间Pod的读写权限
- **1、签发CA证书**
- **2、生成kubeconfig授权文件**
- **3、创建RBAC权限策略**

### 基于RBAC认证机制
Role-Based Access Control 基于角色的权限管理。
- 将资源的相关权限赋给角色/集群角色
- 为Pod创建ServiceAccount
- ServiceAccount通过与角色/集群角色来获取相关资源的权限
- Pod通过挂载ServiceAccount的sevret卷来获得apiversion的权限授权

例如： 创建一个数据库管理员DBA角色，集群内数据库相关的Pod的权限授给DBA，其他Pod的ServiceAccount只要绑定了DBA角色即拥有所有数据库相关Pod的权限。ServiceAccount可以绑定多个角色,多个Pod可以使用同一个ServiceAccount


### 使用角色及角色绑定
- **1、打开权限控制**
之前曾将集群管理员角色绑定给了系统默认ServiceAccount,现在需要删掉绑定`kubectl delete clusterrolebindings.rbac.authorization.k8s.io permissive-bind`,否则所有Pod默认都又集群管理员权限，无法验证我们后续的操作。<>
此时再`kubectl exec -it centos -c main -- bash`进入centos应用内执行`curl http://127.0.0.1:8001/apis/app/v1/namespaces/default/deployments`尝试获取命名空间下所有deployments将会返回forbidden
- 1、创建角色
`kubectl create role deployment-admin --verb=get --verb=list --resource=deployments -n default --dry-run=client -o yaml`
```
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default                  ##role只允许获取指定命名空间内的资源的权限，不能跨命名空间。但是ROLE可以绑定给不同空间的账号
  name: deployment-admin
rules:
  - apiGroups: ["apps"]               ##deployment所属组是apps. pod/node/service等核心资源不属于任何API组，会填空[""]
    resources: ["deployments"]        ##资源组名称，复数. 
                                      ##还可以添加一个resourceNames列表指定到具体的资源名称
    verbs: ["get","list"]             ##允许的动作。可以通过curl -s http://127.0.0.1:8001/apis/apps/v1 | jq .resources | jq .[3].verbs查看可选哪些动作
```
- 2、将角色绑定到Pod当前使用的默认ServiceAccount即default上
`kubectl create rolebinding dp-admin-default --role=deployment-admin --serviceaccount=default:default -n default --dry-run -o yaml`(两个default是指default空间下:的default帐号)
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  creationTimestamp: null
  name: dp-admin-default
  namespace: default
roleRef:                                      ##一次绑定只能绑定一个角色
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: deployment-admin
subjects:                                     ##但是可以一次性将一个角色赋给多个帐号主体
- kind: ServiceAccount
  name: default
  namespace: default
```
- 3、此时在绑定了default帐号的Pod内再执行`curl http://127.0.0.1:8001/apis/apps/v1/namespaces/default/deployments`可以访问到集群下所有deployments
### 使用集群角色及集群角色绑定
集群级别的资源如node、Persistentvolume、Namespace等，需要使用集群角色进行授权,例如<br>
`kubectl create clusterrole pv-reader --verb=get,list --resource=persistentvolumes --dry-run=client -o yaml`
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: pv-reader                             ##与role用法几乎一样，少了namespace指定
rules:
- apiGroups:                                  
  - ""
  resources:
  - persistentvolumes
  verbs:
  - get
  - list
```
clusterrolebinding绑定用法与rolebinding并无区别，只是少了namespace指定
### 默认角色及其绑定
