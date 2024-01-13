# String

### 1. `length`
- **Description**: Get the length of the String object.
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
- **Description**: Returns the character at the specified position.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "Hello";
  console.log(str.charAt(1)); // Output: "e"
  ```

### 4. `charCodeAt(index: number)`
- **Description**: Returns the Unicode of the character at the specified index. NaN if no character at the index.
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
  console.log(str1.localeCompare(str2)); // Output: -1
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
- **Description**: Returns the characters in a string

beginning at the specified location through the specified number of characters.
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
- **Description**: Converts a string to lowercase, considering the host's current locale.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "HELLO WORLD";
  console.log(str.toLocaleLowerCase('tr')); // Output: "hello world" (with Turkish locale)
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
- **Description**: Converts a string to uppercase, considering the host's current locale.
- **Return Type**: `string`
- **Example**:
  ```javascript
  let str = "hello world";
  console.log(str.toLocaleUpperCase('tr')); // Output: "HELLO WORLD" (with Turkish locale)
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
- **Description**: Converts Unicode values into characters.
- **Example**:
  ```javascript
  console.log(String.fromCharCode(72, 101, 108, 108, 111)); // Output: "Hello"
  ```

## Traverse String
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