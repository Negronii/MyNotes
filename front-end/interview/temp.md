### Oh My Zsh
```zsh
# If you come from bash you might have to change your $PATH.
# export PATH=$HOME/bin:$HOME/.local/bin:/usr/local/bin:$PATH

# Path to your Oh My Zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Set name of the theme to load --- if set to "random", it will
# load a random theme each time Oh My Zsh is loaded, in which case,
# to know which specific one was loaded, run: echo $RANDOM_THEME
# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
ZSH_THEME="robbyrussell"

# Set list of themes to pick from when loading at random
# Setting this variable when ZSH_THEME=random will cause zsh to load
# a theme from this variable instead of looking in $ZSH/themes/
# If set to an empty array, this variable will have no effect.
# ZSH_THEME_RANDOM_CANDIDATES=( "robbyrussell" "agnoster" )

# Uncomment the following line to use case-sensitive completion.
# CASE_SENSITIVE="true"

# Uncomment the following line to use hyphen-insensitive completion.
# Case-sensitive completion must be off. _ and - will be interchangeable.
# HYPHEN_INSENSITIVE="true"

# Uncomment one of the following lines to change the auto-update behavior
# zstyle ':omz:update' mode disabled  # disable automatic updates
# zstyle ':omz:update' mode auto      # update automatically without asking
# zstyle ':omz:update' mode reminder  # just remind me to update when it's time

# Uncomment the following line to change how often to auto-update (in days).
# zstyle ':omz:update' frequency 13

# Uncomment the following line if pasting URLs and other text is messed up.
# DISABLE_MAGIC_FUNCTIONS="true"

# Uncomment the following line to disable colors in ls.
# DISABLE_LS_COLORS="true"

# Uncomment the following line to disable auto-setting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment the following line to enable command auto-correction.
# ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
# You can also set it to another string to have that shown instead of the default red dots.
# e.g. COMPLETION_WAITING_DOTS="%F{yellow}waiting...%f"
# Caution: this setting can cause issues with multiline prompts in zsh < 5.7.1 (see #5765)
# COMPLETION_WAITING_DOTS="true"

# Uncomment the following line if you want to disable marking untracked files
# under VCS as dirty. This makes repository status check for large repositories
# much, much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment the following line if you want to change the command execution time
# stamp shown in the history command output.
# You can set one of the optional three formats:
# "mm/dd/yyyy"|"dd.mm.yyyy"|"yyyy-mm-dd"
# or set a custom format using the strftime function format specifications,
# see 'man strftime' for details.
# HIST_STAMPS="mm/dd/yyyy"

# Would you like to use another custom folder than $ZSH/custom?
# ZSH_CUSTOM=/path/to/new-custom-folder

# Which plugins would you like to load?
# Standard plugins can be found in $ZSH/plugins/
# Custom plugins may be added to $ZSH_CUSTOM/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(git zsh-autosuggestions zsh-syntax-highlighting zsh-completions)

source $ZSH/oh-my-zsh.sh

# User configuration

# export MANPATH="/usr/local/man:$MANPATH"

# You may need to manually set your language environment
# export LANG=en_US.UTF-8

# Preferred editor for local and remote sessions
# if [[ -n $SSH_CONNECTION ]]; then
#   export EDITOR='vim'
# else
#   export EDITOR='mvim'
# fi

# Compilation flags
# export ARCHFLAGS="-arch $(uname -m)"

# Set personal aliases, overriding those provided by Oh My Zsh libs,
# plugins, and themes. Aliases can be placed here, though Oh My Zsh
# users are encouraged to define aliases within a top-level file in
# the $ZSH_CUSTOM folder, with .zsh extension. Examples:
# - $ZSH_CUSTOM/aliases.zsh
# - $ZSH_CUSTOM/macos.zsh
# For a full list of active aliases, run `alias`.
#
# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"

# pnpm
export PNPM_HOME="/Users/ruiming.xie/Library/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) export PATH="$PNPM_HOME:$PATH" ;;
esac
# pnpm end
➜  ~ nano .zshrc
➜  ~ cat .zshrc
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

# If you come from bash you might have to change your $PATH.
# export PATH=$HOME/bin:$HOME/.local/bin:/usr/local/bin:$PATH

# Path to your Oh My Zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Set name of the theme to load --- if set to "random", it will
# load a random theme each time Oh My Zsh is loaded, in which case,
# to know which specific one was loaded, run: echo $RANDOM_THEME
# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
ZSH_THEME="robbyrussell"

# Set list of themes to pick from when loading at random
# Setting this variable when ZSH_THEME=random will cause zsh to load
# a theme from this variable instead of looking in $ZSH/themes/
# If set to an empty array, this variable will have no effect.
# ZSH_THEME_RANDOM_CANDIDATES=( "robbyrussell" "agnoster" )

# Uncomment the following line to use case-sensitive completion.
# CASE_SENSITIVE="true"

# Uncomment the following line to use hyphen-insensitive completion.
# Case-sensitive completion must be off. _ and - will be interchangeable.
# HYPHEN_INSENSITIVE="true"

# Uncomment one of the following lines to change the auto-update behavior
# zstyle ':omz:update' mode disabled  # disable automatic updates
# zstyle ':omz:update' mode auto      # update automatically without asking
# zstyle ':omz:update' mode reminder  # just remind me to update when it's time

# Uncomment the following line to change how often to auto-update (in days).
# zstyle ':omz:update' frequency 13

# Uncomment the following line if pasting URLs and other text is messed up.
# DISABLE_MAGIC_FUNCTIONS="true"

# Uncomment the following line to disable colors in ls.
# DISABLE_LS_COLORS="true"

# Uncomment the following line to disable auto-setting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment the following line to enable command auto-correction.
# ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
# You can also set it to another string to have that shown instead of the default red dots.
# e.g. COMPLETION_WAITING_DOTS="%F{yellow}waiting...%f"
# Caution: this setting can cause issues with multiline prompts in zsh < 5.7.1 (see #5765)
# COMPLETION_WAITING_DOTS="true"

# Uncomment the following line if you want to disable marking untracked files
# under VCS as dirty. This makes repository status check for large repositories
# much, much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment the following line if you want to change the command execution time
# stamp shown in the history command output.
# You can set one of the optional three formats:
# "mm/dd/yyyy"|"dd.mm.yyyy"|"yyyy-mm-dd"
# or set a custom format using the strftime function format specifications,
# see 'man strftime' for details.
# HIST_STAMPS="mm/dd/yyyy"

# Would you like to use another custom folder than $ZSH/custom?
# ZSH_CUSTOM=/path/to/new-custom-folder

# Which plugins would you like to load?
# Standard plugins can be found in $ZSH/plugins/
# Custom plugins may be added to $ZSH_CUSTOM/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(git zsh-autosuggestions zsh-syntax-highlighting zsh-completions)

source $ZSH/oh-my-zsh.sh

# User configuration

# export MANPATH="/usr/local/man:$MANPATH"

# You may need to manually set your language environment
# export LANG=en_US.UTF-8

# Preferred editor for local and remote sessions
# if [[ -n $SSH_CONNECTION ]]; then
#   export EDITOR='vim'
# else
#   export EDITOR='mvim'
# fi

# Compilation flags
# export ARCHFLAGS="-arch $(uname -m)"

# Set personal aliases, overriding those provided by Oh My Zsh libs,
# plugins, and themes. Aliases can be placed here, though Oh My Zsh
# users are encouraged to define aliases within a top-level file in
# the $ZSH_CUSTOM folder, with .zsh extension. Examples:
# - $ZSH_CUSTOM/aliases.zsh
# - $ZSH_CUSTOM/macos.zsh
# For a full list of active aliases, run `alias`.
#
# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"

# pnpm
export PNPM_HOME="/Users/ruiming.xie/Library/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) export PATH="$PNPM_HOME:$PATH" ;;
esac
# pnpm end
```

### debugger

```javascript
function foo() {
  debugger;
  console.log('foo');
}
```

In chrome devtools, you can use `debugger` to pause the execution of the code and inspect the variables. 

### performance measurement

In chrome devtools, you can go to performance, then click record (round button) on top left, then see the performance of the recorded time.

### See render

In React devtools, settings, general, check "Highlight updates when components render". It can also record performance like chrome devtools. It is more specific to React and comprehensive.

In JavaScript, **hidden classes** are an optimization mechanism primarily used to enhance the performance of property access in objects. They are an internal feature of the V8 engine (used by Chrome and Node.js) that helps speed up how properties are accessed by dynamically managing the structure of objects.

### How Hidden Classes Work

1. **Object Creation**: When you create an object, the JavaScript engine assigns a hidden class to that object, which contains layout information about its properties.

2. **Adding Properties**: When you add properties to an object, if these properties are added in a consistent order and manner, the JavaScript engine can reuse the existing hidden class or create a new one that reflects the object's structure.

3. **Optimized Access**: By using hidden classes, the JavaScript engine can quickly locate an object's properties without having to search through the entire object, making property access more efficient.

### Example

Consider the following code:

```javascript
function createPoint(x, y) {
    return { x: x, y: y };
}

const p1 = createPoint(1, 2);
const p2 = createPoint(3, 4);
```

In this example, both `p1` and `p2` will have the same hidden class because they have the same structure.

### Benefits of Hidden Classes

- **Shared Structure**: If multiple objects have the same properties and structure, they can share the same hidden class, improving performance.
- **Avoiding Dynamic Modifications**: Frequently adding or removing properties can lead to changes in hidden classes, which can degrade performance. Therefore, it’s best to determine an object’s structure as much as possible at creation time.

### Summary

Hidden classes are an internal mechanism used by JavaScript engines to optimize property access in objects. By designing object structures thoughtfully, you can leverage this mechanism to enhance the execution efficiency of your code.

## Improve performance experience

In Shopee's CMT project, we had a requirement to enhance the user experience by adding a "Set Metrics" button to the drawer filter interface. When users click the filter button on the table, a drawer containing various filter fields appears. Our goal was to integrate a "Set Metrics" button at the top of this drawer, allowing users to customize their view. Upon clicking the "Set Metrics" button, a modal should pop up, enabling users to select which fields they want to display in the drawer filter.

We were using a useDrawerFilter custom hook to manage the filter drawer options, the result is passed to the table component as a prop. 

The initial design involved managing state through a useSetMetrics custom hook, which maintained two key states: one for tracking selected metrics that changed with user selections in the "Set Metrics" modal (representing unsaved changes) and another for saved changes. The useMetrics hook was then called within the useDrawerFilter hook to retrieve these states, utilizing the saved changes to determine which fields to display. 

However, a significant issue arose when the "Set Metrics" modal was opened; any selection or deselection of fields would trigger a re-render of the useDrawerFilter hook due to updates in the unsaved changes state. This unintended re-rendering affected the entire table, causing it to refresh every time a change was made, resulting in a noticeable delay of around half a second for updates. This behavior created a frustrating user experience and highlighted the need for a more efficient state management approach.

Initially, I was unsure of the cause of the performance issue. To investigate, I utilized Chrome DevTools to record the application's performance. The recording revealed that JavaScript calculations were consuming nearly all the processing time. Upon further inspection, I discovered that the React Diff function was taking an excessive amount of time, indicating that something was being re-rendered too frequently. To pinpoint the issue, I opened the React DevTools and enabled the "Show re-rendered components" feature. This allowed me to identify that the entire table component was re-rendering with every selection change made in the "Set Metrics" modal, confirming my suspicion that unnecessary re-renders were significantly impacting performance.

The final solution involved moving the useSetMetrics hook inside the SetMetricsButton component, which effectively isolated the state management for metrics selection. This change prevented unnecessary re-renders of the useDrawerFilter hook and its parent components whenever the state of the "Set Metrics" modal changed.

The useDrawerFilter hook continued to manage the state of selected fields, with a callback function for updating the state passed to the button component. This callback was only invoked when the save button in the modal was clicked, ensuring that the hook's state was updated only when necessary.

After implementing this change, performance improved significantly; however, it was still not sufficient. The modal's closing animation was sluggish due to lingering performance issues, negatively impacting the user experience. To address this, I optimized the process by allowing the animation to complete before calling the callback to update the state.

While further optimization could involve managing the drawer filter directly within the table component and passing a callback to update its state, I opted not to pursue this approach because the Shanghai Team did not have access to the necessary library.