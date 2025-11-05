#!/usr/bin/env bash
set -euo pipefail

echo "[1/8] Checking Xcode CLT..."
xcode-select -p >/dev/null 2>&1 || xcode-select --install || true

echo "[2/8] Checking Homebrew..."
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew not found. Installing..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

echo "[3/8] Installing ffmpeg..."
brew list ffmpeg >/dev/null 2>&1 || brew install ffmpeg

echo "[4/8] Installing Python 3.11..."
brew list python@3.11 >/dev/null 2>&1 || brew install python@3.11
PY311="$(brew --prefix)/opt/python@3.11/bin/python3.11"

echo "[5/8] Creating venv..."
$PY311 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel setuptools

echo "[6/8] Installing Python deps (CPU wheels)..."
python -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
python -m pip install whisperx watchdog soundfile huggingface_hub

echo "[7/8] Configure paths"
if [[ ! -f config.env ]]; then
  cp config.env.example config.env
  echo "Edit config.env now? [y/N]"
  read -r EDIT
  if [[ "${EDIT:-N}" =~ ^[Yy]$ ]]; then ${EDITOR:-nano} config.env; fi
fi
source config.env

mkdir -p "$LOG_DIR"
touch "$LOG_DIR/watcher.log"

echo "[8/8] Optional: download pyannote (gated)."
echo "If you have HF_TOKEN and accepted access, download now? [y/N]"
read -r DL
if [[ "${DL:-N}" =~ ^[Yy]$ && -n "${HF_TOKEN:-}" ]]; then
  hf download pyannote/speaker-diarization-3.1 --local-dir "$MODELS_PYAN_DIR/speaker-diarization-3.1" --token "$HF_TOKEN" || true
  hf download pyannote/segmentation-3.0        --local-dir "$MODELS_PYAN_DIR/segmentation-3.0"      --token "$HF_TOKEN" || true
fi

echo "Install complete."
echo "Start watcher with:  open ./run_watcher.command"
