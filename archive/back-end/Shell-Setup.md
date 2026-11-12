# Zsh 怎样从启动配置找到插件与 pnpm 命令？

**案例背景：** 新终端中输入 `pnpm` 得到 `command not found`，补全和语法高亮也没有出现。三个现象可能发生在不同步骤：程序尚未安装、启动文件没有执行，或查找路径与加载顺序不对。先分清谁在找什么，才能改对配置。

~~~mermaid
flowchart TD
    A[启动交互式 Zsh] --> B[读取适用的启动文件]
    B --> C[设置插件位置、fpath 与 PATH]
    C --> D[载入 Oh My Zsh]
    D --> E[框架运行 compinit]
    E --> F[从 fpath 注册补全函数]
    F --> G[按 Tab 调用对应函数]
    D --> H[插件初始化行编辑器]
    H --> I[最后载入语法高亮]
    C --> J[输入 pnpm：PATH 查找可执行程序]
~~~

## 启动文件不是同一个入口

默认设置下，Zsh（Z shell，一种 Unix 命令行解释器）会读取 `.zshenv`；login shell（登录 shell）另外读取 `.zprofile`，interactive shell（交互式 shell）读取 `.zshrc`，登录 shell 最后还会读取 `.zlogin`。因此常见的交互式登录 shell 按 `.zshenv` → `.zprofile` → `.zshrc` → `.zlogin` 的顺序读取用户文件。各类文件有系统级和用户级版本，用户文件位于 `$ZDOTDIR`，仅在它未设置时才取 `$HOME`。终端窗口是否启动登录 shell 取决于终端配置，因此新终端不一定会按登录 shell 的路径配置启动。

插件、提示符和键盘交互通常放在 `.zshrc`。脚本执行环境不能假定读过它，因此“终端能运行 pnpm”不代表 CI、编辑器启动的进程或非交互 shell 也有同一个 `PATH`。为运行程序配置明确的环境，不要把整个交互配置当作脚本依赖。

## 框架、插件文件和启用配置怎样衔接？

Oh My Zsh 是可选的配置框架。先安装它和需要的插件，再通过 `source` 在当前 shell 执行其启动脚本。框架加载时读取 `plugins` 数组，因此必须先赋值。数组元素用空格分隔；内置 Git 插件的 `gst`、`gco` 只是 `git status`、`git checkout` 的 alias（别名）。它们没有创建新 Git 功能。

外部的 `zsh-autosuggestions`、`zsh-syntax-highlighting`、`zsh-completions` 都需要各自的实际文件。只把名称写进数组不会安装插件。`zsh-completions` 的 Oh My Zsh 配方是把它的 `src` 目录放入 `fpath`，不要把它作为普通插件添加。下例假设 Oh My Zsh 已安装在所示目录、两个插件已放到框架可发现的位置，并把补全项目的路径替换成真实安装目录：

~~~zsh
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="robbyrussell"
plugins=(git zsh-autosuggestions zsh-syntax-highlighting)
fpath+=(/actual/install/path/zsh-completions/src)
source "$ZSH/oh-my-zsh.sh"
~~~

Oh My Zsh 的启动脚本会运行 `compinit`；将补全目录放进 `fpath` 后再载入框架即可，不要在这份配置里再显式运行一次 `compinit`。框架之外的纯 Zsh 配置才需要在设置 `fpath` 后运行 `autoload -U compinit && compinit`。语法高亮按其维护者要求最后加载；若框架载入后还配置会影响 Zsh 行编辑器的其他插件或 widget（编辑器操作），应将高亮加载放在这些设置之后。重新打开终端通常比反复 `source ~/.zshrc` 更容易观察一次干净的加载；重复 source 可能重复注册钩子和监听行为。

## `fpath` 与 `PATH` 分别查找什么？

| 名称 | 搜索对象 | 本例中的用途 |
|---|---|---|
| `PATH` / Zsh 的 `path` 数组 | 外部可执行程序 | 查找 `pnpm`、`git` |
| `fpath` | 可自动加载的 Zsh 函数文件 | 查找补全定义 |

`fpath` 中的文件由 `compinit` 建立命令与补全函数之间的映射。例如，隔离测试用的 `_pnpm` 文件可以是：

~~~zsh
#compdef pnpm
_pnpm() { compadd -- example-option }
~~~

初始化时，`#compdef pnpm` 登记 `pnpm` 对应的 `_pnpm`；在测试提示符输入 `pnpm ex` 后按 Tab，Zsh 调用该函数并补出 `example-option`。这个教学替身只展示注册与调用过程，实际补全由安装的定义提供。纯 Zsh 配置应在把真实 `src` 目录加入 `fpath` 后运行一次 `autoload -U compinit && compinit`；使用 Oh My Zsh 时则让前面的框架入口完成初始化。

## pnpm 已安装，为何仍找不到？

先用 `whence -va pnpm` 检查当前 shell 能否找到程序。若找不到，先按原安装方式定位可执行文件，用其绝对路径运行；若尚未安装，则先完成安装。`pnpm setup` 本身也要由一个已经可运行的 pnpm 执行，不能直接修复“程序根本不存在”的问题。

按 2026-11-13 核对的 pnpm 12.x 文档，`pnpm setup` 会准备 `PNPM_HOME` 并安装当前 pnpm；能识别启动配置且未指定 `--no-modify-path` 时，还会更新 shell 的命令路径。如果它无法判断要改哪个配置文件（例如容器没有设置 `SHELL`），仍会安装，并打印需要手动加入的 `PNPM_HOME` 与 `PATH` 行。`--no-modify-path` 则明确要求不改路径配置。版本和安装方式会影响选项与目录，使用其他版本时先查看 `pnpm setup --help`；尤其 pnpm 本身与全局命令目录可能不同，应以安装输出为准。若选择手工维护，下面只演示如何加入一个**已存在且包含目标程序**的目录：

~~~zsh
export PNPM_HOME="$HOME/Library/pnpm" # 示例，按实际安装位置替换
case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) export PATH="$PNPM_HOME:$PATH" ;;
esac
~~~

> [!example] 为什么给 PATH 两侧加冒号？
> 假设目录是 `/opt/pnpm`。在 `:/usr/bin:/opt/pnpm:/bin:` 中匹配 `:/opt/pnpm:`，检查的是完整目录项，不会把 `/opt/pnpm-old` 当作命中。重复执行也不会再次前置同一目录。

`PATH` 从前向后查找外部程序；但 shell alias 或函数可能先拦截命令名。排查时看解析结果而不是只看配置文件：

~~~zsh
whence -va pnpm
print -l -- $path
print -l -- $fpath
~~~

这些结果回答“当前 shell 会使用哪个命令、去哪些目录找”，不证明另一个终端或 CI 使用相同环境。`pnpm setup` 的当前全局命令布局涉及 `$PNPM_HOME/bin`；若需要这些命令，应检查 setup 实际生成的目录安排，不能只复制旧教程的一条 PATH。

## 怎样区分语法检查和加载成功？

先确认本次 shell 对应的用户配置路径，再检查该文件：

~~~zsh
print -r -- "${ZDOTDIR-$HOME}/.zshrc"
zsh -n "${ZDOTDIR-$HOME}/.zshrc"
~~~

这里的 `-` 只在 `ZDOTDIR` 未设置时回退到 `$HOME`；若变量已设置为空，不会误改成检查 `$HOME/.zshrc`。如果启动脚本会重设 `ZDOTDIR`，应使用诊断得到的实际读取路径。`zsh -n` 只解析指定文件的语法，不执行其中的 `source`，所以不存在的插件文件、错误的程序路径也可能通过。再开新交互 shell，观察启动错误并检查 `whence -va`、补全与高亮。读到配置、找到文件、初始化成功、最终功能可用，是四个不同的检查点。

> [!info]- 来源
> - 启动文件条件与 ZDOTDIR：Zsh 5.9.2 [Startup/Shutdown Files](https://zsh.sourceforge.io/Doc/Release/Files.html#Startup_002fShutdown-Files)，核对 2026-11-13。
> - 框架与插件顺序：[Oh My Zsh Plugins](https://github.com/ohmyzsh/ohmyzsh/wiki/Plugins)、[Git 插件别名](https://github.com/ohmyzsh/ohmyzsh/blob/master/plugins/git/README.md)。
> - 外部插件安装与最后加载要求：[autosuggestions](https://github.com/zsh-users/zsh-autosuggestions/blob/master/INSTALL.md)、[syntax-highlighting INSTALL](https://github.com/zsh-users/zsh-syntax-highlighting/blob/master/INSTALL.md)；框架的补全初始化：[Oh My Zsh 启动脚本](https://github.com/ohmyzsh/ohmyzsh/blob/master/oh-my-zsh.sh)；补全目录与 Oh My Zsh 安装方式：[zsh-completions README](https://github.com/zsh-users/zsh-completions#oh-my-zsh)。核对 2026-11-13。
> - `pnpm setup` 的选项、路径更新和全局命令目录：[pnpm 12.x setup](https://pnpm.io/12.x/cli/setup)，核对 2026-11-13；pnpm 9.15.2 本机只读 `--help`，未运行会修改配置的 setup。
