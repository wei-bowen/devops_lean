### 基本概念
![](./iptables.png)
iptables有4表5链n条规则的概念.
比如我们要去上海(可能是进入上海市逗留，可能只是借道做飞机去国内其他城市或者国外)，根据具体情况来决定需要接受哪些关卡的检查。<br>
关卡可能有火车站、出入境检疫所、机场登机口等。iptables种的检查关卡就是链。<br>
每个关卡可能会有多个部门对我们进行检查,比如在火车站这道关卡，下了火车，上海市公安局会检查你是不是逃犯、火车站看你是不是买票了、卫生局看你是不是核算检查阳性。<br>
iptables的表概念就是对应不同的检查部门，负责不同的职能，按不同的规则进行检查，而规则就是只能部门在检查关卡设定的检查规则。

**四表**
```
- filter  负责过滤
- nat     负责地址转换
- mangle  拆解并修改报文
- raw     基础用不到。关闭nat表上启用的连接追踪机制
```
**五链**
```
- PREROUTING
- INPUT
- FORWARD
- OUTPUT
- POSTROUTING
```
**n条规则**
```
- target      处理动作
- prot        协议类型
- opt         额外选项
- source      源地址
- destination 目标地址
```