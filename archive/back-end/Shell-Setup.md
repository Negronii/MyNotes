# Shell Setup: Zsh and Oh My Zsh / Zsh 与 Oh My Zsh

核心操作：先安装框架和外部插件，再把已存在的插件写入 `plugins` 数组；语法高亮最后加载，`zsh-completions` 的 `fpath` 配置放在 Oh My Zsh 启动前。`PNPM_HOME` 应指向实际安装目录，而 `zsh -n` 只检查语法。

Oh My Zsh is an optional Zsh configuration framework. Installing the framework, enabling a plugin, and installing that plugin are separate steps. Review the current [official installation instructions](https://ohmyz.sh/#install) before choosing an install method; this note does not run an installer.

## Minimal `.zshrc` / 最小配置

```zsh
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="robbyrussell"
plugins=(git)
source "$ZSH/oh-my-zsh.sh"
```

Oh My Zsh reads the `plugins` array when its startup script is sourced; array items are separated by spaces, not commas. The bundled `git` plugin adds aliases such as `gst` (`git status`) and `gco` (`git checkout`). The aliases are conveniences, not separate Git commands.

## Optional external plugins / 可选外部插件

`zsh-autosuggestions`, `zsh-syntax-highlighting`, and `zsh-completions` are separate projects. Listing their names does not install them: first follow each project's installation instructions and put its files where Oh My Zsh can load them. Add only plugins that are present:

```zsh
plugins=(git zsh-autosuggestions zsh-completions zsh-syntax-highlighting)
```

Load `zsh-syntax-highlighting` last; its maintainers require that order. `zsh-completions` has an `fpath` setup step that belongs before Oh My Zsh is sourced; follow its current instructions rather than assuming the array alone enables every completion definition. Restart the shell after changing the plugin list.

## pnpm on the command path / pnpm 命令路径

The pnpm home directory depends on the installation method and platform. Current pnpm provides `pnpm setup` to create its home directory and update the shell configuration. If managing the path manually, use the actual directory selected for that installation; the following is a macOS example, not a portable default:

```zsh
export PNPM_HOME="$HOME/Library/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) export PATH="$PNPM_HOME:$PATH" ;;
esac
```

The membership check avoids adding the same directory repeatedly. After editing `.zshrc`, `zsh -n ~/.zshrc` checks shell syntax only; it does not verify that referenced plugins exist or that every command in startup files is available.

## Sources / 参考资料

- [Oh My Zsh installation](https://ohmyz.sh/#install), [plugin configuration](https://github.com/ohmyzsh/ohmyzsh/wiki/Plugins), and the [Git plugin aliases](https://github.com/ohmyzsh/ohmyzsh/blob/master/plugins/git/README.md).
- External plugin installation and ordering: [zsh-autosuggestions](https://github.com/zsh-users/zsh-autosuggestions/blob/master/INSTALL.md), [zsh-syntax-highlighting](https://github.com/zsh-users/zsh-syntax-highlighting/blob/master/INSTALL.md), and [zsh-completions](https://github.com/zsh-users/zsh-completions#oh-my-zsh).
- [pnpm setup](https://pnpm.io/cli/setup) documents how it creates the pnpm home directory and adds it to `PATH` through shell configuration.
