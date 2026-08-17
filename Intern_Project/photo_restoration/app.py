import os
import tempfile
from contextlib import asynccontextmanager

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl

from restore import restore_photo


class RestoreRequest(BaseModel):
    """Request body for the restore endpoint."""

    photo_url: HttpUrl


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup and shutdown hooks for the service."""
    print("Photo restoration service ready")
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    html_path = "/app/index.html"
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"status": "ok"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/restore")
async def restore_endpoint(
    request: RestoreRequest,
    background_tasks: BackgroundTasks,
):
    """Download a photo, restore it, and return the restored file."""
    input_path = None
    output_path = None

    try:
        # Download the source image from the supplied URL.
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            response = await client.get(str(request.photo_url))
            response.raise_for_status()

        # Save the downloaded image to a temporary file for restore_photo.
        with tempfile.NamedTemporaryFile(
            suffix=".img",
            prefix="source_",
            delete=False,
        ) as input_file:
            input_path = input_file.name
            input_file.write(response.content)

        # Run the photo restoration pipeline from restore.py without blocking
        # the async event loop.
        output_path = await run_in_threadpool(restore_photo, input_path)

        # Delete the temporary input and output files after FileResponse sends.
        background_tasks.add_task(_delete_file, input_path)
        background_tasks.add_task(_delete_file, output_path)

        return FileResponse(
            output_path,
            media_type="image/png",
            filename="restored.png",
            background=background_tasks,
        )

    except httpx.HTTPStatusError as exc:
        _delete_file(input_path)
        raise HTTPException(
            status_code=400,
            detail=f"Failed to download image: HTTP {exc.response.status_code}",
        ) from exc
    except httpx.HTTPError as exc:
        _delete_file(input_path)
        raise HTTPException(
            status_code=400,
            detail=f"Failed to download image: {exc}",
        ) from exc
    except Exception as exc:
        _delete_file(input_path)
        _delete_file(output_path)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restore image: {exc}",
        ) from exc


def _delete_file(path: str | None) -> None:
    """Remove a temporary file if it exists."""
    if not path:
        return

    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass
