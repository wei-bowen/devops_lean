# 第一章、创建一个kubernetes集群
### 1、环境准备
 3台虚拟机/物理机。均为双核4G，硬盘70G，系统为centos7.6. 没有条件就降低配置，应该不是很要紧。 <br>
   IP地址(IP网络使用nat网络，dhcp自动分配即可)为： 
 + 192.168.0.77  k8s-master   
 + 192.168.0.88  k8s-node1
 + 192.168.0.99  k8s-node2
### 2、安装前配置(未特意说明的，默认在全部机器上执行)
>**关闭防火墙**
``` 
systemctl stop firewalld 
systemctl disable firewalld
 ```
 >**关闭selinux**
 ```shell
 setenforce 0                                                       ###当场关闭，重启后恢复
 sed 's#SELINUX=enforcing#SELINUX=disabled#' /etc/selinux/config
 ```
 >**关闭iptables**
 ```shell
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -F
iptables -L -n
```
>**关闭swap**
```shell
swapoff -a          ##临时关闭
vim /etc/fstab      ##将swap挂在行注释掉
```
>**配置主机名(在对应机器上执行)**
```shell
hostnamectl set-hostname k8s-master && bash       ##在主节点执行，bash是当场刷新
hostnamectl set-hostname k8s-node1 && bash        ##节点1执行
hostnamectl set-hostname k8s-node1 && bash        ##节点2执行
```
>**在master节点添加IP/主机名解析**
```shell
cat >> /etc/hosts << EOF
192.168.31.61 k8s-master
192.168.31.62 k8s-node1
192.168.31.63 k8s-node2
EOF
```
>**将桥接的IPv4流量传递到iptables的链：**
```shell
cat > /etc/sysctl.d/k8s.conf << EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF
sysctl --system
```
>**配置时间同步**
```shell
yum install ntpdate -y
ntpdate time.windows.com            ##注：也可以配置master节点为各个节点的时间同步中心，只要确保节点间时间一致即可
```
### 3、软件安装(docker\kubeadm\kubelet)
>**docker安装**
```shell
yum install -y yum-utils device-mapper-persistent-data lvm2                                     ##安装依赖包
wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo          ##安装epel源，是为了安装container-selinux
yum install epel-release -y
yum install container-selinux -y
yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo           ##安装docker-ce的yum源
yum install -y docker-ce
systemctl start docker && systemctl enable docker                                               ##启动docker并配置开机启动
echo "OPTIONS='--registry-mirror=https://mirror.ccs.tencentyun.com'" >> /etc/sysconfig/docker   ##配置国内加速镜像源访问dockehub
systemctl daemon-reload
systemctl restart docker
```
>**安装kubeadm\kubelet**
```shell
cat > /etc/yum.repos.d/kubernetes.repo << EOF                                               ##安装阿里云kubernetes相关yum源
[kubernetes]
name=Kubernetes
baseurl=https://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64
enabled=1
gpgcheck=0
repo_gpgcheck=0
gpgkey=https://mirrors.aliyun.com/kubernetes/yum/doc/yum-key.gpg https://mirrors.aliyun.com/kubernetes/yum/doc/rpm-package-key.gpg
EOF
yum install -y kubelet-1.18.0 kubeadm-1.18.0 kubectl-1.18.0                                 ##指定版本号安装
systemctl restart kubelet && systemctl enable kubelet
```
### 4、master节点初始化
```shell
kubeadm init \
  --apiserver-advertise-address=192.168.0.77 \
  --image-repository registry.aliyuncs.com/google_containers \
  --kubernetes-version v1.18.0 \
  --service-cidr=10.96.0.0/12 \
  --pod-network-cidr=10.244.0.0/16 \
  --ignore-preflight-errors=all
```
**相关配置项说明：**  
- --apiserver-advertise-address 集群对外通告地址，局域网内默认为master节点IP地址
- --image-repository  由于默认拉取镜像地址k8s.gcr.io国内无法访问，这里指定阿里云镜像仓库地址
- --kubernetes-version K8s版本，与上面安装的一致
- --service-cidr 集群内部虚拟网络，Pod统一访问入口
- --pod-network-cidr Pod网络，，与下面部署的CNI网络组件yaml中保持一致
<br>
也支持通过配置文件安装`kubeadm init --config kubeadm.yaml` 下面是一个范例，了解大致语法即可
```yaml
apiVersion: kubeadm.k8s.io/v1alpha1
kind: MasterConfiguration
controllerManagerExtraArgs:
  horizontal-pod-autoscaler-use-rest-clients: "true"   ##允许使用自定义资源进行自动水平扩展
  horizontal-pod-autoscaler-sync-period: "10s"
  node-monitor-grace-period: "10s"
apiServerExtraArgs:
  runtime-config: "api/all=true"
kubernetesVersion: "stable-1.11"
```

**安装成功后配置（按图说明即可）：** <br>

![安装成功截图](https://github.com/wei-bowen/kubernetes_learn/blob/master/images/install_finnish.png)

因为kubernetes集群默认需要加密方式访问。下面的命令是将刚部署生成的kubernetes集群的安全配置文件保存到当前用户的.kube目录下，kubectl会默认使用目录下的授权信息访问集群。
```shell
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```
- 复制安装成功的这一段代码（在节点上执行可加入集群，24小时内有效）
```
kubeadm join 192.168.0.77:6443 --token nuja6n.o3jrhsffiqs9swnu --discovery-token-ca-cert-hash sha256:63bca849e0e01691ae14eab449570284f0c3ddeea590f8da988c07fe2729e924
```
**kubeadm init工作流程**
- Preflight Checks. 检查Linux内核版本、cgroups模块、hostname、kubelet、端口占用、基础linux指令、dockker登
- 在/etc/kubernetes/pki下生成对外提供服务作序的各种证书。（可以拷贝现有证书到目录下，kubeadm发现后会跳过此步骤）
- 为master组件生成Pod配置文件。通过Static Pod的方式，Pod Yaml文件仿造/etc/kubernetes/manifests路径下即可启动。启动后通过检查localhost:6443/healthz检查组件状态
- 为集群生成bootstrap token,让其他节点可以通过token加入集群
- 将ca.crt登Master节点的重要信息，以configma的形式存入etcd,叫cluster-info
- 安装默认插件kuber-proxy和DNS

### 5、部署k8s集群网络插件(推荐calico网络，也可以自行搜索flannel安装)。

master节点执行
```shell
wget https://docs.projectcalico.org/manifests/calico.yaml
vim calico.yaml
##搜寻CALICO_IPV4POOL_CIDR 找到后将该行- name前面的#号删掉取消注释，下一行的value前面的#号也删掉，并将IP端192.168.0.0改成我们在master初始化的时候配置的10.244.0.0
```

### 6、节点加入集群
在节点上执行安装完成后的kubeadm join 命令即可加入集群，如果已过24小时或者不小心关闭窗口没复制到那个命令，可以 <br>
在master节点上执行命令重新生成token
```shell
kubeadm token create                                                                                                                              ##创建token
kubeadm token list                                                                                                                                ##查看生成的token
openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | openssl rsa -pubin -outform der 2>/dev/null | openssl dgst -sha256 -hex | sed 's/^.* //'    ##生成token校验码
```
然后到节点上执行
```shell
kubeadm reset     ##被踢出后需要重新加入的节点需要执行此命令清空老的配置，第一次加入的节点不需要
kubeadm join 192.168.0.77:6443 --token $(上面生成的token) --discovery-token-ca-cert-hash sha256:$(上面生成的token校验码)
```
此时在master节点执行 kubectl get nodes -o wide 即可看到加入集群的节点信息

### 7、最终验证
```shell
kubectl get nodes -o wide                     ###应该可以看到所有节点为ready状态
kubectl create deployment web --image=nginx   ##创建一个叫名为web的deployment
kubectl scale deployment web --replicas 2     ##扩展web创建2个pod，正常情况下会一个node节点创建一个
kubectl get pods -o wide                      ##可以看到每个节点都安装了一个pod
kubecte delete all --all                      ##清空刚创建的资源
```

### 8、部署Dashboard可视化插件(可选)
`kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.0-rc6/aio/deploy/recommended.yaml`

### 9、部署容器存储插件（可选）
存储插件可以在容器里挂载一个基于网络或者其他机制的远程数据卷，使得在容器中创建的文件，实际上是保存在远程存储服务器上，或者以分布式的方式保存在多节点上，而与当前宿主机没有任何绑定关系。这样，无论在其他哪个宿主机上启动新的容器，都可以请求挂载指定的持久化存储卷，从而访问到数据卷保存的内容。<br>
此处演示一个可用的基于ceph的开源项目。后面存储章节再讲。
```shell
kubectl apply -f https://raw.githubusercontent.com/rook/rook/master/cluster/examples/kubernetes/ceph/common.yaml
kubectl apply -f https://raw.githubusercontent.com/rook/rook/master/cluster/examples/kubernetes/ceph/operator.yaml
kubectl apply -f https://raw.githubusercontent.com/rook/rook/master/cluster/examples/kubernetes/ceph/cluster.yaml
```
