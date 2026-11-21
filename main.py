import os, subprocess, uuid, imageio_ffmpeg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from faster_whisper import WhisperModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
os.makedirs("outputs", exist_ok=True)
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")

class VideoRequest(BaseModel):
    youtube_url: str

@app.get("/")
def home():
    return {"status": "ClipForge Render Server Active"}

@app.post("/api/process")
def process_video(req: VideoRequest):
    job_id = str(uuid.uuid4())[:8]
    raw = f"outputs/{job_id}_raw.mp4"
    short = f"outputs/{job_id}_short.mp4"
    try:
        subprocess.run(["yt-dlp", "-f", "best[height<=720][ext=mp4]/best[ext=mp4]", "-o", raw, req.youtube_url], check=True)
        segments, _ = whisper_model.transcribe(raw)
        text = " ".join([s.text.strip() for s in list(segments)[:4]]) or "वायरल शॉर्ट तैयार है!"
        subprocess.run([ffmpeg_exe, "-y", "-i", raw, "-ss", "00:00:05", "-t", "00:00:30", "-vf", "crop=ih*9/16:ih,scale=720:1280", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", short], check=True)
        if os.path.exists(raw): os.remove(raw)
        return {
            "title": "YouTube शॉर्ट तैयार है!",
            "thumbnail": "https://images.unsplash.com/photo-1611162617474-5b21e879e113?auto=format&fit=crop&w=800&q=80",
            "clips": [{
                "title": "AI काटा गया शॉर्ट #1 (9:16)",
                "duration": "00:30",
                "score": 96,
                "timestamp": "00:05 - 00:35",
                "caption": text[:120],
                "reason": "Render सर्वर द्वारा प्रोसेस किया गया।",
                "download_url": f"/outputs/{job_id}_short.mp4"
            }]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
