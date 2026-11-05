# Who owns SwiftUI state, and how do child views receive changes? / SwiftUI 状态由谁拥有，子视图如何接收变更？

SwiftUI stores `@State` according to view identity; `Binding` gives a child a read/write connection to state owned elsewhere. For reference models, choose the wrapper that matches ownership and observation: legacy `ObservableObject` wrappers differ from the iOS 17+/macOS 14+ Observation pattern. / SwiftUI 按 view identity 保存 `@State`；`Binding` 让子视图读写由别处拥有的状态。引用模型应按所有权与观察系统选择 wrapper：旧 `ObservableObject` wrappers 与 iOS 17+/macOS 14+ Observation 模式不同。

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

## Sources / 参考资料

- Swift Language Guide: [functions](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/functions/), [structures and classes](https://docs.swift.org/swift-book/LanguageGuide/ClassesAndStructures.html), and [initialization](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/initialization/). The in-out parameter description follows Swift's [declaration reference](https://docs.swift.org/latest/documentation/the-swift-programming-language/declarations/); leading-dot shorthand is specified as an [implicit member expression](https://docs.swift.org/swift-book/ReferenceManual/Expressions.html#implicit-member-expression).
- Apple SwiftUI: [State](https://developer.apple.com/documentation/swiftui/state), [Binding](https://developer.apple.com/documentation/swiftui/binding), [StateObject](https://developer.apple.com/documentation/swiftui/stateobject), [ObservedObject](https://developer.apple.com/documentation/swiftui/observedobject), and [EnvironmentObject](https://developer.apple.com/documentation/swiftui/environmentobject). The newer Observation availability and environment pattern are scoped in Apple's [migration guide](https://developer.apple.com/documentation/swiftui/migrating-from-the-observable-object-protocol-to-the-observable-macro) and [model-data guide](https://developer.apple.com/documentation/swiftui/managing-model-data-in-your-app).
- Apple Developer Documentation: [SwiftUI images](https://developer.apple.com/documentation/swiftui/image), [adding images to an Xcode project](https://developer.apple.com/documentation/xcode/adding-images-to-your-xcode-project), [custom fonts](https://developer.apple.com/documentation/swiftui/applying-custom-fonts-to-text), [managing app information property-list values](https://developer.apple.com/documentation/bundleresources/managing-your-app-s-information-property-list), [foregroundColor deprecation](https://developer.apple.com/documentation/swiftui/view/foregroundcolor%28_%3A%29), [safe-area expansion](https://developer.apple.com/documentation/swiftui/view/ignoressafearea%28_%3Aedges%3A%29), and [Xcode previews](https://developer.apple.com/documentation/xcode/adding-previews-to-your-interface-files).
- `#imageLiteral` maps to UIKit's documented [`UIImage(imageLiteralResourceName:)`](https://developer.apple.com/documentation/uikit/uiimage/init%28imageliteralresourcename%3A%29); use SwiftUI `Image` for SwiftUI view hierarchies. Platform/API availability checked 2026-10-15.
