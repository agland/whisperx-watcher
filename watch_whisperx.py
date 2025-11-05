import os, time, logging, math
from pathlib import Path
from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver as Observer
import whisperx
from whisperx.diarize import DiarizationPipeline

# Paths
RECORDINGS_DIR = Path("/Users/alex/Library/Mobile Documents/com~apple~CloudDocs/Recording")
MODELS_ASR_DIR = Path("/Users/alex/Library/Application Support/noScribe/whisper_models/faster-en-med")
MODELS_PYAN_DIR = Path("/Users/alex/transcriber/pyan_dir")
LOG_PATH = Path("/Users/alex/whisperx-watcher/watcher.log")
AUDIO_EXTS = {".m4a", ".wav", ".mp3", ".flac", ".ogg", ".aac"}

# Offline/local caches for HF/pyannote
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(MODELS_PYAN_DIR))
os.environ.setdefault("PYANNOTE_CACHE", str(MODELS_PYAN_DIR))

# Logging (file + console)
logger = logging.getLogger("watcher")
logger.setLevel(logging.INFO)
fh = logging.FileHandler(LOG_PATH)
ch = logging.StreamHandler()
fmt = logging.Formatter("%(asctime)s %(message)s")
fh.setFormatter(fmt); ch.setFormatter(fmt)
logger.addHandler(fh); logger.addHandler(ch)

def is_audio(p: Path) -> bool:
    return p.suffix.lower() in AUDIO_EXTS

def wait_for_stable(p: Path, interval=1.5, checks=3, timeout=600):
    logger.info(f"Waiting for file to stabilize: {p.name}")
    start = time.time(); last = -1; stable = 0
    while True:
        size = p.stat().st_size
        stable = stable + 1 if size == last else 0
        if stable >= checks:
            logger.info(f"File stabilized: {p.name}")
            return
        if time.time() - start > timeout:
            raise TimeoutError(f"Timeout waiting for {p.name} to stabilize")
        last = size
        time.sleep(interval)

def srt_timestamp(t: float) -> str:
    t = max(0.0, float(t))
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int(round((t - math.floor(t)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def write_srt(segments, path: Path):
    with open(path, "w") as f:
        for i, seg in enumerate(segments, 1):
            start = srt_timestamp(seg["start"])
            end = srt_timestamp(seg["end"])
            text = seg["text"].strip()
            spk = seg.get("speaker", "SPK0")
            f.write(f"{i}\n{start} --> {end}\n[{spk}] {text}\n\n")

def write_txt(segments, path: Path):
    with open(path, "w") as f:
        for seg in segments:
            spk = seg.get("speaker", "SPK0")
            f.write(f"[{spk} {seg['start']:.1f}-{seg['end']:.1f}] {seg['text'].strip()}\n")

def process_file(path: Path):
    if not is_audio(path): return
    txt_out = path.with_suffix(".txt")
    srt_out = path.with_suffix(".srt")
    try:
        # Skip if done and fresh
        if txt_out.exists() and srt_out.exists() and txt_out.stat().st_mtime >= path.stat().st_mtime:
            logger.info(f"Skipping already processed: {path.name}")
            return

        logger.info(f"Processing: {path.name}")
        wait_for_stable(path)

        logger.info("Loading ASR model (CPU int8)...")
        asr = whisperx.load_model("medium.en", device="cpu", compute_type="int8", download_root=str(MODELS_ASR_DIR))

        logger.info("Loading audio...")
        audio = whisperx.load_audio(str(path))

        logger.info("Transcribing...")
        res = asr.transcribe(audio, verbose=False)

        logger.info("Loading align model...")
        align_model, metadata = whisperx.load_align_model(language_code=res["language"], device="cpu")

        logger.info("Aligning...")
        res = whisperx.align(res["segments"], align_model, metadata, audio, device="cpu")

        # Diarization (best-effort, offline)
        diar_ok = False
        try:
            logger.info("Running diarization...")
            dp = DiarizationPipeline(use_auth_token=None, device="cpu")  # relies on local cache via env
            diar_segments = dp(audio)
            res = whisperx.assign_word_speakers(diar_segments, res)
            diar_ok = True
        except Exception as e:
            logger.error(f"Diarization failed; continuing without speakers: {e}")
            for seg in res["segments"]:
                seg.setdefault("speaker", "SPK0")

        logger.info("Writing outputs...")
        write_txt(res["segments"], txt_out)
        write_srt(res["segments"], srt_out)

        mark = "with diarization" if diar_ok else "without diarization"
        logger.info(f"Transcription complete ({mark}): {path.name}")
    except Exception as e:
        logger.error(f"Error processing {path.name}: {e}")

class Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory: return
        p = Path(event.src_path)
        if is_audio(p):
            logger.info(f"Detected new file: {p}")
            process_file(p)

if __name__ == "__main__":
    logger.info("Watcher starting...")
    # Process any existing files on startup
    for p in sorted(RECORDINGS_DIR.iterdir()):
        if p.is_file() and is_audio(p):
            process_file(p)

    observer = Observer()
    observer.schedule(Handler(), str(RECORDINGS_DIR), recursive=False)
    observer.start()
    logger.info("Watcher active.")
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
