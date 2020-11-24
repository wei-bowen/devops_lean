### 基本概念
![](./iptables.png)
iptables有4表5链n条规则的概念.
比如我们要去上海(可能是进入上海市逗留，可能只是借道做飞机去国内其他城市或者国外)，根据具体情况来决定需要接受哪些关卡的检查。<br>
关卡可能有火车站、出入境检疫所、机场登机口等。iptables种的检查关卡就是链。<br>
每个关卡可能会有多个部门对我们进行检查,比如在火车站这道关卡，下了火车，上海市公安局会检查你是不是逃犯、火车站看你是不是买票了、卫生局看你是不是核算检查阳性。<br>
iptables的表概念就是对应不同的检查部门，负责不同的职能，按不同的规则进行检查，而规则就是只能部门在检查关卡设定的检查规则。<br>

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
- 除了这五道链，用户还可以自定义链
```
**n条规则**
```
- target      处理动作
- prot        协议类型
- opt         额外选项
- source      源地址
- destination 目标地址
```
因为常用的也就控制流量输入输出和转发，所以只要学习filer过滤、nat转发两张表即可，涉及INPUT/OUTPUT链。
### iptables查询
常规查询: `iptables -t filter -nL` 一般来说filer表最常用，默认就是查filter表，所以-t filter可以省略。可用选项如下
```
-t filter       :   后接那四个表名中的一个,指定要查询的表
-L <链名>       :   后接链名，自定要查询的链下面的规则。例如-L INPUT  。如果不带链名就是查询表下所有链的规则
-v              :   输出详细信息
-n              :   解析成ip地址,比如有规则是接受所有来源IP地址的数据，不加-n就是显示anywhere，加了就显示0.0.0.0/0
--line          :   带序号输出

```

### filer过滤规则管理
iptables的基本管理规则:
- 在一道关卡(链)上可能要接受多个部门(tables)的检查，他们是有优先级的，同时在场时raw>mangle>nat>filter
- 在关卡(链)上接受检查时，是按不同部门(tables)设定的rules顺序检查，只要符合了其中一条匹配规则后即执行检查后操作(放行ACCEPT/丢弃DROP/转到自定义链继续检查)。不再执行后续规则的匹配。
- 未匹配到任何规则时，执行默认操作(policy)

#### 设定默认规则
`iptables -t filter -P INPUT (DROP|ACCEPT)`   将表的指定链默认操作设为放行或者丢弃。

#### 添加规则
例如`iptables -A INPUT -s 192.168.0.90 -j DROP`   在INPUT关卡末尾添加一条规则，数据包来自192.168.0.90时执行丢弃操作。其他可用选项：
```
-t filter           :     指定表面同样默认filter可以省略，其他如nat需要指定
-A INPUT            :     在INPUT关卡末尾添加一条规则。前面说过iptables是按顺序匹配的，顺序有意义。A指appendend追加
-I INPUT            :     在INPUT关卡第一条添加规则。I指insert插入
-I INPUT 6          :     指定位置插入，放在第6位。
-j                  :     当匹配时执行的操作。可以是ACCEPT放行、DROP丢弃、或者指定一个链名(可以是自定义链)，流转到下一个链进行检查
```

#### 删除规则
```
iptables -t filter -F INPUT                             -F 链名：删除INPUT链下所有规则
iptables -D INPUT 3                                     -D 链名 序号：删除指定链下特定序号的规则
iptables -t filter -D INPUT -s 192.168.1.146 -j DROP    删除链下指定内容的规则
```
#### 修改规则
只能修改动作，例如上面拒绝了192.168.0.90的数据，改为放行
`iptables -R INPUT 1 -s 192.168.0.90 -j ACCEPT`:麻烦的是既要带序号又要带原来的匹配规则。不如直接删了重建。

#### 保存规则
上述所有操作都是临时的，重启失效。想要永久生效必须保存在配置文件/etc/sysconfig/iptables中
`service iptables save`保存即可。也可以使用导出命令将规则写入配置文件`iptables-save > /etc/sysconfig/iptables`

#### 读取规则
可以在其他机器上指定`iptables-save > $file`导出到指定文件中，然后文件拷贝到本机执行导入`iptables-restore < $file`。
批量设置规则时时可以自己写规则文件然后导入

```
