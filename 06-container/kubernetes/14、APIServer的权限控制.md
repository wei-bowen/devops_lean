## kubernet API服务器的安全防护
- Pod内访问：资源权限赋给role/clusterrole，然后通过rolebind/clusterrolebind绑定到serviceaccount，然后Pod创建时通过关联serviceaccount获得权限
- 集群外账户访问。

### Pod内访问
#### 基于RBAC认证机制
Role-Based Access Control 基于角色的权限管理。
- 将资源的相关权限赋给角色/集群角色
- 为Pod创建ServiceAccount
- ServiceAccount通过与角色/集群角色来获取相关资源的权限
- Pod通过挂载ServiceAccount的sevret卷来获得apiversion的权限授权

例如： 创建一个数据库管理员DBA角色，集群内数据库相关的Pod的权限授给DBA，其他Pod的ServiceAccount只要绑定了DBA角色即拥有所有数据库相关Pod的权限。ServiceAccount可以绑定多个角色,多个Pod可以使用同一个ServiceAccount


#### 使用角色及角色绑定
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
#### 使用集群角色及集群角色绑定
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
#### 默认角色及其绑定
### 集群外用户访问
kubectl 命令行工具通过 kubeconfig 文件的配置来选择集群以及集群API Server通信的所有信息。kubeconfig 文件用来保存关于集群用户、命名空间和身份验证机制的信息。默认情况下 kubectl 读取 $HOME/.kube/config 文件，也可以通过设置环境变量 KUBECONFIG 或者 --kubeconfig 指定其他的配置文件。

### 管理员配置role/clusterrole并通过rolebind/clusterrolebind绑定到用户上
- 用户不必创建，只要指定名字即可

#### 1、生成客户端身份认证文件
三种客户端身份认证
- K8S CA签发的证书
- Token
- 用户名+密码
>K8S CA签发
```shell
mkdir -p /usr/local/kubernetes/bin && cd /usr/local/kubernetes/bin
wget -O cfssl https://pkg.cfssl.org/R1.2/cfssl_linux-amd64
wget -O cfssljson https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64
wget -O cfssl-certinfo https://pkg.cfssl.org/R1.2/cfssl-certinfo_linux-amd64
chmod +x ./*
echo "export PATH=$PATH:/usr/local/kubernetes/bin/">>/etc/profile
source /etc/profile
mkdir -p /etc/kubernetes/pki/ssl && cd /etc/kubernetes/pki/ssl
###⬇创建CA配置文件
cat > ca-config.json << EOF
{
    "signing": {
        "default": {
            "expiry": "87600h"
        },
        "profiles": {
            "kubernetes": {
                "expiry": "8760h",
                "usages": [
                    "signing",                  ##表示该证书可用于签名其他证书
                    "key encipherment",         
                    "server auth",              ##表示该CA对server提供的证书进行验证
                    "client auth",              ##表示该CA对client提供的证书进行验证
                ] 
            }
        }
    }
}
EOF
###⬇创建CA签名文件
cat > node1-adm-csr.json << EOF
{
    "CN": "node1-adm",                          ##用户名
    "hosts": [],
    "key": {
        "algo": "rsa",
        "size": 2048
    },
    "names": [
        {
            "C": "US",
            "L": "HZ",
            "ST": "Hangzhou"
            "O": "node-adm"                     ##用户组
            "OU": "System"
        }
    ]
}
EOF
```
#### 2、配置权限
#### 3、生成kubeconfig文件
```shell
kubectl config set-cluster kubernetes \
--certificate-authority=/etc/kubernetes/pki/ca.crt \          ##指定ca文件
--embed-certs=true \                                          ##ture是直接把ca.crt内容写入配置文件，不选ture则只指定crt文件位置
--server=https://192.168.0.77:6443 \                          ##集群apiserver地址端口
--kubeconfig=wbw.kubeconfig                                   ##指定将配置输出到哪个文件
```
上面只是示例，完整的配置文件示例：
```yaml
apiVersion: v1
clusters:
- cluster:
    certificate-authority: /etc/kubernetes/pki/ca.crt
    server: https://192.168.0.77:6443
  name: k8s-clusterName
contexts:
- context:
    cluster: k8s-clusterName
    user: userName
    namespace: default
  name: k8s-clusterName
current-context: k8s-clusterName
kind: Config
preferences: {}
users:
- name: userName
  user:
    client-certificate: /etc/kubernetes/pki/apiserver.crt
    client-key: /etc/kubernetes/pki/apiserver.key
```

