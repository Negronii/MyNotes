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

_Image literal_ which is a convenient way to insert images directly into your code.

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

## Xcode Interface Builder Tips

### Using the '+' Button for Attributes and Components

- The '+' button located in the top-right corner of the Xcode interface is a versatile tool.
- It allows you to add new components to your storyboard or Swift UI canvas.
- You can also add various attributes to your existing components through this menu.

### Embedding Components in Stack Views

- Right-click on any UI component within the Interface Builder.
- Choose the option to 'Embed in' from the context menu.
- You can select between VStack (Vertical Stack), HStack (Horizontal Stack), or ZStack (Depth Stack) depending on your layout needs.

## SwiftUI Image Scaling

### Making an Image Scalable

- Use `.resizable()` modifier to make images scalable within SwiftUI.
- This can be done by manually typing it or by dragging the attribute from the 'Modifiers' section in the '+' add bar.

### Maintaining Aspect Ratio

- To keep the image's proportions consistent, add `.aspectRatio(contentMode: .fit)` after `.resizable()`.
- This ensures the image scales within the given dimensions without distortion.

#### Example Code for Scalable Image:

```swift
Image("diamond")
    .resizable()
    .aspectRatio(contentMode: .fit)
    .frame(width: 200.0)
```

#### Example for a Scalable Avatar Image

```swift
Image("YourImageName in Assets")
    .resizable()
    .aspectRatio(contentMode: .fit)
    .frame(height: 150)
    .clipShape(Circle())
    .overlay(
        Circle().stroke(Color.white, lineWidth: 5)
    )
```

### Understanding Predefined Values

- Values that start with a '.' (dot) are predefined in SwiftUI, such as some fonts and colors.
- These provide a convenient way to use standard system values without memorizing specific parameters.

## Setting a Full-Screen Background Color in SwiftUI

To have a background color that fills the entire screen in SwiftUI, including the areas outside the safe area, you can use the following code pattern with a `ZStack`:

```swift
ZStack {
    Color(.blue).edgesIgnoringSafeArea(.all)
    // Your other components here
}
```

This code snippet places a `Color` view as the base layer of a `ZStack` and sets its edges to ignore the safe area, thus allowing the color to extend to the whole screen.

## Accessing the `info.plist` File in the Latest Version of Xcode

In newer versions of Xcode, the `info.plist` file might not be immediately visible if no changes have been made to it yet. To find and modify the `info.plist`:

1. Double-click on the project name in the Xcode navigator (look for the app icon, not the folder icon).
2. In the main area on the right, click on the "Info" tab.
3. To add a new property, click on the "+" button next to any existing property.

## Using Custom Fonts in SwiftUI

To incorporate custom fonts into your SwiftUI app, follow these steps:

#### Download and Add the Font to Your Project

1. Download your desired font, for example, from [Google Fonts](https://fonts.google.com/specimen/Pacifico?query=paci).
2. Right-click on your project folder in Xcode and create a new Group named `Fonts`.
3. Drag the downloaded font file, such as `Pacifico-Regular.ttf`, into this group. Ensure you check "Copy items if needed" so the file is copied to your project.

#### Register the Font in the `info.plist`

4. Open `info.plist` and add a new entry called "Fonts provided by application".
5. For the value, enter the name of the font file, such as "Pacifico-Regular.ttf".

#### Ensure the Font is Included in the Build

6. In the `info.plist`, double-click the added font entry. In the rightmost panel, make sure to check the target membership box for the current project to include the font in the build process.

#### Use the Font in SwiftUI Code

7. Apply the custom font in your SwiftUI views like this:

```swift
Text("Ruiming Xie").font(Font.custom("Pacifico-Regular", size: 40))
```

This code creates a `Text` view and applies the custom font `Pacifico-Regular` with a font size of 40.

## Shapes and Colors

### Using fill() for Shapes

For shapes, instead of applying color directly as a foreground color, it’s often more effective to use `fill()` to apply the color within the shape's boundary.

```swift
RoundedRectangle(cornerRadius: 25)
    .fill(Color.white)
```

### ForegroundColor for Text

For text elements, applying color is straightforward with the `foregroundColor()` modifier.

```swift
Text("Hello, World!")
    .foregroundColor(.white)
```

## SF Symbols

### Downloading SF Symbols

To use SF Symbols, first download SF Symbols 5 from Apple's official website.

### Searching and Using an SF Symbol

Once you have SF Symbols installed, you can easily browse and find the appropriate symbol for your use case.

```swift
Image(systemName: "phone.fill")
```

### Coloring SF Symbols

Change the color of an SF Symbol using `foregroundColor()`.

```swift
Image(systemName: "phone.fill")
    .foregroundColor(.green)
```

## Padding and Margins

Padding in SwiftUI might not behave as you expect if you're coming from a CSS background.

### Understanding Padding in SwiftUI

Padding in SwiftUI often acts more like what we would consider margins in CSS.

```swift
RoundedRectangle(cornerRadius: 25)
    .fill(Color.white)
    .frame(height: 50)
    .overlay(
        HStack {
            Image(systemName: "phone.fill")
                .foregroundColor(.green)
            Text("+61 402 369 915")
                .foregroundColor(.black)
        }
    )
    .padding(.all) // This adds space around the RoundedRectangle, like a CSS margin.
```

## Code Reusability

Xcode provides tools to help clean up and reuse your code effectively.

### Extracting a Subview

Select a block of code, right-click, and choose `Extract Subview` to create a reusable component.

## Creating Parameterized Views

SwiftUI's declarative syntax makes it simple to create views that can be customized with parameters.

### Defining a Parameterized View

You can define a view that takes parameters to create a reusable UI component.

```swift
struct InfoView: View {
    let text: String
    let imageName: String

    var body: some View {
        RoundedRectangle(cornerRadius: 25)
            .fill(Color.white)
            .frame(height: 50)
            .overlay(
                HStack {
                    Image(systemName: imageName)
                        .foregroundColor(.green)
                    Text(text)
                        .foregroundColor(.black)
                }
            )
            .padding(.all)
    }
}
```

### Using the Parameterized View

Instantiate and use the new view by passing in the required parameters.

```swift
InfoView(text: "+61 402 369 915", imageName: "phone.fill")
```

## Organizing UI Components

Maintaining an organized codebase is crucial when developing complex applications in SwiftUI. The Model-View-Controller (MVC) design pattern can help with this organization.

### Using the View Folder in MVC

In the MVC design pattern, it’s a common practice to place UI components in a dedicated `View` folder. This helps in keeping the project organized and the MVC layers separated.

### Creating a New SwiftUI View

When adding a new UI component, you should:

1. Click on `New File...` in Xcode.
2. Choose `SwiftUI View` from the template options.
3. Save the new file in the `View` folder to adhere to MVC principles.

### Example: InfoView.swift

Below is an example of how you can structure a SwiftUI view in a separate file:

```swift
import SwiftUI

struct InfoView: View {
    let text: String
    let imageName: String

    var body: some View {
        RoundedRectangle(cornerRadius: 25)
            .fill(Color.white)
            .frame(height: 50)
            // .foregroundColor(.white) // This line is commented out because we use .fill
            .overlay(
                HStack {
                    Image(systemName: imageName)
                        .foregroundColor(.green)
                    Text(text)
                        .foregroundColor(.black)
                }
            )
            .padding(.all)
    }
}

// MARK: - Preview
struct InfoView_Previews: PreviewProvider {
    static var previews: some View {
        InfoView(text: "+61 402 369 915", imageName: "phone.fill")
    }
}
```

### Using MARK Comments

To increase readability and organization of your SwiftUI views, use `// MARK: -` comments to separate different sections of the file, such as the body definition and the preview provider.

### Previews Section

SwiftUI allows you to preview your custom views with different data directly within Xcode. The `PreviewProvider` protocol enables you to see a live preview of your views with sample data.
