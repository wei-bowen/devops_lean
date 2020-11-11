类似linux上的yum，用于在k8s上部署管理复制的应用。<br>
**Helm主要概念**
- Chart: 一个Helm包，包含了运行一个应用所需要的工具和资源定义，还可能包含k8s集群中的服务定义
- Release:在K8S集群上运行的一个Chart实例。Chart可以被安装多次，每次都是一个独立Release
- Repository:存放和共享Chart的仓库
**Helm安装**
```shell
wget https://get.helm.sh/helm-v3.4.0-linux-amd64.tar.gz
tar -zxf helm-v3.4.0-linux-amd64.tar.gz
mv linux-amd64/helm /usr/bin/
```
