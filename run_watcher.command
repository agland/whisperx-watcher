#!/usr/bin/env bash
cd "$(dirname "$0")"
source "./config.env"
export HF_HUB_OFFLINE HUGGINGFACE_HUB_CACHE PYANNOTE_CACHE
export RECORDINGS_DIR MODELS_ASR_DIR MODELS_PYAN_DIR LOG_DIR
export WHISPERX_MODEL_NAME WHISPERX_DEVICE WHISPERX_COMPUTE_TYPE
./.venv/bin/python ./watcher/watch_whisperx.py
