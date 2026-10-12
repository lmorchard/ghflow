#!/bin/sh
# Link the ghflow OpenCode plugins into the global plugin directory.
# Usage: scripts/install-opencode-plugin.sh [--remove]
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
TARGET_DIR="${OPENCODE_CONFIG_DIR:-$HOME/.config/opencode}/plugins"
mkdir -p "$TARGET_DIR"
for src in "$HERE"/opencode-plugins/*.js; do
  name=$(basename "$src")
  dest="$TARGET_DIR/$name"
  if [ "${1:-}" = "--remove" ]; then
    [ -L "$dest" ] && rm "$dest" && echo "removed $dest"
    continue
  fi
  if [ -e "$dest" ] && [ ! -L "$dest" ]; then
    echo "refusing to replace a regular file: $dest" >&2
    exit 1
  fi
  ln -sfn "$src" "$dest"
  echo "linked $dest -> $src"
done
