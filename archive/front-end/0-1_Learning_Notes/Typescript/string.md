# 字符串处理怎样从位置索引走到用户看见的文字？

**案例背景：** 报表标题是 `"  Hello World! 😀  "`，要去掉边缘空白、找到关键词、替换标签，并正确计算展示长度。字符串值不可变；变换方法返回新字符串，查找方法则返回位置或匹配信息，原字符串不会被原地修改；但“一个位置”究竟是什么单位，决定了截断是否安全。Unicode 分段的深入机制见[文本算法为什么必须先选择字符单位？](../../../../engineering-foundations/algorithms/text-units-and-algorithms.md)。

## 先处理什么，再按什么单位找位置？

```javascript
const title = "  Hello World! 😀  ";
const trimmed = title.trim();               // "Hello World! 😀"
const keyword = "World";
const position = trimmed.indexOf(keyword);  // 6 个 UTF-16 编码单元偏移
const label = trimmed.slice(position, position + keyword.length); // "World"
const renamed = trimmed.replace(keyword, "Everyone");
// "Hello Everyone! 😀"；trimmed 未变
```

`trim` 只去两端空白，不合并中间空格。`indexOf` / `lastIndexOf` 返回首个/最后一个匹配位置，未找到是 −1；查找失败后不能直接拿 −1 当正常切片起点。`indexOf(searchString, position)` 的第二参数指定开始查找的位置；`split(separator, limit)` 的第二参数限制返回项数，不保证保留余下文本。`concat` 和 `+` 拼接出新字符串，`split(' ')` 按分隔符产出数组，并不是自然语言分词。

## 为什么 length、索引与可见字符数量不一致？

JavaScript 字符串由 UTF-16 code unit（代码单元）组成。`"Hello".length` 为 5；`"😀".length` 为 2，因为它用 surrogate pair（代理对）表示。`charAt(i)` 返回一个代码单元的字符串，越界为 `""`；`charCodeAt(i)` 返回代码单元数值，越界为 NaN。方括号越界则是 `undefined`。

```javascript
console.log("Hello".charAt(1), "Hello".charCodeAt(1)); // "e", 101
console.log("😀".charCodeAt(0).toString(16), "😀".codePointAt(0).toString(16)); // "d83d", "1f600"
console.log("😀".codePointAt(1).toString(16)); // "de00"：索引 1 指向代理对的低位
console.log([..."😀"]); // ["😀"]
console.log(String.fromCharCode(72,101,108,108,111)); // "Hello"
console.log(String.fromCodePoint(0x1F600)); // "😀"

// 接续上例：displayText 是去空白后的同一标题；renamed 是替换后的版本。
const displayText = trimmed;
const segmenter = new Intl.Segmenter("en", {granularity:"grapheme"});
const graphemeCount = Array.from(segmenter.segment(displayText)).length;
console.log(displayText.length, [...displayText].length, graphemeCount); // 15, 14, 14
const renamedGraphemes = Array.from(segmenter.segment(renamed)).length;
console.log(renamed.length, [...renamed].length, renamedGraphemes); // 18, 17, 17

const utf16Prefix = displayText.slice(0, 14);
const graphemePrefix = Array.from(
  segmenter.segment(displayText),
  ({segment}) => segment
).slice(0, 14).join("");
console.log(JSON.stringify(utf16Prefix)); // "Hello World! \ud83d"
console.log(JSON.stringify(graphemePrefix)); // "Hello World! 😀"

for (const sample of ["😀", "e\u0301", "👨‍👩‍👧‍👦"]) {
  const codePoints = [...sample].length;
  const graphemes = Array.from(segmenter.segment(sample)).length;
  console.log(sample, sample.length, codePoints, graphemes);
}
```

`codePointAt(i)` 在有效代理对的高位读取完整码点，但 `i` 仍按 UTF-16 编码单元计；指向代理对低位时只返回低代理项数值。`for...of` 或字符串展开按 code point（码点）推进，不会把有效代理对拆开；但组合重音或家庭 emoji 仍可能包含多个码点。需要按用户感知的字符边界截断时，可用 grapheme cluster（字素簇）分段作为近似；它不等同于字体最终绘制的 glyph（字形），不能直接把 `split('')`、`slice` 或码点遍历当成它。

长度对比和截断都使用同一份去空白后的 `displayText = trimmed`：它有 15 个 UTF-16 编码单元、14 个码点和 14 个字素簇。替换后的 `renamed = "Hello Everyone! 😀"` 则分别有 18、17、17 个。`displayText.slice(0, 14)` 的结束位置按代码单元计且不包含索引 14，因此留下 emoji 的高代理项 `\ud83d`，没有完整字符；代码用 `JSON.stringify` 把这个未配对代理项显示出来。按字素簇取前 14 项则保留完整的 😀；因为这个例子正好有 14 个字素簇，该结果仍是整份去空白标题。

| 输入 | length：UTF-16 编码单元 | 字符串展开：码点 | Intl.Segmenter：字素簇 |
|---|---:|---:|---:|
| 😀 | 2 | 1 | 1 |
| é（e 加组合重音） | 2 | 2 | 1 |
| 👨‍👩‍👧‍👦（家庭 emoji） | 11 | 7 | 1 |

上述分段计数在 Node.js v26.13.0（ICU 79.1、Unicode 18.0）下复算；使用 Intl.Segmenter 的运行时需要支持该 API，分段结果也可能随国际化数据版本变化。

## 三种切片参数为何不能互换？

| 方法 | 第二参数 | 负数和次序 |
|---|---|---|
| `slice(start,end)` | 不包含的结束位置 | 负数从末尾换算；不会交换起止值 |
| `substring(start,end)` | 不包含的结束位置 | 负数按 0；开始大于结束时交换两者 |
| 旧 `substr(start,length)` | 长度 | 负起点从末尾换算；负长度按 0 处理并返回空串。Annex B 兼容方法，维护旧代码时识别 |

`"Hello".slice(1,4)` 是 `"ell"`；`substring(4,1)` 也是 `"ell"`，但 `slice(4,1)` 是空串。旧例 `"Hello World!".substr(1,4)` 为 `"ello"`，等价的本例 `slice(1,5)` 也为 `"ello"`。`"Hello World!".substr(-5,2)` 为 `"or"`：负起点从末尾换算；`"Hello World!".substr(7,-2)` 为 `""`：负长度按 0 处理。三者的位置和长度参数都以代码单元计，不会自动保护 emoji 或字素簇边界。

## 文本匹配、替换和排序分别要什么契约？

| 操作 | 结果与条件 |
|---|---|
| `search` / `match` | `search` 返回首个匹配位置或 −1；`match` 返回匹配数组或 `null`。无 `g` 时匹配数组含 `index`、`input` 等信息；有 `g` 且匹配成功时返回匹配字符串数组。 |
| `replace` / `replaceAll` | 返回新字符串；字符串模式的 `replace` 只替换首处，多处替换用 `replaceAll` 或合适的全局正则。 |
| `localeCompare` | 负数、0、正数分别表示调用方字符串排在参数前、在当前选项下相等、排在参数后；返回值不保证正好是 −1 或 1，语言环境和选项影响顺序。 |
| `collator.compare` | 用 `new Intl.Collator(...)` 创建比较器后，可在批量排序中复用其 `compare`；具体规则取决于语言环境和比较选项。 |
| `toLowerCase` / `toUpperCase` | 返回新字符串；大小写映射可改变长度，不代表任意语言下的文本等价关系。 |
| `toLocaleLowerCase` / `toLocaleUpperCase` | 返回按指定语言环境映射的新字符串；不同语言环境可能有不同大小写结果。 |

在 `"Hello World!"` 上，`search(/\bW\w+/)` 返回 6；`match(/\bW\w+/)` 返回 `World` 的匹配数组，结果的 `index` 为 6、`input` 是原字符串。这种正则只说明本例的简单匹配，不是完整的 Unicode 词法分析。前面的案例用 `replace("World", "Everyone")` 替换首处；若要替换多处，可用 `replaceAll` 或合适的全局正则。

土耳其语中，`"I".toLocaleLowerCase("tr")` 得到 `"ı"`，`"i".toLocaleUpperCase("tr")` 得到 `"İ"`。搜索或排序契约还要决定是否忽略大小写、重音，以及如何归一化；不能把先调用 `toLowerCase()` 后相等，当作所有文本的等价规则。

`String(123)` 转为原始字符串 `"123"`；`new String('Hello')` 创建包装对象，`typeof` 为 object，`valueOf()` 和 `toString()` 可取得字符串值。日常数据用原始字符串即可，包装对象身份不同会给判断和集合键增加不必要差异。

> [!info]- 来源
> - UTF-16 字符串表示、String 构造和包装对象、length、charAt、charCodeAt、codePointAt、索引、切片、匹配、替换、大小写转换与迭代：[ECMAScript 2026, §§6.1.4、22.1.1–22.1.4.1](https://tc39.es/ecma262/2026/multipage/text-processing.html)，核对 2026-11-12。
> - 旧 `substr(start, length)` 的 Annex B 兼容契约：[ECMAScript 2026 Annex B](https://tc39.es/ecma262/2026/multipage/additional-ecmascript-features-for-web-browsers.html#sec-string.prototype.substr)，核对 2026-11-12。
> - Intl.Segmenter 的 grapheme 粒度及分段记录：[ECMA-402 2026, §§19.1–19.7](https://tc39.es/ecma402/2026/#segmenter-objects)；默认扩展字素簇规则：[Unicode UAX #29, Unicode 18.0.0, Revision 49](https://www.unicode.org/reports/tr29/tr29-49.html)，2026-09-01。
> - localeCompare、Intl.Collator 和语言环境大小写映射：[ECMA-402 2026, §§10.3.3、20.1.1–20.1.3](https://tc39.es/ecma402/2026/#collator-objects)，核对 2026-11-12。
> - 运行复算：Node.js v26.13.0，ICU 79.1，Unicode 18.0，CLDR 49.0；不据此断言其它运行时使用相同国际化数据。
