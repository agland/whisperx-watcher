# WhisperX Watcher  
A lightweight macOS utility that automatically transcribes audio recordings dropped into a watched folder using [WhisperX](https://github.com/m-bain/whisperX).  
It runs locally with optional speaker diarization support and saves `.txt` and `.srt` transcripts automatically.

---

## Overview
This setup is optimized for users who:
- Use **macOS** and want a local, fast transcription pipeline.
- Prefer **faster-whisper** models for offline ASR.
- Optionally use **pyannote.audio** diarization with their own Hugging Face token.
- Want the watcher to start automatically at login.

---

## Folder structure
```

~/whisperx-watcher/
├── install.sh
├── run_watcher.command
├── watch_whisperx.py
├── README.md
└── (optional) config.env.example

````

- **install.sh** – installs dependencies, sets up the virtual environment, and optionally downloads models.  
- **run_watcher.command** – launches the watcher in a new terminal window.  
- **watch_whisperx.py** – monitors a folder and runs WhisperX when new audio appears.  

---

## Installation

### 1. Clone this repo
```bash
git clone https://github.com/agland/whisperx-watcher.git
cd whisperx-watcher
````

### 2. Run setup

```bash
./install.sh
```

This script:

* Creates a Python virtual environment (`~/.venvs/whisperx`)
* Installs WhisperX, PyTorch, Watchdog, and dependencies
* Sets up folder paths:

  * `APP_DIR`: `~/whisperx-watcher`
  * `MODELS_ASR_DIR`: where the Whisper model will be stored
  * `MODELS_PYAN_DIR`: for optional diarization models
* Offers to download **Systran/faster-whisper-medium.en** automatically
  (no token required; can also auto-download later on first run)

---

## Running the watcher

After install:

```bash
open ./run_watcher.command
```

This opens a new Terminal window that runs the watcher.
When a new `.m4a` or `.wav` file appears in your configured recordings folder, it will:

1. Wait for the file to finish copying.
2. Transcribe it with WhisperX.
3. Optionally run speaker diarization (if models + token available).
4. Save `.txt` and `.srt` files next to the recording.

---

## Optional: Run automatically at login

To auto-start at macOS login, add this as a Login Item:

```bash
osascript -e 'tell application "System Events" to make login item at end with properties {path:"/Users/$USER/whisperx-watcher/run_watcher.command", hidden:false}'
```

You can also do it manually in:
**System Settings → General → Login Items → Add run_watcher.command**

---

## Models

### ASR (required)

* **Model:** `Systran/faster-whisper-medium.en`
* **Access:** Public, no token needed.
* **Installer:** offers to download automatically into your `MODELS_ASR_DIR`.
* If skipped, WhisperX will auto-fetch at runtime.

### Diarization (optional)

* **Models:**

  * `pyannote/speaker-diarization-3.1`
  * `pyannote/segmentation-3.0`
* **Access:** gated on Hugging Face. Request access at [https://huggingface.co/pyannote](https://huggingface.co/pyannote).
* **Usage:** once approved, set your token and download:

  ```bash
  export HF_TOKEN=hf_yourtokenhere
  hf download pyannote/speaker-diarization-3.1 --local-dir "$MODELS_PYAN_DIR/speaker-diarization-3.1" --token "$HF_TOKEN"
  hf download pyannote/segmentation-3.0 --local-dir "$MODELS_PYAN_DIR/segmentation-3.0" --token "$HF_TOKEN"
  ```
* Without these, WhisperX will still output valid transcripts (no speaker labels).

---

## Offline mode

Once your models are downloaded, you can run completely offline by setting:

```bash
export HF_HUB_OFFLINE=1
```

---

## Troubleshooting

| Symptom                                                                         | Likely cause                                   | Fix                                                  |
| ------------------------------------------------------------------------------- | ---------------------------------------------- | ---------------------------------------------------- |
| `module 'whisperx.utils' has no attribute 'write_srt'`                          | Older WhisperX version                         | Reinstall: `pip install -U whisperx`                 |
| `DiarizationPipeline.__init__() got an unexpected keyword argument 'model_dir'` | pyannote version mismatch                      | Skip diarization or re-download with correct version |
| Script stalls at "Performing voice activity detection"                          | Pyannote downloading large model               | Wait or disable diarization                          |
| Nothing happens on new file                                                     | Verify `Recordings_DIR` path in watcher config |                                                      |

---

## Uninstall

To remove everything:

```bash
rm -rf ~/.venvs/whisperx ~/whisperx-watcher ~/transcriber
```

---

## License

MIT.  Contributions welcome.

---

## Credits

* [WhisperX](https://github.com/m-bain/whisperX) – speech-to-text and alignment
* [Pyannote.audio](https://github.com/pyannote/pyannote-audio) – diarization models
* [Hugging Face Hub](https://huggingface.co) – model hosting

```

---
