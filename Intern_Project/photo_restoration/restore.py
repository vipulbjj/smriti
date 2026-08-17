"""
Photo restoration: DeOldify colorization + Swin2SR super-resolution.

Pipeline:
  1. RGB load + contrast/brightness normalization
  2. Pre-colorization preprocessing
  3. DeOldify artistic colorization (B&W / faded photos)
  4. 4x super-resolution (Swin2SR)
  5. Sharpen + color + contrast polish
"""

from __future__ import annotations

import logging
import os
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEVICE = torch.device("cpu")

DEOLDIFY_ROOT = Path(os.environ.get("DEOLDIFY_ROOT", str(Path(__file__).resolve().parent)))
DEOLDIFY_RENDER_FACTOR = int(os.environ.get("DEOLDIFY_RENDER_FACTOR", "35"))

# Super-resolution (transformers Swin2SR, 4x real-world).
SWIN2SR_MODEL_ID = "caidas/swin2SR-realworld-sr-x4-64-bsrgan-psnr"

GRAYSCALE_CHANNEL_SPREAD_THRESHOLD = 8.0
FADED_SATURATION_THRESHOLD = 22.0

MAX_UPSCALE_INPUT_SIDE = int(os.environ.get("RESTORE_SR_MAX_INPUT_SIDE", "512"))
ENABLE_UPSCALING = os.environ.get("RESTORE_ENABLE_UPSCALING", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Module-level model handles
# ---------------------------------------------------------------------------

_swin2sr_model = None
_swin2sr_processor = None
_swin2sr_load_error: str | None = None
_deoldify_colorizer = None
_deoldify_load_error: str | None = None


# ---------------------------------------------------------------------------
# Startup loading
# ---------------------------------------------------------------------------


def _log(msg: str) -> None:
    print(f"[restore] {msg}", flush=True)


def _init_deoldify_colorizer() -> None:
    global _deoldify_colorizer, _deoldify_load_error

    models_dir = DEOLDIFY_ROOT / "models"
    weight_file = models_dir / "ColorizeArtistic_gen.pth"
    if not weight_file.is_file():
        _deoldify_load_error = f"DeOldify weights not found at {weight_file}"
        _log(_deoldify_load_error)
        return

    try:
        from deoldify.visualize import get_image_colorizer

        _deoldify_colorizer = get_image_colorizer(
            root_folder=DEOLDIFY_ROOT,
            artistic=True,
            render_factor=DEOLDIFY_RENDER_FACTOR,
        )
        _log(
            f"DeOldify colorizer ready (artistic, render_factor={DEOLDIFY_RENDER_FACTOR})."
        )
    except Exception as exc:
        _deoldify_load_error = str(exc)
        _log(f"DeOldify load failed: {exc}")


def _init_upscaler() -> None:
    global _swin2sr_model, _swin2sr_processor, _swin2sr_load_error
    if not ENABLE_UPSCALING:
        _log("Swin2SR upscaling disabled, skipping model load.")
        return
    try:
        _log(f"Loading Swin2SR 4x upscaler: {SWIN2SR_MODEL_ID} ...")
        from transformers import AutoImageProcessor, Swin2SRForImageSuperResolution

        _swin2sr_processor = AutoImageProcessor.from_pretrained(SWIN2SR_MODEL_ID)
        _swin2sr_model = Swin2SRForImageSuperResolution.from_pretrained(SWIN2SR_MODEL_ID)
        _swin2sr_model.to(DEVICE)
        _swin2sr_model.eval()
        _log("Swin2SR upscaler ready.")
    except Exception as exc:
        _swin2sr_load_error = str(exc)
        _log(f"Swin2SR load failed: {exc}")


_log("Initializing restoration models (CPU)...")
_init_deoldify_colorizer()
_init_upscaler()
_log("Model initialization complete.")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def restore_photo(image_path: str) -> str:
    """
    Restore a vintage or faded photo: enhance, colorize, upscale, polish.

    Args:
        image_path: Path to the source image file.

    Returns:
        Path to a temporary PNG containing the restored image.
    """
    try:
        input_path = Path(image_path)
        if not input_path.is_file():
            raise FileNotFoundError(f"Input image not found: {image_path}")

        _log(f"Step 1/7: Loading image {input_path.name}")
        with Image.open(input_path) as image:
            working = image.convert("RGB")

        _log("Step 2/7: Adjusting contrast and brightness")
        working = _enhance_contrast_brightness(working)

        _log("Step 2b/7: Pre-colorization preprocessing")
        working = ImageOps.autocontrast(working, cutoff=2)
        working = working.filter(ImageFilter.MedianFilter(size=3))
        working = ImageEnhance.Brightness(working).enhance(1.1)

        _log("Step 3/7: Removing scratches and damage (OpenCV inpainting)")
        working = _remove_scratches(working)

        if _needs_colorization(working):
            if _deoldify_colorizer is not None:
                _log("Step 4/7: Colorizing (DeOldify artistic)")
                working = _colorize_deoldify(working)
            else:
                detail = _deoldify_load_error or "DeOldify colorizer is not loaded."
                _log(f"Step 4/7: Skipping colorization ({detail})")
        else:
            _log("Step 4/7: Skipping colorization (already colorful)")

        if ENABLE_UPSCALING:
            _log("Step 5/7: AI 4x super-resolution (Swin2SR)")
            working = _upscale_swin2sr(working)
        else:
            _log("Step 5/7: Skipping upscaling (RESTORE_ENABLE_UPSCALING not set)")

        _log("Step 6/7: Sharpening and final polish")
        working = working.filter(ImageFilter.SHARPEN)
        working = working.filter(ImageFilter.SHARPEN)
        working = ImageEnhance.Color(working).enhance(1.3)
        working = ImageEnhance.Contrast(working).enhance(1.1)

        _log("Step 7/7: Saving result")
        output_file = tempfile.NamedTemporaryFile(
            suffix=".png",
            prefix="restored_",
            delete=False,
        )
        output_path = output_file.name
        output_file.close()
        working.save(output_path, format="PNG")
        _log(f"Restoration done: {output_path}")
        return output_path

    except Exception as exc:
        raise RuntimeError(f"Photo restoration failed: {exc}") from exc


# ---------------------------------------------------------------------------
# DeOldify colorization
# ---------------------------------------------------------------------------


def _colorize_deoldify(image: Image.Image) -> Image.Image:
    assert _deoldify_colorizer is not None

    t0 = time.perf_counter()
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            temp_path = Path(tmp.name)
            image.save(temp_path, format="PNG")

        result = _deoldify_colorizer.get_transformed_image(
            temp_path,
            render_factor=DEOLDIFY_RENDER_FACTOR,
            post_process=True,
            watermarked=False,
        )
        _log(f"DeOldify colorization took {time.perf_counter() - t0:.1f}s")
        return result.convert("RGB")
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Pre-processing
# ---------------------------------------------------------------------------


def _enhance_contrast_brightness(image: Image.Image) -> Image.Image:
    """Auto contrast + gentle brightness normalization."""
    img = ImageEnhance.Contrast(image).enhance(1.18)
    img = ImageEnhance.Brightness(img).enhance(1.05)
    img = ImageEnhance.Color(img).enhance(1.08)
    return img


def _remove_scratches(image: Image.Image) -> Image.Image:
    """
    Detect and remove scratches, dust, and damage using OpenCV inpainting.

    Steps:
    1. Convert to grayscale numpy array
    2. Detect damage mask using adaptive thresholding + morphological operations:
       - Find very bright streaks (scratches) using threshold > 245
       - Find very dark spots (dust) using threshold < 10
       - Combine both masks
       - Dilate slightly to cover scratch edges (kernel 2x2, iterations=1)
    3. Apply cv2.inpaint with INPAINT_TELEA method, inpaintRadius=3
    4. Return as PIL RGB image
    """
    rgb = np.asarray(image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    bright_mask = (gray > 245).astype(np.uint8) * 255
    dark_mask = (gray < 10).astype(np.uint8) * 255
    damage_mask = cv2.bitwise_or(bright_mask, dark_mask)

    kernel = np.ones((2, 2), np.uint8)
    damage_mask = cv2.dilate(damage_mask, kernel, iterations=1)

    inpainted = cv2.inpaint(
        rgb,
        damage_mask,
        inpaintRadius=3,
        flags=cv2.INPAINT_TELEA,
    )
    return Image.fromarray(inpainted, mode="RGB")


def _needs_colorization(image: Image.Image) -> bool:
    if image.mode in ("L", "1", "LA", "P"):
        return True

    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    spread = max(
        float(np.std(rgb[:, :, 0] - rgb[:, :, 1])),
        float(np.std(rgb[:, :, 1] - rgb[:, :, 2])),
        float(np.std(rgb[:, :, 0] - rgb[:, :, 2])),
    )
    if spread < GRAYSCALE_CHANNEL_SPREAD_THRESHOLD:
        return True

    hsv = _rgb_to_hsv(rgb)
    mean_sat = float(np.mean(hsv[:, :, 1]))
    return mean_sat < FADED_SATURATION_THRESHOLD


def _rgb_to_hsv(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb[:, :, 0] / 255.0, rgb[:, :, 1] / 255.0, rgb[:, :, 2] / 255.0
    maxc = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    v = maxc
    delta = maxc - minc
    s = np.where(maxc > 1e-6, delta / maxc, 0.0)

    rc = np.where(delta > 1e-6, (maxc - r) / delta, 0.0)
    gc = np.where(delta > 1e-6, (maxc - g) / delta, 0.0)
    bc = np.where(delta > 1e-6, (maxc - b) / delta, 0.0)

    h = np.zeros_like(maxc)
    h = np.where((maxc == r) & (delta > 1e-6), (bc - gc), h)
    h = np.where((maxc == g) & (delta > 1e-6), 2.0 + (rc - bc), h)
    h = np.where((maxc == b) & (delta > 1e-6), 4.0 + (gc - rc), h)
    h = (h / 6.0) % 1.0

    return np.stack([h, s, v], axis=-1)


def _resize_max_side(image: Image.Image, max_side: int) -> Image.Image:
    w, h = image.size
    if max(w, h) <= max_side:
        return image
    scale = max_side / float(max(w, h))
    return image.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)


# ---------------------------------------------------------------------------
# Super-resolution (Swin2SR)
# ---------------------------------------------------------------------------


def _upscale_swin2sr(image: Image.Image) -> Image.Image:
    assert _swin2sr_model is not None and _swin2sr_processor is not None

    work = _resize_max_side(image, MAX_UPSCALE_INPUT_SIDE)
    t0 = time.perf_counter()

    inputs = _swin2sr_processor(images=work, return_tensors="pt")
    pixel_values = inputs.pixel_values.to(DEVICE)

    with torch.inference_mode():
        outputs = _swin2sr_model(pixel_values)

    output = outputs.reconstruction.squeeze().float().cpu().clamp(0, 1).numpy()
    output = np.moveaxis(output, 0, -1)
    output = (output * 255.0).round().astype(np.uint8)
    result = Image.fromarray(output, mode="RGB")

    _log(f"Swin2SR upscale took {time.perf_counter() - t0:.1f}s ({work.size} -> {result.size})")
    return result
