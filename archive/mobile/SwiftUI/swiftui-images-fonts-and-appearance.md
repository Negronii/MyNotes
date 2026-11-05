# How do image resources, fonts, and styles affect SwiftUI appearance? / 图片资源、字体和样式如何影响 SwiftUI 外观？

UIKit `UIImage` is not a SwiftUI `Image` view; resource names, font registration, platform plist keys, symbol availability, and modifier order shape rendering. The examples keep iOS-family and macOS font keys separate and expand the view that should extend beyond the safe area. / UIKit `UIImage` 不是 SwiftUI `Image` 视图；资源名称、字体注册、平台 plist 键、符号可用性与 modifier 顺序共同影响呈现。示例区分 iOS 系列和 macOS 字体键，并扩展需要越过安全区的视图。

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

## Sources / 参考资料

- Swift Language Guide: [functions](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/functions/), [structures and classes](https://docs.swift.org/swift-book/LanguageGuide/ClassesAndStructures.html), and [initialization](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/initialization/). The in-out parameter description follows Swift's [declaration reference](https://docs.swift.org/latest/documentation/the-swift-programming-language/declarations/); leading-dot shorthand is specified as an [implicit member expression](https://docs.swift.org/swift-book/ReferenceManual/Expressions.html#implicit-member-expression).
- Apple SwiftUI: [State](https://developer.apple.com/documentation/swiftui/state), [Binding](https://developer.apple.com/documentation/swiftui/binding), [StateObject](https://developer.apple.com/documentation/swiftui/stateobject), [ObservedObject](https://developer.apple.com/documentation/swiftui/observedobject), and [EnvironmentObject](https://developer.apple.com/documentation/swiftui/environmentobject). The newer Observation availability and environment pattern are scoped in Apple's [migration guide](https://developer.apple.com/documentation/swiftui/migrating-from-the-observable-object-protocol-to-the-observable-macro) and [model-data guide](https://developer.apple.com/documentation/swiftui/managing-model-data-in-your-app).
- Apple Developer Documentation: [SwiftUI images](https://developer.apple.com/documentation/swiftui/image), [adding images to an Xcode project](https://developer.apple.com/documentation/xcode/adding-images-to-your-xcode-project), [custom fonts](https://developer.apple.com/documentation/swiftui/applying-custom-fonts-to-text), [managing app information property-list values](https://developer.apple.com/documentation/bundleresources/managing-your-app-s-information-property-list), [foregroundColor deprecation](https://developer.apple.com/documentation/swiftui/view/foregroundcolor%28_%3A%29), [safe-area expansion](https://developer.apple.com/documentation/swiftui/view/ignoressafearea%28_%3Aedges%3A%29), and [Xcode previews](https://developer.apple.com/documentation/xcode/adding-previews-to-your-interface-files).
- `#imageLiteral` maps to UIKit's documented [`UIImage(imageLiteralResourceName:)`](https://developer.apple.com/documentation/uikit/uiimage/init%28imageliteralresourcename%3A%29); use SwiftUI `Image` for SwiftUI view hierarchies. Platform/API availability checked 2026-10-15.
