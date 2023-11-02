# SwiftUI Notes

## Declaring constant and variables
```swift
let a = 0 //this is a constant
var b = 1 // this is a variable
a = 2 // report error, constant cannot be re-assigned values
b = 2 // valid
```

## Functions
Certainly! Here's a structured note on Swift functions, drawing comparisons with Java, React (JavaScript/TypeScript), and Python where relevant.

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
- Each parameter has both a name for internal use within the function and an argument label for use when calling the function, which can be omitted with `_`.

```swift
func exampleWithParams(internalName externalLabel: Type, _ noLabel: Type) {
    // function body
}
```

**Argument Labels:**
- Swift uses argument labels to give context to the arguments, making function calls read like sentences.
- This is unique to Swift, as JavaScript/TypeScript, Java, and Python typically do not use argument labels.

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
- This is somewhat akin to passing an object or array in JavaScript/TypeScript or Python, where the changes are reflected outside the function.

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

### Mutating Functions
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

The `mutating` keyword tells the compiler that this method is going to modify the instance it belongs to. Without the `mutating` keyword, you would not be able to compile this code because structs are immutable by default.

## Struct vs Classes
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

- **Value Types**: Structs are value types, which means they are copied when they are passed around in your code, and they do not use reference counting.
- **No Inheritance**: Structs do not support inheritance. They cannot inherit from another struct or class.
- **Memberwise Initializers**: Swift structs automatically receive a memberwise initializer if you do not provide one, which initializes new struct instances with the default values you provide.
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

In Swift, structs are preferred over classes in many cases due to their simplicity and performance characteristics. Use a class when you need to control the identity of the data you're modeling (for example, if you need to compare instances, manage shared state, or use inheritance). Otherwise, default to using a struct.

Keep in mind the following considerations:

- Use a class if you need to control the identity of your object or if your object's lifecycle needs to be managed.
- Use structs for small data values that will be copied rather than shared.
- Structs are preferable when they are going to be passed around a lot in your code, and you want to ensure they remain immutable.

Swift also includes features like protocols and extensions, which can provide some of the functionality of inheritance for structs, allowing you to write very flexible and reusable code without the overhead that can come with classes.

## Image Literal

*Image literal* which is a convenient way to insert images directly into your code. 

### Key Points

- **Usage**: Image literals are used for inserting image references in Swift code without the need for explicit string-based filenames.
- **React Comparison**: This is somewhat similar to using `<Image src={ImportedImage}>` in React, where `ImportedImage` would typically be imported at the top of your file.
- **Array of Image Literals**: In Swift, you can store multiple image literals in an array, which allows for a collection of images to be handled programmatically.

### How to Use Image Literal in Swift

To use an image literal in Xcode:

1. Type `#imageLiteral(` and Xcode will offer to autocomplete this with an image literal. Alternatively, you can start typing the name of your image and Xcode's autocomplete may suggest the image literal for you.
2. A media library picker will be presented, allowing you to select an image from your asset catalog.
3. Once selected, the literal will be inserted into your code, and it will display a small thumbnail of the image.

### Example

```swift
let image: UIImage = #imageLiteral(resourceName: "your_image_name")
```

In the above code, `"your_image_name"` is the name of the image in your asset catalog. At runtime, the `UIImage` object will be created with the specified image.

### Array Example

```swift
let images: [UIImage] = [#imageLiteral(resourceName: "image1"), #imageLiteral(resourceName: "image2"), #imageLiteral(resourceName: "image3")]
```

Here, `images` is an array containing three image literals, which can be iterated over or accessed via their index.

## String Interpolation

**Swift vs. JavaScript**

In Swift programming, when you want to insert the value of a variable or an expression directly into a string, you use the **String Interpolation** method. The syntax for string interpolation in Swift is:
```swift
"\(varName)"
```

The syntax for string interpolation in JavaScript is below, just FYI:
```javascript
`${varName}`
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

- `break` is used to end the execution of a loop, switch, or conditional statement prematurely.
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

