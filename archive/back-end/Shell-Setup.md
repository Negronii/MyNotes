# Shell Setup (Oh My Zsh)

## Installation

```bash
sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

## Key Configuration (`~/.zshrc`)

### Theme

```zsh
ZSH_THEME="robbyrussell"
```

### Plugins

```zsh
plugins=(git zsh-autosuggestions zsh-syntax-highlighting zsh-completions)
```

- `git` — aliases like `gst` (status), `gco` (checkout), `gl` (pull)
- `zsh-autosuggestions` — suggests commands as you type based on history
- `zsh-syntax-highlighting` — colors valid/invalid commands in real time
- `zsh-completions` — extra completion definitions

### pnpm Path

```zsh
export PNPM_HOME="$HOME/Library/pnpm"
case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) export PATH="$PNPM_HOME:$PATH" ;;
esac
```
