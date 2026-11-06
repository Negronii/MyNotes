# SwiftUI 的布局修饰符和可复用视图如何配合？

你要把图标、标签和白色卡片组合成一行，并把它复用在多个信息项上。边框看起来太大时，是图形本身大了，还是留白被算进布局？重复界面该保留在一个文件里，还是拆为可传入数据的子视图？理解父子布局与修饰符顺序后，再决定如何抽取和预览。

## SwiftUI 与 Interface Builder 的布局方式有何不同？

在 storyboard（故事板）或 XIB（XML 界面文件）中，Interface Builder 通过编辑器拖放 UIKit/AppKit 控件；UIKit 的 `UIStackView` 是 storyboard 中排列子视图的容器。SwiftUI 则以 Swift 代码构造视图值，常用 `VStack`、`HStack`、`ZStack` 组合垂直、水平与叠放布局。它们与 Interface Builder 的堆栈容器不是同一个对象。

SwiftUI 布局大体按层次协商：父视图向子视图提出可用尺寸，子视图返回自己采用的尺寸，容器再确定位置。frame、padding 等 modifier（修饰符）改变参与协商的视图包装，因此阅读一串 modifier 时应先确认每一步包住了哪个视图。

## `padding` 为什么不像 CSS 的 `margin`？

SwiftUI 没有一个独立 CSS 风格的 margin 属性。`padding` 给当前组合视图的边缘增加空间，父布局会把这段空间计入视图尺寸。修饰符按从上到下的顺序包裹前面的结果。

```swift
RoundedRectangle(cornerRadius: 25)
    .fill(.white)
    .frame(height: 50)
    .overlay {
        HStack {
            Image(systemName: "phone.fill")
                .foregroundStyle(.green)
            Text("Contact")
                .foregroundStyle(.black)
        }
    }
    .padding()
```

这里 `padding()` 作用于已包含矩形、frame 和 overlay 的完整组合，因此留白出现在组合视图外侧。要看顺序的实际影响，可比较边框包住留白前后的视图：

```swift
Text("Contact")
    .padding(8)
    .border(.blue) // 边框包含文字和留白

Text("Contact")
    .border(.blue)
    .padding(8) // 外侧留白不在边框内
```

> [!example] 读 modifier 链时逐层追踪边界
> 从内到外读第一段：矩形形状先填白色，再获得 50 点高度，再叠加图标和文字，最后整体增加系统默认留白。因此父容器看到的是带留白的完整卡片，而不是单独的文字或矩形。

> [!warning] 固定高度不适合直接承载任意字号的内容
> 上例的 50 点高度只是演示 modifier 顺序；较大的 Dynamic Type 或较长文本可能溢出固定框。真实卡片应让内容参与测量，用最小高度而不是强制高度，并让背景跟随内容伸展：
>
> ```swift
> HStack {
>     Image(systemName: "phone.fill")
>     Text("Contact")
> }
> .frame(minHeight: 50)
> .padding(.horizontal, 12)
> .padding(.vertical, 8)
> .background {
>     RoundedRectangle(cornerRadius: 25).fill(.white)
> }
> ```

## 什么时候把一段界面抽成参数化子视图？

当多处界面共享相同结构、但标签或图标不同，就把变化部分变为参数。Xcode 某些版本可通过编辑器的 Extract Subview 操作生成子视图；也可以直接声明一个 View（视图）类型。

```swift
import SwiftUI

struct InfoView: View {
    let text: String
    let imageName: String

    var body: some View {
        HStack {
            Image(systemName: imageName)
                .foregroundStyle(.green)
            Text(text)
                .foregroundStyle(.black)
        }
        .frame(minHeight: 50)
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background {
            RoundedRectangle(cornerRadius: 25).fill(.white)
        }
    }
}
```

调用者只提供不同数据，结构和样式仍由该组件负责：

```swift
struct ContactList: View {
    var body: some View {
        VStack {
            InfoView(text: "Contact", imageName: "phone.fill")
            InfoView(text: "Email", imageName: "envelope.fill")
        }
    }
}
```

把视图文件放进名为 `Views` 的文件夹是一种项目组织约定，不是 SwiftUI 要求；目录名本身不会改变视图行为。新建文件时可从 Xcode 的 SwiftUI View 模板开始，再按项目的边界组织 view 与 model。文件内可用 `// MARK: -` 分隔属性、视图内容和预览等区域。

## Xcode 预览能验证什么？

预览用给定输入在 canvas 中显示视图，帮助检查布局和不同样例；它不是运行时数据源，也不保证网络、权限、完整导航或设备行为与真实 app 一致。提供可重复的样例输入，可以更快定位布局变化：

```swift
// MARK: - Preview
#Preview {
    InfoView(text: "Contact", imageName: "phone.fill")
}

#Preview {
    InfoView(text: "Email", imageName: "envelope.fill")
}
```

较旧的工具链或不便使用预览宏的项目仍可通过 `PreviewProvider` 声明：

```swift
struct InfoView_Previews: PreviewProvider {
    static var previews: some View {
        InfoView(text: "Contact", imageName: "phone.fill")
    }
}
```

两种写法描述的是 Xcode 预览配置；现代项目通常用 `#Preview`。预览通过后仍要在目标平台检查交互、动态字体、资源与系统环境差异。

> [!info]- 来源
> - **父子视图提议尺寸、返回尺寸与组合布局**：Apple SwiftUI “Laying Out a Simple View”及布局调整指南；[简单布局](https://developer.apple.com/documentation/swiftui/laying-out-a-simple-view)及[布局调整](https://developer.apple.com/documentation/swiftui/layout-adjustments)，核对日期 2026-11-06。
> - **padding 尺寸和 modifier 顺序**：Apple SwiftUI `padding(_:)` API；[padding](https://developer.apple.com/documentation/swiftui/view/padding%28_%3A%29-68shk)，核对日期 2026-11-06。
> - **`#Preview`、样例数据与旧 `PreviewProvider`**：Apple Xcode “Adding Previews to Your Interface Files”及 SwiftUI “Previews in Xcode”；[添加预览](https://developer.apple.com/documentation/xcode/adding-previews-to-your-interface-files)及[预览集合](https://developer.apple.com/documentation/swiftui/previews-in-xcode)，核对日期 2026-11-06。
