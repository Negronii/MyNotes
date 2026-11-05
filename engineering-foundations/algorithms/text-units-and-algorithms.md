# Which units should a text algorithm count and compare? / 文本算法应按什么单位计数和比较？

Choose the unit from the behavior you need. Code units support storage indexing, code points represent Unicode values, and grapheme clusters better match many user-perceived characters. Formatting, comparison, and counting should use the same explicit assumptions. / 按任务选择单位。编码单元适合存储索引，码点表示 Unicode 值，字素簇更接近许多用户感知的字符。格式化、比较和计数都应明确所用假设。

## String algorithms

The examples iterate Unicode code points with `Array.from`; that keeps surrogate pairs together. A user-perceived character can contain multiple code points, so grapheme-aware text operations need segmentation and may also need normalization.

### Palindrome check

~~~javascript
function isPalindrome(value) {
  const characters = Array.from(String(value));
  for (let left = 0, right = characters.length - 1; left < right; left++, right--) {
    if (characters[left] !== characters[right]) return false;
  }
  return true;
}
~~~

### Longest consecutive character

Returns the first longest run. Empty input returns an empty character and length zero.

~~~javascript
function longestConsecutive(value) {
  const characters = Array.from(value);
  if (characters.length === 0) return { char: '', len: 0 };

  let bestChar = characters[0];
  let bestLength = 1;
  let currentLength = 1;
  for (let i = 1; i <= characters.length; i++) {
    if (i < characters.length && characters[i] === characters[i - 1]) {
      currentLength++;
    } else {
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

### Number formatting (thousand separators)

For display, use locale-aware formatting and specify a locale when output must be stable across machines. The manual version below accepts only strings containing an optional minus sign and decimal digits; use locale-aware formatting for numeric values and localized output.

~~~javascript
function formatNumber(value, locale = 'en-US') {
  return new Intl.NumberFormat(locale).format(value);
}

function formatIntegerThousands(text) {
  if (typeof text !== 'string' || !/^-?\d+$/.test(text)) throw new TypeError('expected an integer string');
  const sign = text.startsWith('-') ? '-' : '';
  const digits = sign ? text.slice(1) : text;
  return sign + digits.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}
~~~

### Switch ASCII letter case

This example changes only the English ASCII letters A-Z and a-z; other code points are preserved.

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

---

[Back to the main question / 返回主问题](algorithms-and-complexity.md).
