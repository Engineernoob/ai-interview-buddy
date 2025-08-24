from faster_whisper import WhisperModel
import soundfile as sf, io

model = WhisperModel("small.en", device="cpu")

def transcribe_segment(audio_bytes: bytes) -> str:
    wav_buf = io.BytesIO()
    sf.write(wav_buf, audio_bytes, 16000, "PCM_16")
    wav_buf.seek(0)
    segments, _ = model.transcribe(wav_buf, language="en")
    return " ".join(s.text for s in segments)
