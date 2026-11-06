# 为什么不同数组展平方式会产生不同空位？

逐层 [].concat(...items)、数组展开与 flat 对稀疏空位的不同处理已并入[JavaScript 数组操作如何处理空位、修改与复制？](../../../frontend/javascript/arrays.md#flat%E3%80%81%E9%80%92%E5%BD%92%E4%B8%8E%E9%80%90%E5%B1%82%20concat%20%E7%9A%84%E7%A9%BA%E4%BD%8D%E7%BB%93%E6%9E%9C)，并保留原 sparse 输入的逐项结果。
