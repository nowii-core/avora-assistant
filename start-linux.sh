#!/usr/bin/env bash
# Avvia Avora. Argomento opzionale: demo
cd "$(dirname "$0")"
MODE_ARG=""; [ "${1:-}" = "demo" ] && MODE_ARG="--demo"
if ! command -v python3 >/dev/null 2>&1; then echo "Installa Python 3 (https://www.python.org/downloads/) e riprova."; exit 1; fi
if [ -z "$MODE_ARG" ]; then
  if ! command -v ollama >/dev/null 2>&1; then
    echo "Ollama non trovato: installalo con 'curl -fsSL https://ollama.com/install.sh | sh' oppure da https://ollama.com/download."
    echo "Intanto parte la modalità demo."; MODE_ARG="--demo"
  elif ! curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    (ollama serve >/dev/null 2>&1 &); sleep 3
  fi
fi
exec python3 run.py $MODE_ARG
