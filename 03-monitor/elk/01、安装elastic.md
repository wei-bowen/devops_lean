### 安装helm
```shell
wget https://get.helm.sh/helm-v3.4.2-linux-amd64.tar.gz
tar -zxvf helm-v3.4.2-linux-amd64.tar.gz
cd linux-amd64/
mv helm /usr/local/bin/
```

### 安装elastic的helm仓库
```shell
git clone https://github.com/elastic/helm-charts.git
kubectl create ns elastic && kubens elastic
helm install elasticsearch ./helm-charts/elasticsearch --set imageTag=8.0.0-SNAPSHOT
```

### 分配PV
```
kubectl get statefulsets.apps elasticsearch-master -o yaml > state-elastic.yaml  
kubectl delete statefulsets.apps elasticsearch-master
kubectl delete pvc elasticsearch-master-elasticsearch-master-0
kubectl delete pvc elasticsearch-master-elasticsearch-master-1
kubectl delete pvc elasticsearch-master-elasticsearch-master-2
vim state-elastic.yaml                ## 添加 storageClassName: "nfs-storage" 
kubectl apply -f state-elastic.yaml
```
