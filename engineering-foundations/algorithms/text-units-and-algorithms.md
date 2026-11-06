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

> [!info]- 来源
> - JavaScript 字符串的 UTF-16 表示及字符串迭代按码点处理：[ECMAScript 2026 text processing](https://tc39.es/ecma262/2026/multipage/text-processing.html)，String value 与 StringIterator。
> - 构造器入口：[ECMA-402 2026 §8.2.7 `Intl.NumberFormat`](https://tc39.es/ecma402/2026/#sec-intl.numberformat)、[§8.2.10 `Intl.Segmenter`](https://tc39.es/ecma402/2026/#sec-intl.segmenter)；格式化机制见 [§16 NumberFormat Objects](https://tc39.es/ecma402/2026/#numberformat-objects)，分段机制见 [§19 Segmenter Objects](https://tc39.es/ecma402/2026/#segmenter-objects)。Node.js v26.11.1 只用于复算本例行为，不据此断言运行时采用 UAX #29 rev.49。
> - 字素簇默认边界与适用限制：[Unicode Standard Annex #29, Unicode 18.0.0, Revision 49](https://www.unicode.org/reports/tr29/tr29-49.html)，2026-09-01；以 extended grapheme cluster 作默认分段，允许声明定制。
> - 数字安全整数上限：[ECMAScript 2026 Number.MAX_SAFE_INTEGER](https://tc39.es/ecma262/2026/multipage/numbers-and-dates.html#sec-number.max_safe_integer)，2⁵³−1。
