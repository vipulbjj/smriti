---
title: Photo Restoration Service
emoji: 🖼️
colorFrom: yellow
colorTo: pink
sdk: docker
pinned: false
---

# Photo Restoration Service

FastAPI microservice that restores vintage or faded photos from a public URL.

## Pipeline

1. Contrast and brightness normalization
2. **Colorize** (only for B&W or washed-out images), fallback chain:
   - Stable Diffusion 2 img2img (`stabilityai/stable-diffusion-2-base`)
   - ControlNet colorization (`neurallove/controlnet-sd21-colorization-diffusers`)
   - DDColor (`piddnad/ddcolor_modelscope`)
3. **4× super-resolution** with Swin2SR (`caidas/swin2SR-realworld-sr-x4-64-bsrgan-psnr`)
4. Sharpen and light denoise

Models load once at import time. Only the first successful colorizer in the chain is kept in memory.

## Restore a Photo

```json
{
  "photo_url": "https://example.com/photo.jpg"
}
```

```bash
curl -X POST "https://your-space-url.hf.space/restore" \
  -H "Content-Type: application/json" \
  -d '{"photo_url": "https://example.com/photo.jpg"}' \
  --output restored.png
```

## CPU / Hugging Face Spaces

The Docker image sets `RESTORE_SKIP_SD=1` so CPU Spaces use **DDColor + Swin2SR** (stable RAM and startup). Remove that env var on a GPU Space to enable the full SD → ControlNet → DDColor chain.

| Variable | Default | Purpose |
|----------|---------|---------|
| `RESTORE_SKIP_SD` | `1` in Docker | Skip SD/ControlNet loaders |
| `RESTORE_COLORIZER` | `auto` | Force `sd_img2img`, `controlnet`, or `ddcolor` |
| `RESTORE_SD_MAX_SIDE` | `384` | Max side for SD colorization |
| `RESTORE_SD_STEPS` | `12` | SD inference steps |
| `RESTORE_SR_MAX_INPUT_SIDE` | `512` | Max side fed to Swin2SR |

## Tech Stack

- FastAPI + uvicorn
- PyTorch (CPU), diffusers, transformers
- DDColor (vendored `ddcolor/` + `basicsr/`)
- Swin2SR 4× real-world super-resolution
