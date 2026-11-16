# 文本算法应按码元、码点还是字素簇处理？

本章用一个合成案例贯穿：报表系统里编号为 42 的报表有一段事件描述，用户可能在其中输入 emoji、组合重音或其他扩展文字，系统要对它计数、截取、比较和做前缀搜索。难点在于，JavaScript 的字符串索引、Unicode 码点和用户看到的“一个字符”不是同一种单位，所以要先定义任务按什么单位计数、比较或切分，再写算法。

三种单位分别是 UTF-16 code unit（UTF-16 编码单元）、Unicode code point（Unicode 码点）和 extended grapheme cluster（扩展字素簇）。一个 UTF-16 编码单元是一个 16 位值；补充平面上的字符（如大多数 emoji）用一对 surrogate（代理）编码，占两个编码单元，但只表示一个码点。组合重音本身是一个独立码点，通常和前面的基字符合成一个扩展字素簇，也就是用户眼中的一个字符。

## 三种长度会怎样不同？

`String.prototype.length` 返回 UTF-16 编码单元数。`Array.from` 按码点迭代字符串：有效的代理对合成一个元素，孤立的代理单独成为一个元素；组合重音这类附加符仍是独立的码点元素。`Intl.Segmenter` 的 grapheme 模式按 locale（语言环境）和运行时实现的分段规则切出字素簇，结果通常接近用户感知的字符。不过这些规则允许定制，某个 Node 运行时的输出不能等同于当前 UAX #29 版本的每条边界规则。

下图把同一个输入 `A😀e\u0301` 按三种单位划分。每个方框是该行的一个单位；方框的横向边界对齐原始 UTF-16 位置，不代表字符在屏幕上的显示宽度。`◌́` 里的虚线圆只为让组合重音看得清，不属于输入。

![A、emoji 与组合重音在编码单元、码点、字素簇三种粒度下的分组](resources/text-string-units.svg)

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

其中 A 占 1 个编码单元、1 个码点；😀 是代理对，占 2 个编码单元、1 个码点；e 加 U+0301 组合重音占 2 个编码单元、2 个码点，但通常合成 1 个字素簇。三种计数都不等于存储大小：若要限制请求的字节数，还需按明确的编码（如 UTF-8）另算字节。

## 返回的索引按什么单位计？

知道了三种长度，下一个问题是：各种 API 返回的位置又按哪种单位计？字符串方法返回的位置通常是 UTF-16 编码单元偏移；先把字符串转成数组，数组下标数的就是数组元素。`Intl.Segmenter` 的分段记录也使用原字符串的编码单元偏移，因此可以直接用 `part.index` 回到原字符串定位。

~~~javascript
const indexedSample = 'A😀e\u0301';
const graphemeSegments = Array.from(
  new Intl.Segmenter('en', { granularity: 'grapheme' }).segment(indexedSample)
);
const graphemes = graphemeSegments.map(({ segment }) => segment);
const finalGrapheme = 'e\u0301';

console.log(indexedSample.length); // 5 UTF-16 code units
console.log(indexedSample.indexOf(finalGrapheme)); // 3 code-unit offset
console.log(Array.from(indexedSample).indexOf('e')); // 2 code-point array index
console.log(graphemeSegments.find(({ segment }) => segment === finalGrapheme).index); // 3 code-unit offset
console.log(graphemes.indexOf(finalGrapheme)); // 2 grapheme-array index
~~~

| 表达式 | 返回值 | 位置单位 |
|---|---:|---|
| `indexedSample.length` | 5 | 编码单元数量，不是索引 |
| `indexedSample.indexOf(finalGrapheme)` | 3 | 原字符串编码单元偏移 |
| `Array.from(indexedSample).indexOf('e')` | 2 | 码点数组下标 |
| Segmenter 记录的 `.index` | 3 | 原字符串编码单元偏移 |
| `graphemes.indexOf(finalGrapheme)` | 2 | 字素簇数组下标 |

所以，码点数组或字素簇数组的下标不能直接传给原字符串的 `slice`、`substring` 等方法，因为这些方法按编码单元解释参数。本例中 `slice(2)` 会从 😀 的低代理 U+DE00 开始截取，`slice(3)` 才从 `e\u0301` 开始。若要在原文中高亮或替换数组里的某个元素，应保留原字符串偏移（例如 Segmenter 的 `.index`），或显式建立数组下标到原偏移的映射。

另一个容易混淆的点是：同一个用户可见字符可能有不同的码点序列，`Array.from` 不会把它们统一。例如预组字符 é（U+00E9）与 e 加组合重音看起来相同，逐码点比较却不同：`'é' === 'e\u0301'` 为 false，经 NFC（Normalization Form C，规范化形式 C）规范化后两者相等。Unicode 把这种关系叫 canonical equivalence（规范等价）。若业务要求按规范等价比较，可在明确的处理边界调用 `normalize('NFC')`；需要保留原始输入时，不要无意改写它的码点序列。NFC/NFD 只处理规范等价；NFKC/NFKD 还会合并部分兼容形式（如全角字母与半角字母），是否适用取决于任务，不能当作显示文本的通用清理。规范化后的偏移只属于规范化副本：例如 `'e\u0301'.length` 是 2，`'é'.length` 是 1，所以要改写原输入时，不能把副本上的偏移直接套回原文。

## 回文和连续重复要比较什么单位？

单位的选择会直接改变算法结论。下面的回文判断用同一套双指针逻辑，只是输入的切分方式不同：`isPalindromeByCodePoint` 按码点从两端向中间比较，会把代理对当作一个元素，但不做规范化；`isPalindromeByGrapheme` 先用 Segmenter 切成字素簇，按用户可见单元比较。

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

const palindromeText = 'e\u0301x\u0301e';
console.log(isPalindromeByCodePoint(palindromeText)); // true
console.log(splitGraphemes(palindromeText));          // ['é', 'x́', 'e']
console.log(isPalindromeByGrapheme(palindromeText));  // false
~~~

同一个输入因单位不同而得出相反结果：码点序列是 `e, U+0301, x, U+0301, e`，镜像两端相等；默认字素簇则是 `e\u0301, x\u0301, e`，首尾不相同。

两个函数都要求输入是字符串，空字符串返回 true；元素之间用精确的字符串相等比较，不做规范化，也不做 case folding（大小写折叠，后文详述）。是否规范化是另一个独立决定：`'éxe\u0301'` 直接按字素簇比较为 false，先作 NFC 变成 `'éxé'` 后再比较则为 true。另外，UAX #29 的默认扩展字素簇是可复现的分段规则，但语言或应用可以对它 tailor（定制）；字素簇数也与编码字节长度无关。

复杂度分析：令 m 为码点数、g 为字素簇数、u 为 UTF-16 编码单元数。码点版本先生成含 m 个码点的数组，再做至多 floor(m/2) 次相等比较，时间和临时数组空间都是 O(m)。字素簇版本的分段耗时由 `Intl.Segmenter` 的实现决定，ECMAScript 规范没有给出渐近界。分段之后，收集 g 个段需要 O(g)；按常见的“逐编码单元比较字符串”成本模型，至多比较 floor(g/2) 对段，参与比较的段文本总长不超过 u，所以分段后的收集与比较是 O(u+g)。数组保存 g 个段引用，段文本的额外存储最多 O(u)（运行时也可能共享底层字符串）。两种实现都不包含规范化成本。

第二个例子是找最长的连续重复字符。下面的 `longestConsecutive` 接受字符串，按码点统计完全相同的连续项；多个段一样长时返回最先出现的那段；空字符串返回空字符串和长度 0。输入 `'😀😀A'` 时结果是 😀、长度 2；若按 UTF-16 下标遍历，每个 emoji 会被拆成两个编码单元，结果就错了。设输入有 m 个码点：`Array.from` 创建 m 个数组项，循环处理每个码点外加一次末尾哨兵，所以总时间 O(m)、辅助空间 O(m)。

以 `AABB` 为例，逐轮追踪 `currentLength` 和 `bestChar`/`bestLength`。每轮开始时，`currentLength` 是以第 `i-1` 项结尾的当前段长度；第 i 项与前一项相同就延长当前段，否则先结算上一段，再从当前字符开始新段。循环多跑一轮到 `i === characters.length`，这个“结束哨兵”强制结算最后一段：

| i | 输入 | 动作 | 当前段 | 最佳段 |
|---:|---|---|---|---|
| 初始 | A | 初始化 | A/1 | A/1 |
| 1 | A | 与前项相同，延长 | A/2 | A/1 |
| 2 | B | 结算 A，再从 B 开始 | B/1 | A/2 |
| 3 | B | 与前项相同，延长 | B/2 | A/2 |
| 4 | 结束哨兵 | 结算 B；长度相同，不覆盖 | — | A/2 |

比较用的是严格大于 `currentLength > bestLength`，所以长度并列时保留先出现的 A。

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

报表描述里常有数字，显示时同样要先说清边界：按什么区域规则显示，输入是数值还是文本。显示数值通常用 `Intl.NumberFormat`，并显式指定 locale，避免依赖用户机器的默认区域。即便如此，格式化结果仍可能随运行时的国际化数据版本变化；若输出要用于协议或稳定快照，不应把本地化显示文本当作机器可解析的格式。下面的手写版本 `formatIntegerThousands` 只接受“可选负号 + ASCII 十进制数字”构成的整数字符串，不接受小数、空格或本地化数字。

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

`Intl.NumberFormat` 按 locale 显示数值，也能接收 BigInt 和表示数值的字符串；手写函数则直接在原始十进制文本中每三位插入逗号。下表用 `9007199254740993`（超过 `Number.MAX_SAFE_INTEGER`，即 2⁵³−1）作对照：只有先调用 `Number(...)` 的最后一行在格式化前就丢失了精度。

| 调用 | 输出 | 保留的信息 |
|---|---|---|
| `formatNumber(1234.5, 'en-US')` | `1,234.5` | en-US 数字显示规则 |
| `formatNumber(1234.5, 'de-DE')` | `1.234,5` | de-DE 数字显示规则 |
| `formatIntegerThousands('9007199254740993')` | `9,007,199,254,740,993` | 原整数字符串的全部数字 |
| `formatNumber('9007199254740993', 'en-US')` | `9,007,199,254,740,993` | 直接传入数字文本，未先转成 Number |
| `formatNumber(9007199254740993n, 'en-US')` | `9,007,199,254,740,993` | BigInt 表示的精确整数 |
| `formatNumber(Number('9007199254740993'), 'en-US')` | `9,007,199,254,740,992` | Number 转换时已舍入的数值 |

这个正则只适合本例限定的 ASCII 整数字符串。普通回溯引擎会在每个候选位置用前瞻重新检查后面的数字，因此不能对任意实现或输入规模声称它是线性时间。若需要明确的单趟线性处理，可以从右向左每三位分组再拼接，n 位输入用 O(n) 时间、生成 O(n) 输出。单纯显示数字时，优先使用 `Intl.NumberFormat`。

大小写转换也要先定边界。下面的 `switchAsciiCase` 接受字符串，只互换 ASCII 的 A–Z 与 a–z，其他码点原样保留。它不是适用于所有语言的大小写转换：Unicode 大小写映射可能依赖 locale，转换前后的长度也可能不同。若输入有 m 个码点、u 个编码单元，该函数逐码点处理一次再拼接输出，时间 O(m+u)，临时映射数组 O(m)，结果字符串 O(u)；ASCII 大小写互换不改变码点数和编码单元数。

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

“不区分大小写”的比较还涉及另一个概念：case folding（大小写折叠）。它把大小写变体映射到同一形式，专为比较设计，和转成小写并不相同。`toLowerCase()` 使用 Unicode 默认小写映射；`toLocaleLowerCase(locale)` 按指定语言环境做小写映射。两者都可能因上下文或语言规则让文本变长或改变，而 ECMAScript 没有提供通用的 `String.prototype.caseFold()`。例如 `'ß'.toLowerCase()` 仍是 `ß`，而 Unicode 18 的完整默认折叠把 U+00DF 映射为 `ss`；`'I'.toLocaleLowerCase('tr')` 则得到土耳其语无点小写 i `ı`。

| 输入与操作 | 输出 | 用途差别 |
|---|---|---|
| `'ß'.toLowerCase()` | `ß` | Unicode 小写映射，不是完整折叠 |
| Unicode 18 完整默认 case fold：U+00DF | U+0073 U+0073（`ss`） | Unicode 默认大小写无关匹配 |
| Unicode 18 完整默认 case fold：U+FB03 `ﬃ` | `ffi` | 个别兼容字符有专门的折叠映射 |
| Unicode 18 完整默认 case fold：U+017F `ſ` | `s` | 折叠映射也可能合并特殊字母 |
| `'I'.toLocaleLowerCase('tr')` | U+0131（`ı`） | 语言环境指定的大小写转换 |
| `'İ'.toLowerCase()` | U+0069 U+0307（`i` 加组合点） | 小写映射可能扩展为多个码点 |

若任务要求不区分大小写，先定义使用默认完整折叠还是特定语言规则，并对存入的键和查询文本走同一条处理链；如果还要求规范等价，再规定规范化与折叠的先后顺序和 Unicode 版本。NFC 本身不折叠大小写，也不去掉重音；case folding 也不是通用的兼容规范化或去重音规则，只是个别兼容字符有自己的折叠映射（如表中 `ﬃ` → `ffi`）。折叠的输出不保证保持原来的规范化形式，契约要求 NFC 输出时，折叠后还要再规范化一次。通用文本匹配应使用明确版本的 Unicode 数据或库，不要把 ASCII 示例函数或普通小写转换当成跨语言折叠。

## Trie 怎样共享前缀并限制候选输出？

回到报表 42 的描述搜索：用户在输入框里键入前缀，系统要列出以该前缀开头的标签。Trie（前缀树）把每个键拆成一串单位，有相同前缀的键沿同一条路径向下走；本例沿用本章的码点单位，每条边是一个 Unicode 码点。`Array.from` 会把有效代理对合成一个码点，所以 😀 是一条边；组合重音若没有规范化，则是另一条独立的码点边，与视觉上的一个字素簇不对应。

本例的匹配契约选用 NFC：写入的键和查询前缀各自先作 NFC，Trie 再判断规范化后的查询码点序列是不是某个规范化后键的前缀。这样，预组字符 café 与 cafe 加 U+0301 被当作同一个键，枚举出的键也是规范化后的形式。这个选择改变了“原始字符串前缀”的含义：原键 `'cafe\u0301'` 确实以原始字符串 `'cafe'` 开头，但它 NFC 后是 `'café'`，于是用前缀 `'cafe'` 查询 Trie 得到 `[]`。NFC 也不做去重音或大小写折叠，`Report` 不匹配 `report`；若产品要求不区分大小写、去重音或处理兼容字符，必须另外定义匹配规则。

每个 Trie 节点有一张“码点 → 子节点”的 Map 和一个 terminal（键结束）标记，terminal 为 true 表示从根到这里的路径恰好是一个完整键。如果需要展示用户原来输入的文本，可以把它存在 terminal 节点的 value 里。下表展示插入几组键后的路径：

| 插入键 | NFC 后的码点路径 | terminal 标记 |
|---|---|---|
| re | r → e | e 节点是完整键 |
| report | 与 re 共享 r → e，再接 p → o → r → t | t 节点是完整键 |
| reporter | 继续共享 report，再接 e → r | 最后一个 r 是完整键 |
| review | 与 re 共享 r → e，再从 v 分支 | 最后一个 w 是完整键 |
| 😀report | 😀 → r → e → p → o → r → t | t 节点是完整键 |
| 先 café，后 cafe 加 U+0301 | 两次写入经 NFC 后都走 café 的同一条路径 | 第二次写入覆盖第一次的 value |

只有 terminal 为 true 才表示完整键；“Trie 里存在这段前缀”不等于“这段前缀本身也是键”。所以 re 既可以是完整键，又有通向 report 和 review 的后续分支。共享的路径只存一次，但每个节点及其子边 Map 都要占内存。

下面实现插入、精确查询和限量的前缀枚举。枚举从前缀对应的节点开始做 depth-first search（DFS，深度优先搜索），先输出当前节点再访问后代，因此前缀本身若也是键会最先出现。子边按 Map 的插入顺序访问，结果不保证字典序。`limit` 限制返回的候选数；显式栈每次只从迭代器取下一条子边，不会为了遍历先复制整张子边表。按本例的插入顺序，`keysWithPrefix('re', 3)` 先输出完整键 `re`，沿 p 分支输出 `report`、`reporter`，达到 3 后停止，因此尚未访问 v 分支中的 `review`。

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
> console.log('cafe\u0301'.startsWith('cafe'));    // true: raw-string prefix
> console.log(trie.keysWithPrefix('cafe'));        // []: separately NFC-normalized codepoint prefix
> console.log(trie.keysWithPrefix('re', 3));      // ['re', 'report', 'reporter']
> console.log(trie.keysWithPrefix('rep', 10));    // ['report', 'reporter']
> console.log(trie.keysWithPrefix('unknown', 5)); // []
> console.log(trie.keysWithPrefix('', 2));        // first two keys in trie traversal order
> ~~~

复杂度分析：设 NFC 后的键含 m 个码点。插入和精确查询先规范化一次，再把文本转成码点，沿 m 条边做 Map 操作；按哈希表“平均 O(1) 访问一条子边”的常见模型，路径查找或更新的期望时间是 O(m)。ECMAScript 对 Map 只要求平均次线性访问，严格的 O(1) 是常见实现的假设，而不是规范保证。规范化成本单独记为 `T_NFC(输入)`，不默认算作 O(m)，因为 ECMAScript 只规定 `normalize` 的结果，不保证它在线性时间内完成。规范化字符串和临时码点数组各占 O(m) 空间；插入最多新建 m 个节点和边，已存在的路径会复用。

`keysWithPrefix` 先用 `normalizeKey` 规范化 `prefix`，再交给 `nodeFor`，而 `nodeFor` 内部又调用一次 `normalizeKey`，所以这段代码确实执行两次 NFC，只是第二次的输入已经是 NFC。设规范化后的前缀有 p 个码点、u 个编码单元；DFS 实际访问 S 个节点，最大后缀深度为 d，返回的 r 个键字符串共 U 个编码单元。不计两次规范化，沿前缀走路径、DFS 和拼接结果字符串的期望时间是 O(p + S + U)；完整时间再加 `T_NFC(原前缀)` 与 `T_NFC(规范化后前缀)`。不计 Trie 本身，额外空间包括：规范化字符串 O(u)、临时码点数组 O(p)、DFS 栈和码点路径 O(d)、返回字符串 O(U)、结果数组 O(r) 个引用，合计 O(u+p+d+U+r)。`limit` 只限制返回条数，不保证访问的节点数或输出字符总量是 O(limit)：前缀下可能有很长的非 terminal 链。

最后看取舍。哈希表适合完整键的精确查找，但无法直接定位一整组前缀候选。另一种做法是把键按与前缀匹配一致的字典序排序，这时匹配某前缀的键在数组中连续，可以先二分查找起点再顺序输出。Trie 则用更多节点和 Map 换取沿前缀直接定位，只有前缀查询足够频繁时，这份额外空间才值得。若候选需要按语言习惯排序，还要另外定义排序规则；本实现的 Map 插入顺序不等于语言排序。

> [!info]- 来源
> - JavaScript String 的 `length` 是 UTF-16 编码单元数、字符串迭代按码点处理、`indexOf`/`slice` 使用字符串偏移：[ECMAScript 2026, §22.1.3.9、§22.1.3.22、§22.1.3.36、§22.1.4.1](https://tc39.es/ecma262/2026/multipage/text-processing.html)。
> - Segmenter 的迭代位置是原字符串编码单元下标，分段记录 `.index` 返回 `startIndex`：[ECMA-402 2026, §§19.6–19.7](https://tc39.es/ecma402/2026/#segmenter-objects)，特别是 §19.7.1 `CreateSegmentDataObject`。
> - NFC 规范化 API：[ECMAScript 2026, §22.1.3.15 `String.prototype.normalize`](https://tc39.es/ecma262/2026/multipage/text-processing.html#sec-string.prototype.normalize)；该方法按最新 Unicode Standard 的规范化形式处理输入。规范等价、NFC/NFD 与 NFKC/NFKD 的区别：[UAX #15, Unicode 18.0.0, Revision 58, §§1.1–1.2](https://www.unicode.org/reports/tr15/tr15-58.html)，2026-08-12。
> - `toLowerCase` 的 Unicode 默认大小写映射及可能扩展码点数：[ECMAScript 2026, §22.1.3.28](https://tc39.es/ecma262/2026/multipage/text-processing.html#sec-string.prototype.tolowercase)；`toLocaleLowerCase` 语言环境映射、可扩展且上下文相关：[ECMA-402 2026, §20.1.2](https://tc39.es/ecma402/2026/#sec-string.prototype.tolocalelowercase)。Unicode 18 完整默认折叠按 UCD `CaseFolding.txt` 的 C+F 映射定义，U+00DF→U+0073 U+0073、U+FB03→U+0066 U+0066 U+0069、U+017F→U+0073；T 状态仅供 Turkic 选择，且该文件提醒 case folding 不保留 normalization form：[CaseFolding-18.0.0.txt](https://www.unicode.org/Public/18.0.0/ucd/CaseFolding.txt)，[UAX #44, Unicode 18.0.0, Revision 38](https://www.unicode.org/reports/tr44/tr44-38.html)。
> - Intl 构造器和本地化数字机制：[ECMA-402 2026 §8.2.7 `Intl.NumberFormat`](https://tc39.es/ecma402/2026/#sec-intl.numberformat)、[§8.2.10 `Intl.Segmenter`](https://tc39.es/ecma402/2026/#sec-intl.segmenter)、[§16 NumberFormat Objects](https://tc39.es/ecma402/2026/#numberformat-objects)；§16.5.16 `ToIntlMathematicalValue` 说明本例的数值字符串与 BigInt 如何跳过先转换为 Number 的步骤。字素簇默认边界与适用限制：[UAX #29, Unicode 18.0.0, Revision 49](https://www.unicode.org/reports/tr29/tr29-49.html)，2026-09-01；以 extended grapheme cluster 作默认分段，允许声明定制。
> - 运行复算：Node.js v26.13.0，ICU 79.1，Unicode 18.0，CLDR 49.0。只记录该运行时的输出，不据此断言其它运行时使用相同国际化数据或逐条采用 UAX #29 rev.49。
> - 数字安全整数上限：[ECMAScript 2026 Number.MAX_SAFE_INTEGER](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-number.max_safe_integer)，2⁵³−1。
> - Trie 的前缀路径、完整键终端标记和前缀枚举：[Robert Sedgewick 与 Kevin Wayne, Algorithms, 4th ed., §5.2 “Tries”](https://algs4.cs.princeton.edu/52trie/)，作者实现 [TrieST.java](https://algs4.cs.princeton.edu/code/edu/princeton/cs/algs4/TrieST.java.html) 使用 256 路扩展 ASCII；本页使用 Map 子边与码点，避免把该 ASCII 实现误当成通用 Unicode 代码。
> - Map 的平均访问时间要求和迭代顺序：[ECMAScript 2026, Keyed Collections, §24.1 Map Objects](https://tc39.es/ecma262/2026/multipage/keyed-collections.html#sec-map-objects)，实现须平均次线性；Map iterator 按插入顺序产生条目。本页 O(m) Trie 路径步数采用常见哈希 Map 的平均 O(1) 子边访问模型，非规范保证。
