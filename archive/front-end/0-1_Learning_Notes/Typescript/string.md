# String / 字符串

**Core idea / 核心概念：** JavaScript strings are sequences of UTF-16 code units; `.length` counts code units, not user-perceived characters. / JavaScript 字符串由 UTF-16 代码单元组成；`.length` 统计代码单元，不等于用户感知的字符数。 See [ECMAScript text processing](https://tc39.es/ecma262/2025/multipage/text-processing.html).

### 1. `length`
- **Description**: Returns the number of UTF-16 code units in the string.
- **Return Type**: `number`
- **Example**:
  ```javascript
  let str = "Hello";
  console.log(str.length); // Output: 5
  ```

### 2. `toString()`
- **Description**: Returns the string representation.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let strObj = new String("Hello");
  console.log(strObj.toString()); // Output: "Hello"
  ```

### 3. `charAt(pos: number)`
- **Description**: Returns the one-code-unit string at the specified index, or `""` when the index is out of range.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "Hello";
  console.log(str.charAt(1)); // Output: "e"
  ```

### 4. `charCodeAt(index: number)`
- **Description**: Returns the UTF-16 code-unit value at the specified index, or `NaN` when the index is out of range.
- **Return Type**: `number`
- **Example**:
  ```javascript
  let str = "Hello";
  console.log(str.charCodeAt(1)); // Output: 101 (Unicode for 'e')
  ```

### 5. `concat(...strings: string[])`
- **Description**: Concatenates two or more strings and returns a new string.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str1 = "Hello";
  let str2 = " World";
  console.log(str1.concat(str2)); // Output: "Hello World"
  ```

### 6. `indexOf(searchString: string, position?: number)`
- **Description**: Returns the position of the first occurrence of a specified string.
- **Return Type**: `number`
- **Example**:
  ```javascript
  let str = "Hello World";
  console.log(str.indexOf("World")); // Output: 6
  ```

### 7. `lastIndexOf(searchString: string, position?: number)`
- **Description**: Returns the last occurrence of a specified string, searching backwards.
- **Return Type**: `number`
- **Example**:
  ```javascript
  let str = "Hello World, World";
  console.log(str.lastIndexOf("World")); // Output: 13
  ```

### 8. `localeCompare(that: string)`
- **Description**: Compares two strings in the current locale.
- **Return Type**: `number`
- **Example**:
  ```javascript
  let str1 = "a";
  let str2 = "b";
  const comparison = str1.localeCompare(str2);
  console.log(comparison < 0); // true when str1 sorts before str2 in the active locale
  ```

### 9. `match(regexp: string | RegExp)`
- **Description**: Finds matches of a regular expression in a string.
- **Return Type**: `RegExpMatchArray | null`
- **Example**:
  ```javascript
  let str = "Hello World!";
  console.log(str.match(/\bW\w+/)); // Output: ["World"]
  ```

### 10. `replace(searchValue: string | RegExp, replaceValue: string)`
- **Description**: Replaces text in a string, using a regular expression or search string.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "Hello World!";
  console.log(str.replace("World", "Everyone")); // Output: "Hello Everyone!"
  ```

### 11. `search(regexp: string | RegExp)`
- **Description**: Executes a search for a match in a string.
- **Return Type**: `number`
- **Example**:
  ```javascript
  let str = "Hello World!";
  console.log(str.search(/\bW\w+/)); // Output: 6
  ```

### 12. `slice(start?: number, end?: number)`
- **Description**: Extracts a section of a string and returns a new string.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "Hello World!";
  console.log(str.slice(6, 11)); // Output: "World"
  ```

### 13. `split(separator: string | RegExp, limit?: number)`
- **Description**: Splits a string into an array of substrings.
- **Return Type**: `string[]`
- **Example**:
  ```javascript
  let str = "Hello World!";
  console.log(str.split(" ")); // Output: ["Hello", "World!"]
  ```

### 14. `substr(start: number, length?: number)`
- **Description**: Legacy Annex B method; prefer `slice()` for new code. Returns up to `length` code units beginning at `start`.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "Hello World!";
  console.log(str.substr(1, 4)); // Output: "ello"
  ```

### 15. `substring(start: number, end?: number)`
- **Description**: Extracts characters from a string between two specified indices.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "Hello World!";
  console.log(str.substring(1, 5)); // Output: "ello"
  ```

### 16. `toLowerCase()`
- **Description**: Converts a string to lowercase letters.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "HELLO WORLD";
  console.log(str.toLowerCase()); // Output: "hello world"
  ```

### 17. `toLocaleLowerCase(locales?: string | string[])`
- **Description**: Converts a string to lowercase using the supplied locale, or the host default when omitted.
- **Return Type**: `string`
- **Example**:
  ```javascript
  console.log("I".toLocaleLowerCase('tr')); // Output: "ı"
  ```

### 18. `toUpperCase()`
- **Description**: Converts a string to uppercase letters.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "hello world";
  console.log(str.toUpperCase()); // Output: "HELLO WORLD"
  ```

### 19. `toLocaleUpperCase(locales?: string | string[])`
- **Description**: Converts a string to uppercase using the supplied locale, or the host default when omitted.
- **Return Type**: `string`
- **Example**:
  ```javascript
  console.log("i".toLocaleUpperCase('tr')); // Output: "İ"
  ```

### 20. `trim()`
- **Description**: Removes whitespace from both ends of a string.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "  Hello World!  ";
  console.log(str.trim()); // Output: "Hello World!"
  ```

### 21. `valueOf()`
- **Description**: Returns the primitive value of a String object.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let strObj = new String("Hello World");
  console.log(strObj.valueOf()); // Output: "Hello World"
  ```

### String Constructor
- **Description**: Allows creating a String object or converting a value to a string.
- **Usage**:
  ```javascript
  let strObj = new String("Hello");
  let str = String(123);
  ```

### `String.fromCharCode(...codes: number[])`
- **Description**: Converts UTF-16 code-unit values into a string. Use `String.fromCodePoint()` for Unicode code points above `0xFFFF`.
- **Example**:
  ```javascript
  console.log(String.fromCharCode(72, 101, 108, 108, 111)); // Output: "Hello"
  ```

## Traverse String

Indexing and `charAt()` use code units and can split surrogate pairs. `for...of` yields code points, but grapheme clusters (“user-perceived characters”) can span multiple code points ([Unicode Standard Annex #29](https://www.unicode.org/reports/tr29/)).

```javascript
const face = "😀";
console.log(face.length); // 2 UTF-16 code units
console.log([...face]);  // ["😀"]: one code point
console.log(String.fromCodePoint(0x1F600)); // "😀"
```
```ts
const str = "Hello"

let result: string[] = [];
for (let i = 0; i < str.length; i++) {
    let char = str.charAt(i);
    result.push(char);
}
// ["H", "e", "l", "l", "o"] 
console.log(result);	
```

```ts
const s = "Hello"
let result: string[] = [];
for (let char of s) {
    result.push(char);
}
// ["H", "e", "l", "l", "o"] 
console.log(result);	
```
