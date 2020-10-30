## Pod和集群节点的自动伸缩
- 获取被伸缩资源对象所管理的所有Pod度量(需要metrics server配合cAdvisior完成)
- 计算使度量数值到达所指定目标数值所需的Pod数量
- 更新被伸缩资源的replicas字段完成横向伸缩
### HPA:基于CPU使用率配置pod的自动横向伸缩
`kubectl autoscale deployment centos --cpu-percent=30 --min=1 --max=5 --dry-run=client -o yaml`
```yaml
apiVersion: autoscaling/v1
kind: HorizontalPodAutoscaler       ##Horizontal水平   Autoscaler自动伸缩器。autosaler单次扩容最多翻倍。扩容最多3分钟触发一次，缩容5分钟
metadata:
  name: centos-autoscaler
spec:
  maxReplicas: 5
  minReplicas: 1                            ##动态调整depoyment的replicas字段，最小1最大5
  scaleTargetRef:                           ##作用的资源目标
    apiVersion: apps/v1
    kind: Deployment
    name: centos
  targetCPUUtilizationPercentage: 30        ##尽力保持cpu使用率维持再30%以内
```
### 基于自定义度量配置Pod的自动横向伸缩
自定义监控指标，然后根据指标来定义自动伸缩的规则


### 集群自动横向伸缩
