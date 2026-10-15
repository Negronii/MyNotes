# Swift and SwiftUI Notes / Swift 与 SwiftUI 笔记

Core idea / 核心概念: Swift value types express independent values; class instances carry shared reference identity. SwiftUI view values describe a hierarchy, while state and bindings connect that hierarchy to mutable data. Property-wrapper choice depends on who owns the data and which observation system the model uses.

核心要点：Swift struct 采用值语义，class 实例则可共享引用身份；SwiftUI 的 view 值可以重建，而状态由 view identity 管理。`@State` 持有本地状态，`Binding` 让子视图编辑同一数据源；`ObservableObject` 和新 Observation 系统各有匹配的所有权与环境注入方式。

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

## SwiftUI state and data flow / SwiftUI 状态与数据流

SwiftUI view structs are values that the framework may recreate as inputs change. SwiftUI-managed state is stored by **view identity**, so its lifetime follows the identity of the view in the hierarchy, not one particular struct value. Keep local view state private and put it at the highest view that owns it. When a view's identity changes, its state storage is recreated.

`@State` owns a value for a view hierarchy; `Binding` is a read/write connection to state owned elsewhere. Passing a plain property gives a child read-only input, while `$property` passes a binding that lets the child edit the same source of truth:

```swift
struct CounterView: View {
    @State private var count = 0

    var body: some View {
        VStack {
            Text("Count: \(count)")
            CounterButton(count: $count)
        }
    }
}

struct CounterButton: View {
    @Binding var count: Int

    var body: some View {
        Button("Add one") { count += 1 }
    }
}
```

For the older `ObservableObject` model system, use `@StateObject` where a view creates and owns a reference model for its identity, and pass that model to child views with `@ObservedObject`. The child observes an input; it should not create the owned model itself. `@EnvironmentObject` is another legacy `ObservableObject` path for an ancestor-supplied model; the ancestor must inject it with `.environmentObject(model)`.

```swift
final class LegacyModel: ObservableObject {
    @Published var title = "Sample"
}

struct LegacyOwner: View {
    @StateObject private var model = LegacyModel()

    var body: some View {
        LegacyChild(model: model)
    }
}

struct LegacyChild: View {
    @ObservedObject var model: LegacyModel

    var body: some View { Text(model.title) }
}
```

Starting with iOS 17, iPadOS 17, macOS 14, tvOS 17, and watchOS 10, SwiftUI supports the Observation system. An `@Observable` reference model can be owned in `@State`, injected with `.environment(model)`, and read using `@Environment(Model.self)`. SwiftUI tracks observable properties that a view's body reads; use `@EnvironmentObject`/`@ObservedObject` for `ObservableObject` models, not as interchangeable wrappers for every reference type.

```swift
import Observation
import SwiftUI

@Observable final class ModernModel {
    var title = "Sample"
}

struct ModernOwner: View {
    @State private var model = ModernModel()

    var body: some View {
        ModernChild().environment(model)
    }
}

struct ModernChild: View {
    @Environment(ModernModel.self) private var model

    var body: some View { Text(model.title) }
}
```

If an `@Environment(Model.self)` or `@EnvironmentObject` lookup has no matching ancestor value, the view fails at runtime. Add the matching environment modifier at the appropriate app, scene, or parent boundary.

## UIKit image literals and SwiftUI images / UIKit 图像字面量与 SwiftUI 图像

UIKit provides `UIImage(imageLiteralResourceName:)`, which Xcode has historically exposed through `#imageLiteral` completion. The result is a UIKit `UIImage`, not a SwiftUI `Image` view. For SwiftUI, store images in an asset catalog and display them with `Image("assetName")`.

### Key Points

- The resource name resolves to an image file or asset in the app bundle; using a literal is optional.

### Xcode image-literal example / Xcode 字面量示例

To use an image literal in Xcode:

1. Type `#imageLiteral(` and Xcode will offer to autocomplete this with an image literal. Alternatively, you can start typing the name of your image and Xcode's autocomplete may suggest the image literal for you.
2. A media library picker will be presented, allowing you to select an image from your asset catalog.
3. Once selected, the literal will be inserted into your code, and it will display a small thumbnail of the image.

### Example

```swift
import UIKit

let image: UIImage = #imageLiteral(resourceName: "your_image_name")
```

`UIImage` belongs to UIKit. The literal's resource name must resolve in the target's resources; for a SwiftUI `Image` view, prefer `Image("your_image_name")` and verify the corresponding image set is included in the target.

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

## Xcode editors: Interface Builder and SwiftUI / Xcode 编辑器：Interface Builder 与 SwiftUI

### Interface Builder (storyboards and XIBs) / Interface Builder（storyboard 与 XIB）

- In storyboard or XIB editing, Xcode's library controls let you add UIKit/AppKit views and related objects. The control's position and appearance vary across Xcode versions.

### Embedding Components in Stack Views

- UIKit storyboards use `UIStackView` for arranged subviews. SwiftUI has separate `VStack`, `HStack`, and `ZStack` view types, authored in Swift code and optionally shown in the SwiftUI canvas; they are not Interface Builder stack views.

## SwiftUI Image Scaling

### Making an Image Scalable

- Use `.resizable()` modifier to make images scalable within SwiftUI.
- The modifier can be written in code; Xcode's canvas/editor controls vary between releases.

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
Image("avatar")
    .resizable()
    .aspectRatio(contentMode: .fit)
    .frame(height: 150)
    .clipShape(Circle())
    .overlay(
        Circle().stroke(Color.white, lineWidth: 5)
    )
```

### Leading-dot member shorthand / 点号成员简写

Swift's leading-dot syntax is an implicit member expression: the surrounding type context tells the compiler which static member to use. For example, `.blue` is shorthand for `Color.blue` when a `Color` is expected, and `.largeTitle` is shorthand for `Font.largeTitle` in a font position. A user-defined type can provide static members usable the same way; leading-dot values are not limited to predefined SwiftUI members.

## Setting a Full-Screen Background Color in SwiftUI

To have a background color that fills the entire screen in SwiftUI, including the areas outside the safe area, you can use the following code pattern with a `ZStack`:

```swift
ZStack {
    Color.blue.ignoresSafeArea()
    // Your other components here
}
```

`edgesIgnoringSafeArea(_:)` is deprecated; use `ignoresSafeArea(_:edges:)`. `Color.blue.ignoresSafeArea()` extends the background view. Apply the modifier to the view that should expand; a surrounding container may affect the resulting layout.

This code snippet places a `Color` view as the base layer of a `ZStack` and extends it beyond the safe area to fill the entire screen.

## Editing app information in Xcode / 在 Xcode 中编辑应用信息

Xcode commonly generates the bundle's information property list from target build settings, so an editable `Info.plist` file may not exist in the project. To add or change an app information value:

1. Select the project in the Project navigator, then select the target.
2. Use the target's **Info** pane to edit supported property-list values; Xcode maps these to build settings or a generated plist.
3. If the target requires a manually managed `Info.plist`, configure that workflow in Build Settings rather than assuming every project has a physical file.

## Using Custom Fonts in SwiftUI

To incorporate custom fonts into your SwiftUI app, follow these steps:

#### Download and Add the Font to Your Project

1. Add a font file you are licensed to distribute to the app target and ensure target membership is enabled.
2. For iOS-family targets, register the font file under `UIAppFonts` (shown as "Fonts provided by application" in Xcode's property-list editor). The value is the file path within the bundle.
3. For macOS targets, Apple's documented key is `ATSApplicationFontsPath`; check the platform-specific font instructions.

#### Register the Font in the `info.plist`

Xcode may generate the final plist from target settings instead of keeping a visible `Info.plist` source file. Configure the key through the target's supported Info/build settings when applicable.

#### Use the Font in SwiftUI Code

Apply the font using its **PostScript name**, which may differ from the filename:

```swift
Text("Sample text").font(.custom("SamplePostScriptName", size: 40))
```

This applies the custom font with a base size of 40 points. For text that should scale with Dynamic Type, use the appropriate scalable custom-font initializer. Verify the PostScript name in Font Book.

## Shapes and Colors

### Using fill() for Shapes

For shapes, instead of applying color directly as a foreground color, it’s often more effective to use `fill()` to apply the color within the shape's boundary.

```swift
RoundedRectangle(cornerRadius: 25)
    .fill(Color.white)
```

### Foreground style for text / 文本前景样式

Use `foregroundStyle(_:)` for a color or style applied to text and other foreground elements. `foregroundColor(_:)` is deprecated.

```swift
Text("Hello, World!")
    .foregroundStyle(.white)
```

## SF Symbols

### Downloading SF Symbols

Use Apple's SF Symbols app and documentation to find a symbol name supported by the deployment target. Symbol availability varies by platform release; the name in a code example is not guaranteed to exist on every target.

### Searching and Using an SF Symbol

Once you have SF Symbols installed, you can easily browse and find the appropriate symbol for your use case.

```swift
Image(systemName: "phone.fill")
```

### Coloring SF Symbols

Apply a foreground style to an SF Symbol using the same style system as text.

```swift
Image(systemName: "phone.fill")
    .foregroundStyle(.green)
```

## Padding and Margins

Padding is a layout modifier. Modifier order matters: in the example below, padding wraps the composed shape, so it creates space around that view in its parent. It is not a separate CSS-style `margin` property.

### Understanding Padding in SwiftUI

```swift
RoundedRectangle(cornerRadius: 25)
    .fill(Color.white)
    .frame(height: 50)
    .overlay(
        HStack {
            Image(systemName: "phone.fill")
                .foregroundStyle(.green)
            Text("Contact")
                .foregroundStyle(.black)
        }
    )
    .padding() // Adds space around the composed view in its parent.
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
                        .foregroundStyle(.green)
                    Text(text)
                        .foregroundStyle(.black)
                }
            )
            .padding(.all)
    }
}
```

### Using the Parameterized View

Instantiate and use the new view by passing in the required parameters.

```swift
InfoView(text: "Contact", imageName: "phone.fill")
```

## Organizing UI Components

SwiftUI does not require a particular project-folder layout or a Model-View-Controller (MVC) architecture. Organize view files and models around the app's boundaries; an Xcode `View` group is a project convention, not a framework requirement.

### Optional view folder / 可选的 View 文件夹

Some projects place SwiftUI view types in a `Views` folder. Choose folders that make the project easier to navigate; the folder name does not change SwiftUI behavior.

### Creating a New SwiftUI View

When adding a new UI component, you should:

1. Click on `New File...` in Xcode.
2. Choose `SwiftUI View` from the template options.
3. Save the file in the group or folder used by the project.

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
            // The shape uses fill; foregroundStyle below colors its child views.
            .overlay(
                HStack {
                    Image(systemName: imageName)
                        .foregroundStyle(.green)
                    Text(text)
                        .foregroundStyle(.black)
                }
            )
            .padding(.all)
    }
}

// MARK: - Preview
#Preview {
    InfoView(text: "Contact", imageName: "phone.fill")
}
```

Xcode's preview macro is the current concise form. `PreviewProvider` remains available when a project or toolchain needs the manual form:

```swift
struct InfoView_Previews: PreviewProvider {
    static var previews: some View {
        InfoView(text: "Contact", imageName: "phone.fill")
    }
}
```

### Using MARK Comments

To increase readability and organization of your SwiftUI views, use `// MARK: -` comments to separate different sections of the file, such as the body definition and the preview provider.

### Previews Section

Previews let you inspect a view with sample data in Xcode without changing the runtime data source.

## Sources / 参考资料

- Swift Language Guide: [functions](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/functions/), [structures and classes](https://docs.swift.org/swift-book/LanguageGuide/ClassesAndStructures.html), and [initialization](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/initialization/). The in-out parameter description follows Swift's [declaration reference](https://docs.swift.org/latest/documentation/the-swift-programming-language/declarations/); leading-dot shorthand is specified as an [implicit member expression](https://docs.swift.org/swift-book/ReferenceManual/Expressions.html#implicit-member-expression).
- Apple SwiftUI: [State](https://developer.apple.com/documentation/swiftui/state), [Binding](https://developer.apple.com/documentation/swiftui/binding), [StateObject](https://developer.apple.com/documentation/swiftui/stateobject), [ObservedObject](https://developer.apple.com/documentation/swiftui/observedobject), and [EnvironmentObject](https://developer.apple.com/documentation/swiftui/environmentobject). The newer Observation availability and environment pattern are scoped in Apple's [migration guide](https://developer.apple.com/documentation/swiftui/migrating-from-the-observable-object-protocol-to-the-observable-macro) and [model-data guide](https://developer.apple.com/documentation/swiftui/managing-model-data-in-your-app).
- Apple Developer Documentation: [SwiftUI images](https://developer.apple.com/documentation/swiftui/image), [adding images to an Xcode project](https://developer.apple.com/documentation/xcode/adding-images-to-your-xcode-project), [custom fonts](https://developer.apple.com/documentation/swiftui/applying-custom-fonts-to-text), [managing app information property-list values](https://developer.apple.com/documentation/bundleresources/managing-your-app-s-information-property-list), [foregroundColor deprecation](https://developer.apple.com/documentation/swiftui/view/foregroundcolor%28_%3A%29), [safe-area expansion](https://developer.apple.com/documentation/swiftui/view/ignoressafearea%28_%3Aedges%3A%29), and [Xcode previews](https://developer.apple.com/documentation/xcode/adding-previews-to-your-interface-files).
- `#imageLiteral` maps to UIKit's documented [`UIImage(imageLiteralResourceName:)`](https://developer.apple.com/documentation/uikit/uiimage/init%28imageliteralresourcename%3A%29); use SwiftUI `Image` for SwiftUI view hierarchies. Platform/API availability checked 2026-10-15.
