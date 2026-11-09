# 文本算法应按码元、码点还是字素簇处理？

报表 42 的事件描述可能含 emoji、组合重音或其他扩展文字。JavaScript 字符串索引、Unicode 码点和用户看到的字符不是同一种单位：先定义任务要计数、比较或切分什么，再实现算法。这里第一次说明三个单位：UTF-16 code unit（UTF-16 编码单元）、Unicode code point（Unicode 码点）和 extended grapheme cluster（扩展字素簇）。

## 三种长度会怎样不同？

JavaScript String.length 返回 UTF-16 编码单元数。Array.from 对字符串迭代时把有效代理对组合成一个码点，孤立代理仍单独保留，但组合附加符仍是另一个码点。Intl.Segmenter 的 grapheme 模式按 locale（语言环境）与实现提供的分段规则给出字素簇；这通常接近用户感知字符，但规则可定制，不能把某个 Node 运行时的结果等同于当前 UAX #29 版本的每条边界规则。

~~~javascript
const sample = 'A😀e\u0301';
const codeUnits = sample.length;
const codePoints = Array.from(sample);
const segmenter = new Intl.Segmenter('en', { granularity: 'grapheme' });
const graphemes = Array.from(segmenter.segment(sample), part => part.segment);

console.log(codeUnits);              // 5
console.log(codePoints.length);      // 4
console.log(graphemes);              // ['A', '😀', 'é']
console.log(graphemes.length);       // 3
~~~

这里 A 占 1 个码元和 1 个码点；😀 是代理对，占 2 个码元、1 个码点；e 加 U+0301 组合重音占 2 个码元、2 个码点，却通常成为 1 个字素簇。字符计数不能代替存储大小：若限制请求字节数，还要另外按明确编码计算字节。

Array.from 不会自动把规范等价的不同码点序列变成相同序列。例如预组字符 é 与 e 加组合重音肉眼可相同，但码点逐个比较不同：'é' === 'e\u0301' 为 false，而 NFC 归一化后两者相等。若业务要求规范等价比较，可在明确边界使用 normalize('NFC')；保留原始输入时不要无意改写其码点序列。

## 回文和连续重复要比较什么单位？

原示例的回文函数按码点逆向比较，所以它把代理对当作单个元素，但不会把规范等价序列归一化；若要按用户可见单元比较，先用 Segmenter 切成字素簇。相同函数逻辑可接受不同切分结果：

~~~javascript
function isPalindromeByCodePoint(value) {
  const units = Array.from(value);
  for (let left = 0, right = units.length - 1; left < right; left++, right--) {
    if (units[left] !== units[right]) return false;
  }
  return true;
}

function splitGraphemes(value, locale = 'en') {
  const segmenter = new Intl.Segmenter(locale, { granularity: 'grapheme' });
  return Array.from(segmenter.segment(value), part => part.segment);
}

function isPalindromeByGrapheme(value) {
  const units = splitGraphemes(value);
  for (let left = 0, right = units.length - 1; left < right; left++, right--) {
    if (units[left] !== units[right]) return false;
  }
  return true;
}
~~~

这两个函数都用精确字符串相等比较；若文字规范化属于需求，应先明确是否按 NFC 归一化。UAX #29 的默认扩展字素簇是可复现的分段规则，但语言或应用可进行 tailor（定制），也不是编码字节长度。

最长连续重复示例按码点统计完全相同的连续项，并在并列时返回第一个最长段；空字符串返回空字符、长度 0。对 Array.from('😀😀A')，结果是字符 😀、长度 2，而按 UTF-16 下标遍历会把每个 emoji 拆成两个码元。

以 `AABB` 走查循环：第 2 个 A 使当前段长到 2；读到第一个 B 时先结算 A，best 变成 A/2；第 2 个 B 使当前段长到 2；循环最后一次以 i===length 结算 B。因更新条件是 `currentLength > bestLength` 而非大于等于，并列保留先出现的 A，尾段也不会漏掉。

~~~javascript
function longestConsecutive(value) {
  const characters = Array.from(value);
  if (characters.length === 0) return { char: '', len: 0 };

  let bestChar = characters[0];
  let bestLength = 1;
  let currentLength = 1;
  for (let i = 1; i <= characters.length; i++) {
    if (i < characters.length && characters[i] === characters[i - 1]) currentLength++;
    else {
      if (currentLength > bestLength) {
        bestLength = currentLength;
        bestChar = characters[i - 1];
      }
      currentLength = 1;
    }
  }
  return { char: bestChar, len: bestLength };
}
~~~

## 数字显示和大小写转换如何明确边界？

展示数值通常使用 Intl.NumberFormat，并显式指定 locale，避免依赖用户机器默认区域。格式化规则仍可能受运行时国际化数据版本影响；若输出用于协议或稳定快照，不应把本地化显示当作机器可解析格式。手写版本仅接受可选负号和 ASCII 十进制数字组成的整数字符串，不接受小数、空格或本地化数字。

~~~javascript
function formatNumber(value, locale = 'en-US') {
  return new Intl.NumberFormat(locale).format(value);
}

function formatIntegerThousands(text) {
  if (typeof text !== 'string' || text.trim() !== text || !/^-?\d+$/.test(text)) {
    throw new TypeError('expected an integer string');
  }
  const sign = text.startsWith('-') ? '-' : '';
  const digits = sign ? text.slice(1) : text;
  return sign + digits.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}
~~~

这个正则适合本例限定的 ASCII 整数字符串；普通回溯引擎可能在多个位置的前瞻中重复检查后缀，因此不对任意实现或输入规模声称线性时间。若要明确的单趟线性处理，可从右向左每三位分组再拼接；展示数字则优先使用 `Intl.NumberFormat`。

大小写切换示例只变换 ASCII A–Z 与 a–z，其他码点保持不变。它不是适用于所有语言的大小写转换：Unicode 大小写映射可能依赖 locale，且转换前后长度也未必相同。

~~~javascript
function switchAsciiCase(value) {
  return Array.from(value, character => {
    const code = character.codePointAt(0);
    if (code >= 65 && code <= 90) return String.fromCodePoint(code + 32);
    if (code >= 97 && code <= 122) return String.fromCodePoint(code - 32);
    return character;
  }).join('');
}
~~~

## Trie 怎样共享前缀并限制候选输出？

在合成报表 42 的描述搜索中，输入框要查找以已输入前缀开头的标签。Trie（前缀树）把键拆成一串单位，让有相同前缀的键沿着同一条路径前进；本例沿用本章的码点单位，按 Unicode 码点建边。Array.from 会把有效代理对组合成一个码点，所以 😀 是一条边；组合重音若未归一化，则仍是另一条码点边，不等同于视觉上的一个字素簇。

匹配合约选择 NFC（Normalization Form C，规范化形式 C）：写入键和查询前缀都先规范化，把规范等价的码点序列映射到同一路径。因而预组字符 café 与 cafe 加 U+0301 的查询相同；键以规范化后的形式枚举。NFC 不是去重音或兼容字符折叠：单独输入 cafe 不匹配规范化后的 café，若产品要不区分重音或处理兼容字符，必须另外定义匹配规则。保存原输入展示时，可在 terminal 的 value 中保留显示文本。

| 插入键 | NFC 后的码点路径 | terminal 标记 |
|---|---|---|
| re | r → e | e 节点是完整键 |
| report | 与 re 共享 r → e，再接 p → o → r → t | t 节点是完整键 |
| reporter | 继续共享 report，再接 e → r | 最后一个 r 是完整键 |
| review | 与 re 共享 r → e，再从 v 分支 | 最后一个 w 是完整键 |
| 😀report | 😀 → r → e → p → o → r → t | t 节点是完整键 |
| 先 café，后 cafe 加 U+0301 | 两次写入经 NFC 后都走 café 的同一条路径 | 第二次写入覆盖第一次的 value |

每个节点有一张从码点到子节点的 Map 和一个 terminal（键结束）标记。只有 terminal 为 true 才表示完整键；“存在这段前缀”不等于“前缀本身也是键”。因此 re 可以既是完整键，也有通向 report 和 review 的后续分支。共享路径存一次，但每个前缀节点及子边 Map 都占内存。

下面实现插入、精确查询和有限前缀枚举。枚举从前缀节点开始做 depth-first search（DFS，深度优先搜索）；terminal 先于后代输出，因此前缀本身若也是键会先出现。子边按 Map 的插入顺序访问，所以结果不承诺字典序；limit 限制返回候选数，显式栈按需取一个子边，不会为了遍历先复制整张子边表。

> [!example]- 可运行：码点 Trie
> ~~~javascript
> class TrieNode {
>   constructor() {
>     this.children = new Map();
>     this.terminal = false;
>     this.value = undefined;
>   }
> }
>
> class CodePointTrie {
>   constructor() {
>     this.root = new TrieNode();
>   }
>
>   normalizeKey(key) {
>     if (typeof key !== 'string') throw new TypeError('key must be a string');
>     return key.normalize('NFC');
>   }
>
>   nodeFor(key) {
>     let node = this.root;
>     for (const codePoint of Array.from(this.normalizeKey(key))) {
>       node = node.children.get(codePoint);
>       if (!node) return null;
>     }
>     return node;
>   }
>
>   insert(key, value) {
>     const normalized = this.normalizeKey(key);
>     let node = this.root;
>     for (const codePoint of Array.from(normalized)) {
>       if (!node.children.has(codePoint)) node.children.set(codePoint, new TrieNode());
>       node = node.children.get(codePoint);
>     }
>     node.terminal = true;
>     node.value = value;
>   }
>
>   has(key) {
>     const node = this.nodeFor(key);
>     return node !== null && node.terminal;
>   }
>
>   lookup(key) {
>     const node = this.nodeFor(key);
>     return node !== null && node.terminal
>       ? { found: true, value: node.value }
>       : { found: false };
>   }
>
>   keysWithPrefix(prefix, limit = 20) {
>     if (!Number.isSafeInteger(limit) || limit < 0) {
>       throw new RangeError('limit must be a non-negative safe integer');
>     }
>     const normalizedPrefix = this.normalizeKey(prefix);
>     const start = this.nodeFor(normalizedPrefix);
>     if (start === null || limit === 0) return [];
>
>     const results = [];
>     const path = [];
>     const stack = [{ node: start, entered: false, children: null }];
>     while (stack.length > 0 && results.length < limit) {
>       const frame = stack[stack.length - 1];
>       if (!frame.entered) {
>         frame.entered = true;
>         if (frame.node.terminal) {
>           results.push(normalizedPrefix + path.join(''));
>           if (results.length === limit) break;
>         }
>         frame.children = frame.node.children.entries();
>       }
>
>       const next = frame.children.next();
>       if (next.done) {
>         stack.pop();
>         if (stack.length > 0) path.pop();
>       } else {
>         const [codePoint, child] = next.value;
>         path.push(codePoint);
>         stack.push({ node: child, entered: false, children: null });
>       }
>     }
>     return results;
>   }
> }
>
> const trie = new CodePointTrie();
> trie.insert('re', 'prefix is also a complete key');
> trie.insert('report', 'report label');
> trie.insert('reporter', 'reporter label');
> trie.insert('review', 'review label');
> trie.insert('café', 'precomposed spelling');
> trie.insert('cafe\u0301', 'decomposed spelling replaces the same normalized key');
> trie.insert('😀report', 'emoji-prefixed key');
>
> console.log(trie.has('café'));                  // true
> console.log(trie.lookup('cafe\u0301'));         // { found: true, value: 'decomposed spelling replaces the same normalized key' }
> console.log(trie.keysWithPrefix('re', 3));      // ['re', 'report', 'reporter']
> console.log(trie.keysWithPrefix('rep', 10));    // ['report', 'reporter']
> console.log(trie.keysWithPrefix('unknown', 5)); // []
> console.log(trie.keysWithPrefix('', 2));        // first two keys in trie traversal order
> ~~~

若键有 m 个码点，在 Map 子边查找按平均常数时间估算时，插入和精确查询需 O(m) 时间；更严谨地说，时间是沿 m 条边执行的 Map 操作总成本。令 p 为输入前缀长度；按常见的线性 Unicode 规范化实现估算，前缀规范化、Array.from 转成码点数组和定位节点共需 O(p) 时间，规范化结果字符串与临时码点数组合计 O(p) 空间。设 DFS 实际访问 S 个节点，d 是访问路径的最大深度，L 是返回键的码点总数，r 是实际返回项数：遍历和构造结果的时间按 O(p + S + L) 估算；显式栈帧和码点路径数组各占 O(d) 空间，返回的字符串另占 O(L)，结果数组含 O(r) 个引用。因此不计 Trie 本身的总额外空间为 O(p + d + L + r)。limit 只限制返回条数，不保证访问节点数或字符总数也为 O(limit)。若需要按语言区域排序的建议项，必须另外定义排序规则；本实现的 Map 插入顺序不等于语言排序。哈希表适合完整键的精确查找，不能直接定位整组前缀候选；排序列表可以先二分找到同前缀键的起点再顺序输出；Trie 用更多节点和 Map 结构换取沿前缀直接定位。只有前缀查询足够常见时，这种空间取舍才值得。

> [!info]- 来源
> - JavaScript 字符串的 UTF-16 表示及字符串迭代按码点处理：[ECMAScript 2026 text processing](https://tc39.es/ecma262/2026/multipage/text-processing.html)，String value 与 StringIterator。
> - JavaScript NFC 规范化 API：[ECMAScript 2026, §22.1.3.15 String.prototype.normalize](https://tc39.es/ecma262/2026/multipage/text-processing.html#sec-string.prototype.normalize)；该方法按最新 Unicode Standard 的规范化形式处理输入。
> - 构造器入口：[ECMA-402 2026 §8.2.7 `Intl.NumberFormat`](https://tc39.es/ecma402/2026/#sec-intl.numberformat)、[§8.2.10 `Intl.Segmenter`](https://tc39.es/ecma402/2026/#sec-intl.segmenter)；格式化机制见 [§16 NumberFormat Objects](https://tc39.es/ecma402/2026/#numberformat-objects)，分段机制见 [§19 Segmenter Objects](https://tc39.es/ecma402/2026/#segmenter-objects)。Node.js v26.11.1 只用于复算本例行为，不据此断言运行时采用 UAX #29 rev.49。
> - 字素簇默认边界与适用限制：[Unicode Standard Annex #29, Unicode 18.0.0, Revision 49](https://www.unicode.org/reports/tr29/tr29-49.html)，2026-09-01；以 extended grapheme cluster 作默认分段，允许声明定制。
> - 数字安全整数上限：[ECMAScript 2026 Number.MAX_SAFE_INTEGER](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-number.max_safe_integer)，2⁵³−1。
> - Trie 的前缀路径、完整键终端标记和前缀枚举：[Robert Sedgewick 与 Kevin Wayne, Algorithms, 4th ed., §5.2 “Tries”](https://algs4.cs.princeton.edu/52trie/)，作者实现 [TrieST.java](https://algs4.cs.princeton.edu/code/edu/princeton/cs/algs4/TrieST.java.html) 使用 256 路扩展 ASCII；本页使用 Map 子边与码点，避免把该 ASCII 实现误当成通用 Unicode 代码。
> - 规范等价与 NFC 规范化形式：[Unicode Standard Annex #15, Unicode 18.0.0, Revision 58, §1.1 “Canonical and Compatibility Equivalence” 与 §1.2 “Normalization Forms”](https://www.unicode.org/reports/tr15/tr15-58.html)，2026-08-12。NFC 选择及其对前缀语义的影响按本节契约说明。
> - 子边迭代顺序：[ECMAScript 2026, Keyed Collections](https://tc39.es/ecma262/2026/multipage/keyed-collections.html)，Map iterator 按插入顺序产生条目。
