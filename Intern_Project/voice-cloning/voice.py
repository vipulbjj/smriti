import asyncio
import os
import tempfile
from pathlib import Path

import httpx
import torch
from pydub import AudioSegment
from TTS.api import TTS


XTTS_V2_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"

_tts_model = None
_tts_device = None


def _get_tts_model():
    global _tts_model, _tts_device
    if _tts_model is None:
        _tts_device = "cuda" if torch.cuda.is_available() else "cpu"
        _tts_model = TTS(XTTS_V2_MODEL).to(_tts_device)
    return _tts_model, _tts_device


class VoiceCloningError(RuntimeError):
    """Raised when voice cloning or synthesis fails."""


def _voice_note_filename(url: str, index: int) -> str:
    source_name = Path(url.split("?", 1)[0]).name
    if source_name and "." in source_name:
        return f"{index:03d}_{source_name}"
    return f"{index:03d}_voice_note.audio"


async def download_voice_notes(urls: list[str], output_dir: Path) -> list[Path]:
    """Download voice note URLs into output_dir and return local paths."""
    output_dir.mkdir(parents=True, exist_ok=True)

    async def download_one(client: httpx.AsyncClient, url: str, index: int) -> Path:
        response = await client.get(url)
        response.raise_for_status()

        destination = output_dir / _voice_note_filename(url, index)
        destination.write_bytes(response.content)
        return destination

    async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
        tasks = [
            download_one(client, url, index)
            for index, url in enumerate(urls, start=1)
        ]
        return await asyncio.gather(*tasks)


def extract_audio_segments(
    audio_paths: list[Path],
    output_dir: Path,
    min_duration_seconds: int = 6,
) -> list[Path]:
    """Convert usable voice notes to clean WAV references for XTTS-v2."""
    output_dir.mkdir(parents=True, exist_ok=True)
    clean_paths: list[Path] = []
    min_duration_ms = min_duration_seconds * 1000

    for index, audio_path in enumerate(audio_paths, start=1):
        audio = AudioSegment.from_file(audio_path)
        if len(audio) < min_duration_ms:
            continue

        clean_audio = (
            audio.set_channels(1)
            .set_frame_rate(24000)
            .set_sample_width(2)
        )
        output_stem = audio_path.stem or f"voice_note_{index}"
        destination = output_dir / f"{index:03d}_{output_stem}.wav"
        clean_audio.export(destination, format="wav")
        clean_paths.append(destination)

    return clean_paths


def _write_manifest(
    output_dir: Path,
    clean_segments: list[Path],
    device: str,
    output_model_path: str,
) -> Path:
    manifest_path = output_dir / "voice_profile.txt"
    relative_segments = [
        os.path.relpath(segment, output_dir)
        for segment in clean_segments
    ]
    lines = [
        "coqui_xtts_v2_voice_profile",
        f"model={XTTS_V2_MODEL}",
        f"device={device}",
        f"output_model_path={output_model_path}",
        "speaker_wavs=",
        *relative_segments,
        "",
    ]
    manifest_path.write_text("\n".join(lines), encoding="utf-8")
    return manifest_path


def _save_voice_profile(
    clean_segments: list[Path],
    output_dir: Path,
    output_model_path: str,
) -> str:
    """Persist cleaned speaker WAVs and write the voice profile manifest."""
    device = "cuda" if torch.cuda.is_available() else "cpu"

    try:
        saved_segments: list[Path] = []
        for index, segment_path in enumerate(clean_segments, start=1):
            destination = output_dir / f"speaker_reference_{index}.wav"
            destination.write_bytes(segment_path.read_bytes())
            saved_segments.append(destination)
    except Exception as exc:
        raise VoiceCloningError("Failed to save speaker reference WAVs.") from exc

    _write_manifest(output_dir, saved_segments, device, output_model_path)
    return str(output_dir)


async def clone_voice_from_paths(
    voice_note_paths: list[str | Path],
    output_model_path: str,
) -> str:
    """Create an XTTS-v2 voice profile from local audio file paths."""
    if len(voice_note_paths) < 5:
        raise ValueError("At least 5 voice notes are required for voice cloning")

    output_dir = Path(output_model_path)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            segment_dir = temp_path / "segments"
            local_paths = [Path(path) for path in voice_note_paths]
            clean_segments = extract_audio_segments(local_paths, segment_dir)
            if not clean_segments:
                raise VoiceCloningError(
                    "No voice notes met the minimum duration requirement."
                )
            return _save_voice_profile(clean_segments, output_dir, output_model_path)
    except VoiceCloningError:
        raise
    except Exception as exc:
        raise VoiceCloningError("Voice cloning failed.") from exc


async def clone_voice(
    voice_note_urls: list[str],
    output_model_path: str,
) -> str:
    """Create an XTTS-v2 voice profile from grandparent voice notes.

    XTTS-v2 performs zero-shot voice cloning from reference WAV files rather
    than training a new model checkpoint. This pipeline downloads voice notes,
    normalizes them into XTTS-ready WAV references, loads XTTS-v2 on the best
    available device, and writes a voice profile directory at output_model_path.
    """
    if len(voice_note_urls) < 5:
        raise ValueError("At least 5 voice notes are required for voice cloning")

    output_dir = Path(output_model_path)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            download_dir = temp_path / "downloads"
            segment_dir = temp_path / "segments"

            downloaded_paths = await download_voice_notes(voice_note_urls, download_dir)
            clean_segments = extract_audio_segments(downloaded_paths, segment_dir)
            if not clean_segments:
                raise VoiceCloningError(
                    "No voice notes met the minimum duration requirement."
                )
            return _save_voice_profile(clean_segments, output_dir, output_model_path)
    except VoiceCloningError:
        raise
    except Exception as exc:
        raise VoiceCloningError("Voice cloning failed.") from exc


async def synthesize_speech(
    text: str,
    model_path: str,
    output_path: str,
    language: str = "hi",
) -> str:
    """Synthesize speech with XTTS-v2 using a saved voice profile."""
    try:
        # Validate required inputs before touching the model or filesystem.
        if not text or not text.strip():
            raise VoiceCloningError("Text is required for speech synthesis.")
        if not model_path or not model_path.strip():
            raise VoiceCloningError("Model path is required for speech synthesis.")
        if not output_path or not output_path.strip():
            raise VoiceCloningError("Output path is required for speech synthesis.")

        profile_dir = Path(model_path)
        manifest_path = profile_dir / "voice_profile.txt"
        if not manifest_path.exists():
            raise VoiceCloningError(f"Voice profile manifest not found: {manifest_path}")

        # Read the manifest and collect speaker WAV references saved by clone_voice().
        speaker_wavs: list[str] = []
        in_speaker_section = False
        for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line == "speaker_wavs=":
                in_speaker_section = True
                continue
            if in_speaker_section:
                speaker_path = Path(line)
                if not speaker_path.is_absolute():
                    speaker_path = profile_dir / speaker_path
                speaker_wavs.append(str(speaker_path))

        if not speaker_wavs:
            raise VoiceCloningError("No speaker WAVs found in voice profile manifest.")

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        device = "cuda" if torch.cuda.is_available() else "cpu"

        def load_and_synthesize() -> None:
            tts_model, _ = _get_tts_model()
            tts_model.tts_to_file(
                text=text,
                speaker_wav=speaker_wavs,
                language=language,
                file_path=output_path,
            )

        # Model loading and synthesis are both heavy synchronous operations.
        await asyncio.to_thread(load_and_synthesize)
        return str(output_path)
    except VoiceCloningError:
        raise
    except Exception as exc:
        raise VoiceCloningError("Speech synthesis failed.") from exc
