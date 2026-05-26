"""
Object storage for generated PDFs.

On Vercel, `/tmp` is ephemeral and capacity-limited, so a memoir PDF written
locally won't survive or scale. When an object store is configured (S3 or
Cloudflare R2), `store_pdf()` uploads the file and returns a time-limited signed
URL. When it isn't configured, it returns the local path unchanged — so local
dev and tests keep working with zero setup.

Config (all optional; absence → local-path fallback):
  STORAGE_BUCKET          bucket name
  STORAGE_ENDPOINT_URL    S3 endpoint (set this to the R2 endpoint for Cloudflare R2)
  STORAGE_REGION          region (default us-east-1)
  AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY   credentials (standard AWS env vars)
  STORAGE_SIGNED_URL_TTL  signed URL lifetime in seconds (default 604800 = 7 days)
"""

import logging
import os

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    return bool(os.environ.get("STORAGE_BUCKET"))


def _client():
    import boto3  # lazy — only needed when storage is configured

    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("STORAGE_ENDPOINT_URL") or None,
        region_name=os.environ.get("STORAGE_REGION", "us-east-1"),
    )


def store_pdf(local_path: str, key: str | None = None) -> str:
    """Upload a PDF and return a signed URL, or return local_path if storage isn't
    configured (or upload fails — we never lose the locally-generated file)."""
    if not is_configured():
        return local_path

    bucket = os.environ["STORAGE_BUCKET"]
    key = key or f"books/{os.path.basename(local_path)}"
    ttl = int(os.environ.get("STORAGE_SIGNED_URL_TTL", str(7 * 24 * 3600)))

    try:
        client = _client()
        with open(local_path, "rb") as f:
            client.upload_fileobj(f, bucket, key, ExtraArgs={"ContentType": "application/pdf"})
        url = client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=ttl
        )
        logger.info("Uploaded PDF to s3://%s/%s", bucket, key)
        return url
    except Exception:
        logger.exception("PDF upload failed — falling back to local path %s", local_path)
        return local_path
