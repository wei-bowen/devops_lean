![redis知识全景](images/redis_qj.jpg)
- **高性能**，包括线程模型、数据结构、持久化、网络框架
- **高可靠**，包括主从复制、烧饼机制
- **高可扩展**，数据分片，负载均衡

redis特性
- key-value型数据库
- 内存键值数据库。所有操作都在内存上完成，这是它快的基础
- 单线程，高性能
- 使用哈希表作为key-value索引
- 通过网络框架进行访问，而非动态库
- 支持日志/快照两种持久化方式

redis是key-value键值对型数据库，value支持
- Strng
- 哈希表
- 列表
- 集合

支持的操作
- PUT: 新写入一个key-value对
- SET：更新一个key-value对
- GET：根据key读取value
- DELETE: 根据key删除键值对
