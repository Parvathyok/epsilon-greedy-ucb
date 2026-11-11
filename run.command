#!/bin/zsh
set -eu
cd "$(dirname "$0")"
if [[ -x .venv/bin/python3 ]]; then
  BANDIT_PYTHON=.venv/bin/python3
elif [[ -x "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3" ]]; then
  BANDIT_PYTHON="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
else
  BANDIT_PYTHON=python3
fi
"$BANDIT_PYTHON" -c 'import numpy' || { echo "Install the requirements using the README instructions."; exit 1; }
exec "$BANDIT_PYTHON" -m backend.server "$@"
