# 数组去重策略有什么区别？

去重策略的相等规则、顺序、重复记录胜出方式与排序边界已并入[JavaScript 数组操作如何处理空位、修改与复制？](../../../frontend/javascript/arrays.md#%E5%8E%BB%E9%87%8D%E5%89%8D%E5%85%88%E9%80%89%E2%80%9C%E7%9B%B8%E5%90%8C%E2%80%9D%E7%9A%84%E5%AE%9A%E4%B9%89)。其中保留了 indexOf 对 NaN 的处理、Set 的 SameValueZero、按业务字段用 Map 保留最后值，以及 comparator / same 配对的排序实现。
