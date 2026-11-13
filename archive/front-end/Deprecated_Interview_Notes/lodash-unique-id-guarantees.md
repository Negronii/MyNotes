# Does Lodash `_.uniqueId` create a secure unique identifier? / Lodash `_.uniqueId` 会生成安全且全局唯一的标识符吗？

本页保留为旧入口。`_.uniqueId` 使用当前 Lodash 模块实例的递增计数器；它不提供跨进程或多个模块实例的唯一性保证，也不是安全令牌。说明见[递增计数器为什么不能保证跨实例唯一？](../../../frontend/libraries/lodash.md#%E5%85%B6%E4%BB%96%E6%96%B9%E6%B3%95%E5%85%88%E7%9C%8B%E8%BF%94%E5%9B%9E%E5%80%BC%E5%92%8C%E8%BE%B9%E7%95%8C)。
