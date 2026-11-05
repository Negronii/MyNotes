# Does Lodash _.uniqueId create a secure unique identifier? / Lodash _.uniqueId 会生成安全且全局唯一的标识符吗？

No. Lodash _.uniqueId(prefix) returns a string based on an incrementing counter in that Lodash runtime. The counter depends on prior calls and does not guarantee uniqueness across processes or provide a security token. / 不会。Lodash _.uniqueId(prefix) 基于当前 Lodash 运行时中的递增计数器返回字符串；计数取决于先前调用，不保证跨进程唯一，也不能作为安全令牌。

~~~javascript
_.uniqueId('contact_');
// A value such as "contact_1"; the suffix depends on earlier calls in this runtime.
~~~

Choose identifiers by their actual contract: a UI-local key, database key, globally unique ID, and secret capability token are different needs. See [Lodash](../../../frontend/libraries/lodash.md) for the general utility reference.

**Version source / 版本来源:** [Lodash 4.17.21 documentation](https://github.com/lodash/lodash/blob/4.17.21/doc/README.md).
