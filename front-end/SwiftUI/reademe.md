# SwiftUI Notes

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

# String Interpolation

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
