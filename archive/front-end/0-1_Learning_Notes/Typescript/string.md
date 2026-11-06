# 字符串处理怎样从位置索引走到用户看见的文字？

**案例背景：** 报表标题是 `"  Hello World! 😀  "`，要去掉边缘空白、找到关键词、替换标签，并正确计算展示长度。字符串值不可变；变换方法返回新字符串，查找方法则返回位置或匹配信息，原字符串不会被原地修改；但“一个位置”究竟是什么单位，决定了截断是否安全。Unicode 分段的深入机制见[文本算法为什么必须先选择字符单位？](../../../../engineering-foundations/algorithms/text-units-and-algorithms.md)。

## 先处理什么，再按什么单位找位置？

```javascript
const title = "  Hello World! 😀  ";
const trimmed = title.trim();               // "Hello World! 😀"
const position = trimmed.indexOf("World"); // 6
const label = trimmed.slice(position, position + 5); // "World"
const renamed = trimmed.replace("World", "Everyone");
// "Hello Everyone! 😀"；trimmed 未变
```

`trim` 只去两端空白，不合并中间空格。`indexOf` / `lastIndexOf` 返回首个/最后一个匹配位置，未找到是 −1；查找失败后不能直接拿 −1 当正常切片起点。`indexOf(searchString, position)` 的第二参数指定开始查找的位置；`split(separator, limit)` 的第二参数限制返回项数，不保证保留余下文本。`concat` 和 `+` 拼接出新字符串，`split(' ')` 按分隔符产出数组，并不是自然语言分词。

## 为什么 length、索引与可见字符数量不一致？

JavaScript 字符串由 UTF-16 code unit（代码单元）组成。`"Hello".length` 为 5；`"😀".length` 为 2，因为它用 surrogate pair（代理对）表示。`charAt(i)` 返回一个代码单元的字符串，越界为 `""`；`charCodeAt(i)` 返回代码单元数值，越界为 NaN。方括号越界则是 `undefined`。

```javascript
console.log("Hello".charAt(1), "Hello".charCodeAt(1)); // "e", 101
console.log([..."😀"]); // ["😀"]
console.log(String.fromCharCode(72,101,108,108,111)); // "Hello"
console.log(String.fromCodePoint(0x1F600)); // "😀"
```

`for...of` 或字符串展开按 code point（码点）推进，不会把有效代理对拆开；但组合重音或家庭 emoji 仍可能包含多个码点。需要按用户感知的字符边界截断时，可用 grapheme cluster（字素簇）分段作为近似；它不等同于字体最终绘制的 glyph（字形），不能直接把 `split('')`、`slice` 或码点遍历当成它。

回到去空白后的 `"Hello World! 😀"`：`.length` 是 15 个代码单元，`[...trimmed].length` 是 14 个码点；这个特定字符串也恰好有 14 个字素簇。用 `new Intl.Segmenter("en", {granularity:"grapheme"})` 的 `segment(trimmed)` 遍历并计数得到 14；若标题换成带组合重音或复合 emoji 的文字，码点数与字素簇数便可能分开。

## 三种切片参数为何不能互换？

| 方法 | 第二参数 | 负数和次序 |
|---|---|---|
| `slice(start,end)` | 不包含的结束位置 | 负数从末尾换算；不会交换起止值 |
| `substring(start,end)` | 不包含的结束位置 | 负数按 0；开始大于结束时交换两者 |
| 旧 `substr(start,length)` | 长度 | Annex B 兼容方法；维护旧代码时识别，新代码用 slice |

`"Hello".slice(1,4)` 是 `"ell"`；`substring(4,1)` 也是 `"ell"`，但 `slice(4,1)` 是空串。三者的位置都是代码单元，不会自动保护 emoji 或字素簇边界。旧例 `"Hello World!".substr(1,4)` 为 `"ello"`，等价的本例 slice 为 `slice(1,5)`。

## 文本匹配、替换和排序分别要什么契约？

| 操作 | 返回什么 | 要留意的条件 |
|---|---|---|
| `search(/\bW\w+/)` | 首个匹配位置或 −1 | 本例匹配 World；不是完整 Unicode 词法分析 |
| `match(/\bW\w+/)` | 匹配数组或 null | 无 `g` 时还含 index/input 等信息；不是只含字符串的普通结果展示 |
| `replace('World','Everyone')` | 新字符串 | 字符串模式只替换首处；多处用 replaceAll 或合适全局正则 |
| `localeCompare(other,locale)` | 负数、0、正数 | 不保证恰好 −1/1；语言环境和比较选项影响顺序 |
| `toLowerCase` / `toUpperCase` | 新字符串 | 大小写映射可改变长度，不是任意语言的等价比较 |
| `toLocaleLowerCase` / `toLocaleUpperCase` | 按指定环境映射的新字符串 | 土耳其语 `"I".toLocaleLowerCase('tr')` 为 `"ı"`，`"i".toLocaleUpperCase('tr')` 为 `"İ"` |

批量排序可创建一个 `Intl.Collator` 并复用其 `compare`。是否忽略大小写、重音，以及如何归一化，是具体搜索/排序契约；不能随意把 lowerCase 后相等当作所有文本的相等规则。

`String(123)` 转为原始字符串 `"123"`；`new String('Hello')` 创建包装对象，`typeof` 为 object，`valueOf()` 和 `toString()` 可取得字符串值。日常数据用原始字符串即可，包装对象身份不同会给判断和集合键增加不必要差异。

> [!info]- 来源
> - 代码单元、切片、匹配、替换与构造方法：[ECMAScript 2026 Text Processing](https://tc39.es/ecma262/2026/multipage/text-processing.html)，String 对应方法；核对 2026-11-06。
> - 旧 substr 的兼容契约：[ECMAScript Annex B](https://tc39.es/ecma262/2026/multipage/additional-ecmascript-features-for-web-browsers.html#sec-string.prototype.substr)。
> - 字素簇分段：[Unicode UAX #29](https://www.unicode.org/reports/tr29/)；语言环境排序：[ECMA-402 Collator](https://tc39.es/ecma402/#collator-objects)。
