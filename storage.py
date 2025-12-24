"""Storage helpers were removed.

The S3 sync feature was reverted per project request. This module is a placeholder
to avoid import errors; no-op functions are provided.
"""
def download_db_from_s3(local_path: str) -> bool:  # pragma: no cover
    return False


def upload_db_to_s3(local_path: str) -> bool:  # pragma: no cover
    return False
