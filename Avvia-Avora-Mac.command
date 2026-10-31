#!/bin/bash
# Avvia Avora con un doppio clic. Aggiungi "demo" come argomento per la modalità demo.
cd "$(dirname "$0")"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
MODE_ARG=""; [ "$1" = "demo" ] && MODE_ARG="--demo"
pause_exit() { read -r -p "Premi Invio per chiudere... " _; exit 1; }

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 non è installato. Apro la pagina ufficiale del download..."
  open "https://www.python.org/downloads/macos/" || true
  pause_exit
fi

if [ -z "$MODE_ARG" ]; then
  if ! command -v ollama >/dev/null 2>&1 && [ ! -d "/Applications/Ollama.app" ]; then
    echo "Per usare i modelli serve Ollama (gratuito). Apro il download ufficiale."
    echo "Installalo, aprilo una volta e riavvia questo file. Intanto parte la modalità demo."
    open "https://ollama.com/download/mac" || true
    MODE_ARG="--demo"
  else
    open -a Ollama >/dev/null 2>&1 || true
    for _ in $(seq 1 30); do curl -fsS "http://127.0.0.1:11434/api/tags" >/dev/null 2>&1 && break; sleep 1; done
  fi
fi

if [ ! -x ".venv/bin/python" ]; then python3 -m venv .venv >/dev/null 2>&1 || true; fi
PYTHON="python3"; [ -x ".venv/bin/python" ] && PYTHON="$PWD/.venv/bin/python"
if [ -z "$MODE_ARG" ] && ! "$PYTHON" -c "import edge_tts" >/dev/null 2>&1; then
  curl -fsSI --connect-timeout 2 --max-time 4 https://pypi.org/simple/edge-tts/ >/dev/null 2>&1 \
    && "$PYTHON" -m pip install --disable-pip-version-check --quiet -r requirements-voice.txt >/dev/null 2>&1 || true
fi
echo "Avvio Avora. Il browser si aprirà da solo; la configurazione dei modelli è guidata."
"$PYTHON" run.py $MODE_ARG
