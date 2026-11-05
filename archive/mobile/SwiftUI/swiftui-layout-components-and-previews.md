# How do SwiftUI layout modifiers and reusable views fit together? / SwiftUI 布局 modifier 与可复用视图如何配合？

SwiftUI composes layout from view values and modifiers. Padding adds space around a composed view in its parent; reusable subviews and parameters keep repeated UI behavior together, while Xcode previews inspect sample inputs without replacing the runtime data source. / SwiftUI 由 view 值与 modifier 组合布局。padding 在父视图中为组合视图增加周围空间；提取子视图并用参数复用可集中重复 UI 行为，Xcode preview 则用样例输入检查界面，不替代运行时数据源。

## Xcode editors: Interface Builder and SwiftUI / Xcode 编辑器：Interface Builder 与 SwiftUI

### Interface Builder (storyboards and XIBs) / Interface Builder（storyboard 与 XIB）

- In storyboard or XIB editing, Xcode's library controls let you add UIKit/AppKit views and related objects. The control's position and appearance vary across Xcode versions.

### Embedding Components in Stack Views

- UIKit storyboards use `UIStackView` for arranged subviews. SwiftUI has separate `VStack`, `HStack`, and `ZStack` view types, authored in Swift code and optionally shown in the SwiftUI canvas; they are not Interface Builder stack views.

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
