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
- kind: ServiceAccount                        ##kind可以是ServiceAccount/User/Group 后面是真实的账号用户组
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
场景实战：加入我想给名字叫t-bag的用户授权访问集群192.168.0.77:6443中的kube-system命名空间的访问权限。需要完成以下步骤
- 1、创建role授予kube-system的访问权限，然后将该role通过rolebinding绑定给用户t-bag
- 2、签发集群的CA证书(用于验证是否访问到了正确的集群)、t-bag的认证证书t-bag.crt及其私钥t-bag.key(用于集群确认t-bag的身份)，三个文件给到t-bag
- 3、t-bag使用配置好kubeconfig文件(文件中包含访问集群所需的所有信息)，然后使用kubectl命令行工具读取kubeconfig来访问集群
#### 1、赋权
就是上面讲到的RBAC授权。
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: kube-system
  name: pod-reader
rules:
- apiGroups: [""] 
  resources: ["pods"]
  verbs: ["get", "watch", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: kube-system
subjects:
- kind: User
  name: t-bag
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```
#### 2、签发证书
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
                    "signing",                  //表示该证书可用于签名其他证书
                    "key encipherment",         
                    "server auth",              //表示该CA对server提供的证书进行验证
                    "client auth"              //表示该CA对client提供的证书进行验证
                ] 
            }
        }
    }
}
EOF
###⬇创建CA签名文件
cat > node1-adm-csr.json << EOF
{
    "CN": "t-bag",                          //用户名
    "hosts": [],
    "key": {
        "algo": "rsa",
        "size": 2048
    },
    "names": [
        {
            "C": "US",
            "L": "HZ",
            "ST": "Hangzhou",
            "O": "node-adm",                     //用户组
            "OU": "System"
        }
    ]
}
EOF
cfssl gencert -ca=/etc/kubernetes/pki/ca.crt -ca-key=/etc/kubernetes/pki/ca.key --config=ca-config.json  t-bag-csr.json | cfssljson -bare t-bag
```
**这一步比较操蛋，没研究成功，我们就假设成功生成了验证文件**
#### 3、配置kubeconfig文件
- kubectl 命令行工具通过 kubeconfig 文件的配置来选择集群以及读取与集群API Server通信的所需的所有信息(包括API地址、集群用户、验证信息、命名空间等)。
- kubeconfig 文件默认是$HOME/.kube/config 文件，也可以通过kubectl --kubeconfig=/path/filename来临时指定
- 还可以通过kubectl --namespace=NS --username=XXXX  等选项来临时覆盖kubeconfig中的内容
- **配置文件长这样**
可以执行`kubectl config set-cluster --....`
```
apiVersion: v1
clusters:
- cluster: 
    certificate-authority: /etc/kubernetes/pki/ca.crt                       ##server的校验文件，验明集群身份。此处也支持certificate-authority-data: cry的具体内容| base64  编码
    server: https://192.168.0.77:6443                                       ##apiserver地址
  name: dev-cluster                                                         ##自定义的集群名称，为了区分不同集群，供上下文选择
- cluseter:
    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0...               ##这是cat /etc/kubernetes/pki/ca.crt | base64 经过编码的内容
    server: https://192.168.0.99:6443
    name: test-cluster
contexts:                                                                   ##上下文(翻译的不直观，就这么叫吧。kubectl通过上下文来选择要连接的集群)
- context:
    cluseter: dev-cluster
    user: dev-admin
    namespace: kube-system                                                  ##指定访问集群使用的默认命名空间
  name: dev-adm@dev-cluseter
- context:
    cluseter: test-cluster
    user: test-adm
  name: test-adm@teat-cluseter
current-context: name: dev-adm@dev-cluseter                                 ##默认选择的上下文
kind: Config 
users:                                                                      ##用户列表，也是带crt/key认证的
- name: dev-admin
  user:
    client-certificate: /etc/kubernetes/pki/apiserver-kubelet-client.crt    ##跟上面cluster的ca一样的，支持文件或者编码
    client-key: /etc/kubernetes/pki/apiserver-kubelet-client.key
- name: test-adm
  user:
    client-certificate-data:
    client-key-data:
```
kubectl默认读取$HOME/.kube/config的内容,也可指定`kubectl --kubeconfig=配置文件 [command]`，还可以指定选项覆盖配置文件中的配置项`kubectl --kubeconfig=配置文件 --user=t-bag --namespace=kube-system [command]`
>**kubeconfig的其他操作
- 1、添加或者修改一个集群
```shell
kubectl config set-cluster 集群名称 \
--server=https://192.168.0.77:6443 \
--certificate-authority=/path/cafile \
....
```
- 2、添加或者修改用户凭据
```shell
kubectl config set-credentials foo --username=foo --password=pass
kubectl config set-credentials foo --token=mysecrettokenXFSSSFF
```
- 3、添加上下文，即将集群和用户联系起来
```shell
kubectl config set-context 上下文名称 --cluseter=集群名称 --user=foo --namespace=default
```

- 4、切换上下文
```shell
kubectl config current-context                ##获取当前上下文
kubectl config get-contexts                   ##获取所有上下文
kubectl config use-context 上下文名称         ##切换上下文
kubectl config delete-context 上下文          ##删除上下文 
```
