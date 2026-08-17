import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

from tts import speak
from voice import VoiceCloningError, clone_voice, clone_voice_from_paths


VOICE_PROFILES_DIR = Path("./voice_profiles")
INDEX_HTML = Path(__file__).parent / "index.html"


class CloneRequest(BaseModel):
    voice_note_urls: list[str]
    grandparent_id: str


class SpeakRequest(BaseModel):
    text: str
    grandparent_id: str
    language: str = "hi"


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Voice cloning service ready")
    yield


app = FastAPI(lifespan=lifespan)


def _profile_path(grandparent_id: str) -> Path:
    if not grandparent_id.strip():
        raise ValueError("grandparent_id is required")
    if Path(grandparent_id).name != grandparent_id:
        raise ValueError("grandparent_id must not contain path separators")
    return VOICE_PROFILES_DIR / grandparent_id


def _delete_file(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


@app.get("/")
async def serve_index() -> FileResponse:
    if not INDEX_HTML.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(path=INDEX_HTML, media_type="text/html")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/upload-and-clone")
async def upload_and_clone_endpoint(
    grandparent_id: str = Form(...),
    files: list[UploadFile] = File(...),
) -> dict[str, str]:
    # Clone a voice profile from uploaded audio files (minimum five).
    try:
        if len(files) < 5:
            raise ValueError("At least 5 audio files are required for voice cloning")

        profile_path = _profile_path(grandparent_id)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            saved_paths: list[Path] = []
            for index, upload in enumerate(files, start=1):
                original_name = Path(upload.filename or f"voice_note_{index}.audio").name
                destination = temp_path / f"{index:03d}_{original_name}"
                destination.write_bytes(await upload.read())
                saved_paths.append(destination)

            voice_model_path = await clone_voice_from_paths(
                voice_note_paths=saved_paths,
                output_model_path=str(profile_path),
            )

        return {
            "voice_model_path": voice_model_path,
            "grandparent_id": grandparent_id,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except VoiceCloningError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/clone")
async def clone_endpoint(request: CloneRequest) -> dict[str, str]:
    # Clone and store a grandparent voice profile from at least five notes.
    try:
        if len(request.voice_note_urls) < 5:
            raise ValueError("At least 5 URLs are required for voice cloning")

        profile_path = _profile_path(request.grandparent_id)
        voice_model_path = await clone_voice(
            voice_note_urls=request.voice_note_urls,
            output_model_path=str(profile_path),
        )
        return {
            "voice_model_path": voice_model_path,
            "grandparent_id": request.grandparent_id,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except VoiceCloningError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/speak")
async def speak_endpoint(request: SpeakRequest) -> FileResponse:
    # Synthesize speech for a grandparent. The TTS switcher uses the cloned
    # profile when present and falls back to gTTS if the profile is missing.
    try:
        if not request.text.strip():
            raise ValueError("text is required")

        profile_path = _profile_path(request.grandparent_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            output_path = temp_audio.name

        try:
            audio_path = await speak(
                text=request.text,
                output_path=output_path,
                voice_model_path=str(profile_path),
                language=request.language,
            )
        except Exception:
            _delete_file(output_path)
            raise

        # The temp audio is removed only after FileResponse has streamed it.
        return FileResponse(
            path=audio_path,
            media_type="audio/mpeg",
            filename=f"{request.grandparent_id}_speech.mp3",
            background=BackgroundTask(_delete_file, audio_path),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except VoiceCloningError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
