# Swift 中的值、函数与控制流怎样改变程序状态？

本章用几个互不依赖的小例子回答三个问题：两个分数怎样交换，坐标副本是否牵动原值，循环如何筛出符合条件的倍数。沿着每段代码的实际输入与输出，就能判断一次赋值改变了什么、函数怎样表达参数，以及控制流执行了几轮。

## `let` 与 `var` 分别限制什么？

`let` 声明不可重新赋值的绑定，`var` 声明可以重新赋值的绑定。编译错误示例保留为注释，避免把不能通过编译的语句混入可运行片段。

```swift
let a = 0
var b = 1
// a = 2 // 编译错误：常量不能重新赋值
b = 2
```

对值类型而言，常量实例的可变属性也不能改；对类实例而言，常量限制的是变量绑定，若类属性本身是 `var`，仍可修改该属性。后文会用结构体与类的差别具体说明。

## 函数调用点如何表达参数与结果？

函数用 `func` 声明。每个参数有内部名称；需要让调用更易读时，还可指定调用点使用的 argument label（参数标签）。省略标签时写 `_`。参数按声明顺序传入。

```swift
func greet(_ person: String, on day: String) -> String {
    "你好，\(person)，今天是\(day)。"
}

let message = greet("小林", on: "周五")
```

这里函数体用 `person` 与 `day`，调用点则写成 `greet("小林", on: "周五")`。参数标签是 Swift 调用语法的一部分，不只是文档注释。

默认参数让调用者省略不常变化的值；没有返回值时可省略返回类型，或显式写 `-> Void`。单表达式函数可以省略 `return`。

```swift
func greeting(_ person: String = "访客", on day: String = "今天") -> String {
    "你好，\(person)，今天是\(day)。"
}

greeting()
greeting("小林")
greeting("小林", on: "周五")

func add(a: Int, b: Int) -> Int {
    return a + b
}

func multiply(a: Int, b: Int) -> Int { a * b }
```

`greeting()` 使用两个默认值；`greeting("小林")` 只使用第二个参数的默认值。固定的返回类型要求所有可到达的正常结束路径都返回该类型的值。

## 函数怎样接收一组参数或修改调用者的变量？

variadic parameter（可变参数）接收零个或多个同类型值，在函数体内表现为数组。下面的 `sum` 可以用任意个整数调用：

```swift
func sum(_ numbers: Int...) -> Int {
    numbers.reduce(0, +)
}

let total = sum(2, 3, 5) // 10
```

若函数确实要改动调用者传入的变量，可使用 in-out parameter（输入输出参数）。调用点用 `&` 明示可能写回；实参必须是变量，不能传常量或字面量。它不能有默认值，也不能同时是可变参数。

> [!info] 输入输出参数在做什么
> Swift 将这类参数描述为先提供实参的值、在函数中修改、调用结束时再写回。它不是“把一个引用类型对象传进去”的同义说法；它对一个变量位置提供显式的读写访问。

```swift
func swapTwoInts(_ a: inout Int, _ b: inout Int) {
    let temporaryA = a
    a = b
    b = temporaryA
}

var someInt = 3
var anotherInt = 107
swapTwoInts(&someInt, &anotherInt)
// someInt 为 107，anotherInt 为 3
```

这个交换函数的两个 `inout` 参数必须访问不同的变量位置；`swapTwoInts(&someInt, &someInt)` 会违反独占访问规则，不能用来交换同一变量。函数没有返回值，但调用者的两个变量在执行后改变了。读代码时要把这种写回当作函数的可观察结果。

## 函数可以作为值传递或返回吗？

每个函数都有一个由参数类型和返回类型组成的 function type（函数类型）。函数可存进变量、传给另一个函数，也可由外层函数返回。函数类型不包含调用点标签。

```swift
var mathFunction: (Int, Int) -> Int = add
let result = mathFunction(2, 3) // 5

func chooseStepFunction(backward: Bool) -> (Int) -> Int {
    func stepForward(input: Int) -> Int { input + 1 }
    func stepBackward(input: Int) -> Int { input - 1 }
    return backward ? stepBackward : stepForward
}

let step = chooseStepFunction(backward: true)
let next = step(10) // 9
```

这个例子展示外层函数按 `backward` 选择并返回一个嵌套函数；返回的两个函数本身都没有捕获外层变量。若要观察真正的捕获，函数体可读取外层参数 `factor`：

```swift
func makeMultiplier(by factor: Int) -> (Int) -> Int {
    func multiply(_ value: Int) -> Int {
        value * factor
    }
    return multiply
}

let triple = makeMultiplier(by: 3)
let product = triple(4) // 12
```

这里返回的 `multiply` 保留了 `factor` 的值，因此 `triple(4)` 得到 12。这个行为是嵌套函数作为值返回并捕获外层参数的具体例子。

## 结构体方法什么时候需要 `mutating`？

`struct`（结构体）是 value type（值类型）。值类型的方法默认不能改动自身；若方法要修改属性或替换 `self`，要加 `mutating`（可变）。调用这种方法的结构体实例必须是 `var`。

```swift
struct Point {
    var x: Int
    var y: Int

    mutating func moveBy(x deltaX: Int, y deltaY: Int) {
        x += deltaX
        y += deltaY
    }
}

var somePoint = Point(x: 1, y: 1)
somePoint.moveBy(x: 2, y: 3)
// somePoint 现在是 (3, 4)
```

相对地，只读取或计算结果的方法不需要 `mutating`：

```swift
struct Calculator {
    var total: Int

    func addTwoNumbers(a: Int, b: Int) -> Int {
        a + b
    }
}
```

`mutating` 是对“方法可能改变值本身”的显式声明，不等于所有副作用；例如它不说明是否会打印或调用外部服务。

## 结构体赋值后，原值会跟着变化吗？

结构体、枚举、整数、字符串、数组与字典都采用 value semantics（值语义）。给结构体赋值会复制它的各个存储属性，但不会递归深复制属性所指向的整个对象图。标准库集合可以用写时复制优化存储，因此语义上的复制不代表每次都立刻搬移全部内存。

```swift
struct PointValue {
    var x: Int
    var y: Int
}

let p1 = PointValue(x: 10, y: 20)
var p2 = p1
p2.x = 30

print(p1.x) // 10
print(p2.x) // 30
```

值复制不是递归深复制。如果结构体的属性本身是类引用，副本会保存同一个引用；修改引用所指的对象时，两个结构体值都会观察到结果：

```swift
final class SharedBox {
    var value = 0
}

struct BoxHolder {
    var box: SharedBox
}

let original = BoxHolder(box: SharedBox())
let copy = original
copy.box.value = 7
print(original.box.value) // 7：两个结构体值引用同一个类实例
```

结构体不支持类继承，但可用协议与扩展组织共享行为。在结构体本体中声明自定义初始化方法后，编译器不再合成成员逐一初始化器；若要同时保留它，可把自定义初始化方法放进扩展。合成的成员逐一初始化器也不会自动成为 `public`，不能假定别的 module 能直接调用它。

## 类为什么共享身份？

`class`（类）是 reference type（引用类型）。将实例赋给另一个变量时，两处引用可以指向同一实例；类支持单继承、运行时类型检查和析构器 `deinit`。Swift 使用 automatic reference counting（自动引用计数，ARC）管理类实例的生命周期。`===` 与 `!==` 比较实例身份，而不是属性值是否相等。

```swift
class Animal {
    var name: String

    init(name: String) {
        self.name = name
    }

    func makeSound() {
        print("一般动物的声音")
    }
}

class Dog: Animal {
    override func makeSound() {
        print("汪")
    }
}

let dog = Dog(name: "Buddy")
dog.makeSound()
let anotherReference = dog
let isSameInstance = dog === anotherReference // true
```

`let` 类绑定仍能改写上面声明为 `var` 的 `name`，但不能把该绑定改指向另一个类实例。这与常量结构体中所有属性都不可变不同。

> [!example] 这两种类型会让共享状态呈现不同结果
> 改结构体自己的存储属性只影响那份值；但若某个属性保存类引用，副本与原值仍可能指向同一对象。若需求是两个独立坐标，结构体的值语义更直接；若多个组件必须跟踪同一连接或模型的身份，类才表达了这种共享关系。

默认先考虑值语义适合的结构体；需要共享身份、继承或特定 Objective-C 类层次兼容时再选类。判断依据是模型行为，不是“类一定更快”或“结构体一定更快”。

## 字符串插值与范围怎样表达计算？

string interpolation（字符串插值）用 `\(表达式)` 将值放入字符串；JavaScript 常用模板字符串 `${expression}`，两种语言的写法不同。

```swift
let varName = "Swift"
let text = "正在学习 \(varName)。"
```

closed range（闭区间）`0...5` 包含两端；half-open range（半开区间）`0..<5` 包含 0 但不包含 5。这个差别会影响循环次数和数组索引边界。

> [!info] 先看端点，再数迭代次数
> `1...5` 经过 1、2、3、4、5 共五次；`1..<5` 经过 1、2、3、4 共四次。遍历数组下标可用 `array.indices`；若明确从零开始，也可用 `0..<array.count` 避免访问不存在的末尾下标。

## 循环如何筛选、等待和提前离开？

`for-in` 可遍历范围、集合、字典和字符串。加入 `where` 可只执行满足条件的元素：

```swift
for index in 1...5 {
    print("索引值是 \(index)")
}

let names = ["Anna", "Alex", "Brian", "Jack"]
for name in names {
    print("Hello, \(name)!")
}

let numberOfLegs = ["spider": 8, "ant": 6, "cat": 4]
for (animalName, legCount) in numberOfLegs {
    print("\(animalName) 有 \(legCount) 条腿")
}

for character in "Hello" {
    print(character)
}

for number in 1...30 where number % 3 == 0 {
    print(number)
}
```

字典没有供程序依赖的固定遍历次序；若输出顺序有要求，先对键排序。普通 `while` 在每轮开始前检查条件；`repeat-while` 先执行一次循环体，再检查条件。下面两段都从 5 开始，各执行五次；若各自从 0 开始，`while` 执行零次，`repeat-while` 仍执行一次。

```swift
var counter = 5
while counter > 0 {
    print("Counter 是 \(counter)")
    counter -= 1
}

var countDown = 5
repeat {
    print("倒数：\(countDown)")
    countDown -= 1
} while countDown > 0
```

循环中的 `continue` 跳过当前轮剩余语句，`break` 退出当前循环或 `switch`：

```swift
for i in 1...10 {
    if i % 2 == 0 {
        continue
    }
    print("奇数：\(i)")
}

for i in 1...10 {
    if i > 5 {
        break
    }
    print("数字：\(i)")
}
```

> [!info]- 来源
> - **常量绑定和值类型**：Swift 语言指南“Properties”“Structures and Classes”，说明值类型复制、常量结构体属性与类引用的可变性；[Swift 语言指南](https://docs.swift.org/swift-book/LanguageGuide/Properties.html)与[结构体和类](https://docs.swift.org/swift-book/LanguageGuide/ClassesAndStructures.html)，核对日期 2026-11-13。
> - **函数标签、默认值、返回值、可变参数、输入输出参数与函数类型**：Swift 语言指南“Functions”与声明参考“In-Out Parameters”；[函数](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/functions/)及[声明](https://docs.swift.org/latest/documentation/the-swift-programming-language/declarations/)，核对日期 2026-11-13。
> - **`mutating` 方法、类身份、ARC 与结构体初始化限制**：Swift 语言指南“Methods”“Choosing Between Structures and Classes”“Initialization”；[方法](https://docs.swift.org/swift-book/LanguageGuide/Methods.html)、[类型选择](https://docs.swift.org/latest/documentation/swift/choosing-between-structures-and-classes/)、[初始化](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/initialization/)及[访问控制](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/accesscontrol/)，核对日期 2026-11-13。
> - **范围与循环**：Swift 语言指南“Control Flow”；[控制流](https://docs.swift.org/swift-book/LanguageGuide/ControlFlow.html)，核对日期 2026-11-13。
