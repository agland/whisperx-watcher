# WhisperX Watcher (macOS, CPU-only, int8)

Watches a folder for new audio and outputs `<name>.txt` and `<name>.srt`. Uses WhisperX + alignment and best-effort pyannote diarization. Apple Silicon, CPU-only, int8.

## Install
```bash
git clone https://github.com/agland/whisperx-watcher.git
cd whisperx-watcher
./install.sh
open ./run_watcher.command

