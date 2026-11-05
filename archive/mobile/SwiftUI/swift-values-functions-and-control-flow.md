# How do Swift values, functions, and control flow behave? / Swift 值、函数与控制流如何工作？

Swift `struct` values have value semantics while class instances carry reference identity. Functions use explicit argument labels and in-out parameters; `mutating` marks changes to a value-type instance. Ranges, loops, and string interpolation express common control flow without changing those ownership rules. / Swift `struct` 采用值语义，class 实例具有引用身份。函数使用显式参数标签与 in-out 参数；`mutating` 标记对值类型实例的修改。范围、循环和字符串插值表达常见控制流，但不改变所有权规则。

## Constants and variables / 常量与变量

```swift
let a = 0 //this is a constant
var b = 1 // this is a variable
a = 2 // report error, constant cannot be re-assigned values
b = 2 // valid
```

## Functions / 函数

### Swift Functions Overview

**Definition and Syntax:**

- A function in Swift is defined using the `func` keyword, similar to how you'd use `function` or `def` in JavaScript/TypeScript or Python respectively.
- Function names follow the camelCase convention, as they do in JavaScript and Java.

```swift
func functionName(parameter1: Type, parameter2: Type) -> ReturnType {
    // function body
}
```

**Parameters:**

- Parameters are strongly typed, just like in Java and TypeScript.
- A parameter can have an internal name and a distinct call-site argument label; `_` omits the external label.

```swift
func exampleWithParams(argumentLabel parameterName: Type, _ noLabel: Type) {
    // function body
}
```

**Argument Labels:**

- The external/call-site argument label comes first; the internal parameter name used in the function body follows it. Swift uses labels to give context to arguments, making calls read like sentences.
- Argument labels are part of Swift call syntax; other languages provide different forms of named arguments.

**Omitting Argument Labels:**

- An underscore `_` is used to omit the argument label, making the syntax cleaner if the context is clear without the label.

```swift
func greet(_ person: String, on day: String) { /* ... */ }
greet("John", on: "Friday")
```

**Default Parameter Values:**

- Functions can have parameters with default values, which is a feature also available in JavaScript/TypeScript and Python, but not in Java.
- If a parameter has a default value, it can be omitted when calling the function.

```swift
func greet(_ person: String = "Guest", on day: String = "Day") { /* ... */ }
greet() // Uses both default values
greet("John") // Uses default for `day`
```

**Return Types:**

- The return type of a function is specified after the arrow `->`, similar to TypeScript's type annotation for function returns.
- If a function does not return a value, the return type is omitted, which is equivalent to a `void` return type in Java or TypeScript.

```swift
func add(a: Int, b: Int) -> Int {
    return a + b
}
```

**No Return Keyword Needed for Single Expressions:**

- If the body of the function is a single expression, Swift allows you to omit the `return` keyword, similar to arrow functions in JavaScript.

```swift
func multiply(a: Int, b: Int) -> Int { a * b }
```

**Variadic Parameters:**

- Swift allows for variadic parameters, which take zero or more values of a specified type.
- You can use variadic parameters in Swift similarly to the way you would use them in JavaScript/TypeScript with rest parameters, or in Python with `*args`.

```swift
func sum(_ numbers: Int...) -> Int {
    return numbers.reduce(0, +)
}
```

**In-Out Parameters:**

- Swift functions can also have in-out parameters, which allows them to modify the values of passed-in variables.
- An `inout` argument must be a variable and is written with `&` at the call site. Swift describes it as a value copied in, modified by the function, and copied back out; it is not an analogy for mutating a reference-type object.

```swift
func swapTwoInts(_ a: inout Int, _ b: inout Int) {
    let temporaryA = a
    a = b
    b = temporaryA
}
```

**Function Types:**

- Every function has a type, made up of the types of its parameters and its return type.
- This is like the function signatures in TypeScript, where you can assign a function to a variable of a function type.

```swift
var mathFunction: (Int, Int) -> Int = add
mathFunction(2, 3) // returns 5
```

**Nested Functions:**

- Functions can be nested within other functions, and the nested function has access to variables that were declared in the outer function.
- This concept is similar to closures in JavaScript and Python.

```swift
func chooseStepFunction(backward: Bool) -> (Int) -> Int {
    func stepForward(input: Int) -> Int { return input + 1 }
    func stepBackward(input: Int) -> Int { return input - 1 }
    return backward ? stepBackward : stepForward
}
```

Swift functions are first-class types, meaning they can be passed as values to other functions, returned from functions, and assigned to variables, just as you can in JavaScript/TypeScript and Python. They offer flexibility and readability, especially with features like argument labels and default parameter values.

### Non-Mutating Functions

Non-mutating functions do not modify the state of the instance on which they're called. For example, if you have a function within a struct that performs an action and returns a result without altering the properties of the struct, it is considered non-mutating.

```swift
struct Calculator {
    var total: Int

    func addTwoNumbers(a: Int, b: Int) -> Int {
        return a + b
    }
}
```

In this example, `addTwoNumbers` does not change the value of any properties of `Calculator`. It simply takes two numbers, adds them, and returns the result.

### Mutating methods / 可变方法

Mutating functions are explicitly marked with the `mutating` keyword, which allows them to modify the properties of the instance on which they're called. This is necessary because, by default, the instance methods of value types cannot modify the properties of their instance.

```swift
struct Point {
    var x: Int
    var y: Int

    mutating func moveBy(x deltaX: Int, y deltaY: Int) {
        x += deltaX
        y += deltaY
    }
}
```

In the `Point` example, `moveBy` is a mutating method because it changes the properties `x` and `y` of the struct. When you have an instance of `Point` and you call `moveBy`, you are changing the instance's state.

You would use it like this:

```swift
var somePoint = Point(x: 1, y: 1)
somePoint.moveBy(x: 2, y: 3) // somePoint is now (3, 4)
```

For a value type, `mutating` marks an instance method that changes `self` or one of its stored properties. Without the keyword, this method cannot mutate the value.

## Structures and classes / 结构体与类

In Swift, both classes and structs are building blocks of your code. They allow you to create complex data types by combining properties and methods. Since you're familiar with Java, you'll recognize many OOP principles in Swift classes, but there are key differences and unique features in Swift, particularly when it comes to structs.

### Classes

Classes in Swift are similar to classes in Java and other object-oriented languages. Here are some key points:

- **Reference Types**: Classes are reference types, meaning that when you assign a class instance to a variable or constant, or pass it to a function, you're actually passing a reference to that instance, not a copy.
- **Inheritance**: Swift classes support single inheritance, meaning a class can inherit from another class, gaining its properties and methods.
- **Reference Counting**: Swift uses automatic reference counting (ARC) for memory management of class instances.
- **Type Casting**: Instances of Swift classes can be checked at runtime to see if they are instances of a particular subclass.
- **Deinitializers**: Classes can have deinitializers with the `deinit` keyword, which are called just before an instance of the class is deallocated.
- **Reference Equality**: You can check for reference equality (whether two variables point to the same instance) using the identity operators `===` and `!==`.

```swift
class Animal {
    var name: String

    init(name: String) {
        self.name = name
    }

    func makeSound() {
        print("Some generic sound")
    }
}

// Inheritance
class Dog: Animal {
    override func makeSound() {
        print("Woof")
    }
}

let dog = Dog(name: "Buddy")
dog.makeSound() // Prints "Woof"
```

### Structs

Structs in Swift are quite different from what you might expect if you're coming from a Java background:

- **Value Types**: Structs have value semantics: assignment or argument passing behaves as an independent value. The standard library can use copy-on-write storage, so the semantic copy does not mean every value is physically copied immediately.
- **No Inheritance**: Structs do not support inheritance. They cannot inherit from another struct or class.
- **Memberwise Initializers**: A struct receives a synthesized memberwise initializer when it defines no custom initializer in its declaration. A custom initializer can change which synthesized initializers are available.
- **Mutability Control**: If an instance of a struct is constant (`let`), all of its properties are also constant, regardless of how they were declared. Properties of a struct instance can only be changed if the instance itself is variable (`var`).

```swift
struct Point {
    var x: Int
    var y: Int
}

let p1 = Point(x: 10, y: 20)
var p2 = p1 // p2 is now a copy of p1
p2.x = 30 // This does not affect p1.x

print(p1.x) // Prints "10"
print(p2.x) // Prints "30"
```

### Choosing Between Classes and Structs

Swift documentation recommends considering a struct by default when its value semantics fit the model. Use a class when shared identity, inheritance, or reference semantics are part of the design; choose based on behavior rather than a blanket performance rule.

Keep in mind the following considerations:

- Use a class when several parts of a program must observe the same instance identity or a class hierarchy is required.
- Use a struct for independent values; declare an instance with `let` when its stored properties should not be mutated.

Swift also includes features like protocols and extensions, which can provide some of the functionality of inheritance for structs, allowing you to write very flexible and reusable code without the overhead that can come with classes.

## String Interpolation

**Swift vs. JavaScript**

In Swift programming, when you want to insert the value of a variable or an expression directly into a string, you use the **String Interpolation** method. The syntax for string interpolation in Swift is:

```swift
"\(varName)"
```

The syntax for string interpolation in JavaScript is below, just FYI:

```javascript
`${varName}`;
```

**Summary:**

- In **Swift**: Use `"\(varName)"` for string interpolation.
- In **JavaScript**: Use `` `${varName}` `` for the same effect.

## Range

```swift
0...5 // means 0, 1, 2, 3, 4, 5, it is inclusive range
0..<5 // means 0, 1, 2, 3, 4, the last element is excluded
```

## Loops

### For-In Loop

The `for-in` loop is used to iterate over a sequence, such as ranges, collections, or strings.

```swift
// Iterate over a range of numbers
for index in 1...5 {
    print("Value of index is \(index)")
}

// Iterate over an array
let names = ["Anna", "Alex", "Brian", "Jack"]
for name in names {
    print("Hello, \(name)!")
}

// Iterate over a dictionary
let numberOfLegs = ["spider": 8, "ant": 6, "cat": 4]
for (animalName, legCount) in numberOfLegs {
    print("\(animalName)s have \(legCount) legs")
}

// Iterate over characters of a string
for character in "Hello" {
    print(character)
}

// Using where clause to filter out
for number in 1...30 where number % 3 == 0 {
    print(number)
}
```

### While Loop

The `while` loop starts by evaluating a condition. If the condition is `true`, the statement or statements inside the loop will execute. After each execution, the condition is evaluated again.

```swift
var counter = 5
while counter > 0 {
    print("Counter is \(counter)")
    counter -= 1
}
```

### Repeat-While Loop

The `repeat-while` loop, similar to a `do-while` loop in other languages, executes the code block first, then evaluates the condition. It ensures that the loop body is executed at least once.

```swift
var countDown = 5
repeat {
    print("Countdown: \(countDown)")
    countDown -= 1
} while countDown > 0
```

### Control Transfer Statements

Swift also provides control transfer statements that change the order in which your code is executed, by transferring control from one piece of code to another. Here are a few:

- `break` ends the current loop or switch early.
- `continue` is used within a loop to stop the current iteration and start the next iteration from the beginning.

```swift
// Using 'continue' to skip an iteration
for i in 1...10 {
    if i % 2 == 0 {
        continue
    }
    print("Odd: \(i)")
}

// Using 'break' to exit a loop
for i in 1...10 {
    if i > 5 {
        break
    }
    print("Number: \(i)")
}
```

## Sources / 参考资料

- Swift Language Guide: [functions](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/functions/), [structures and classes](https://docs.swift.org/swift-book/LanguageGuide/ClassesAndStructures.html), and [initialization](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/initialization/). The in-out parameter description follows Swift's [declaration reference](https://docs.swift.org/latest/documentation/the-swift-programming-language/declarations/); leading-dot shorthand is specified as an [implicit member expression](https://docs.swift.org/swift-book/ReferenceManual/Expressions.html#implicit-member-expression).
- Apple SwiftUI: [State](https://developer.apple.com/documentation/swiftui/state), [Binding](https://developer.apple.com/documentation/swiftui/binding), [StateObject](https://developer.apple.com/documentation/swiftui/stateobject), [ObservedObject](https://developer.apple.com/documentation/swiftui/observedobject), and [EnvironmentObject](https://developer.apple.com/documentation/swiftui/environmentobject). The newer Observation availability and environment pattern are scoped in Apple's [migration guide](https://developer.apple.com/documentation/swiftui/migrating-from-the-observable-object-protocol-to-the-observable-macro) and [model-data guide](https://developer.apple.com/documentation/swiftui/managing-model-data-in-your-app).
- Apple Developer Documentation: [SwiftUI images](https://developer.apple.com/documentation/swiftui/image), [adding images to an Xcode project](https://developer.apple.com/documentation/xcode/adding-images-to-your-xcode-project), [custom fonts](https://developer.apple.com/documentation/swiftui/applying-custom-fonts-to-text), [managing app information property-list values](https://developer.apple.com/documentation/bundleresources/managing-your-app-s-information-property-list), [foregroundColor deprecation](https://developer.apple.com/documentation/swiftui/view/foregroundcolor%28_%3A%29), [safe-area expansion](https://developer.apple.com/documentation/swiftui/view/ignoressafearea%28_%3Aedges%3A%29), and [Xcode previews](https://developer.apple.com/documentation/xcode/adding-previews-to-your-interface-files).
- `#imageLiteral` maps to UIKit's documented [`UIImage(imageLiteralResourceName:)`](https://developer.apple.com/documentation/uikit/uiimage/init%28imageliteralresourcename%3A%29); use SwiftUI `Image` for SwiftUI view hierarchies. Platform/API availability checked 2026-10-15.
