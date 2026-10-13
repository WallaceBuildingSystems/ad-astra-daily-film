"""Local word-timed transcription with faster-whisper.

usage: WHISPER_PROMPT="Robert Goddard, Auburn, Ad Astra, 1926." python3 transcribe.py audio.wav [model]

Writes audio.words.json (word, start, end, probability) and prints the transcript and any low-confidence words.
WHISPER_PROMPT should list the day's names, places and numbers so they are spelled as in the script.
"""
import json, os, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel

model = WhisperModel(sys.argv[2] if len(sys.argv) > 2 else "small.en", device="cpu", compute_type="int8")
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", sys.argv[1], "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                     capture_output=True, check=True).stdout
audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
segs, info = model.transcribe(audio, word_timestamps=True, beam_size=5, vad_filter=True, condition_on_previous_text=False,
                              initial_prompt=os.environ.get("WHISPER_PROMPT", "Ad Astra."))
words = []
for s in segs:
    for w in s.words:
        words.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)})
out = sys.argv[1].rsplit(".", 1)[0] + ".words.json"
json.dump(words, open(out, "w"), indent=0)
print(" ".join(w["w"] for w in words))
print("low confidence:", [(w["w"], w["s"], w["p"]) for w in words if w["p"] < 0.6])
