"""
File service for handling configuration file uploads and temporary storage.

Manages multipart file uploads and prepares configuration directories for Batfish.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import List
from fastapi import UploadFile

logger = logging.getLogger(__name__)


class FileService:
    """
    Service for managing configuration file uploads and temporary storage.

    Constitutional compliance:
    - Principle I: Batfish-First Integration - Files are stored for Batfish processing only
    - Principle V: Observability - Structured logging for all file operations

    Security measures:
    - File size limits (10 MB per file, 100 MB total)
    - Filename sanitization (alphanumeric, hyphens, underscores, dots only)
    - Path traversal prevention
    """

    # Security limits
    MAX_FILE_SIZE_MB = 10
    MAX_TOTAL_SIZE_MB = 100
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    MAX_TOTAL_SIZE_BYTES = MAX_TOTAL_SIZE_MB * 1024 * 1024

    def __init__(self, temp_dir: str = "./uploads"):
        """
        Initialize file service with temporary upload directory.

        Args:
            temp_dir: Temporary directory for uploaded files
        """
        self.temp_dir = Path(temp_dir).resolve()  # Resolve to absolute path
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info("FileService initialized", extra={"temp_dir": str(self.temp_dir)})

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename

        Raises:
            ValueError: If filename is invalid
        """
        import re

        if not filename or not filename.strip():
            raise ValueError("Filename cannot be empty")

        # Remove directory components (path traversal prevention)
        filename = os.path.basename(filename)

        # Allow only alphanumeric, hyphens, underscores, and dots
        if not re.match(r'^[a-zA-Z0-9_.-]+$', filename):
            raise ValueError(f"Invalid filename: {filename}. Only alphanumeric, hyphens, underscores, and dots allowed.")

        # Prevent hidden files
        if filename.startswith('.'):
            raise ValueError(f"Hidden files not allowed: {filename}")

        return filename

    async def save_uploaded_files(
        self,
        snapshot_name: str,
        files: List[UploadFile]
    ) -> Path:
        """
        Save uploaded configuration files to temporary directory.

        Args:
            snapshot_name: Snapshot name (used for directory name)
            files: List of uploaded files

        Returns:
            Path to directory containing saved files

        Raises:
            ValueError: If no files provided, snapshot_name is invalid, or security checks fail
            IOError: If file save operation fails
        """
        if not files:
            raise ValueError("No configuration files provided")

        if not snapshot_name or not snapshot_name.strip():
            raise ValueError("Snapshot name is required")

        # Create snapshot-specific directory
        snapshot_dir = (self.temp_dir / snapshot_name).resolve()

        # Security: Ensure snapshot_dir is within temp_dir (prevent path traversal)
        if not str(snapshot_dir).startswith(str(self.temp_dir)):
            raise ValueError(f"Invalid snapshot name: path traversal detected")

        snapshot_dir.mkdir(parents=True, exist_ok=True)

        # Create configs subdirectory (required by Batfish)
        # Batfish expects: snapshot_name/configs/ directory structure
        configs_dir = snapshot_dir / "configs"
        configs_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Saving uploaded files",
            extra={
                "snapshot": snapshot_name,
                "file_count": len(files),
                "directory": str(snapshot_dir)
            }
        )

        saved_files = []
        total_size = 0

        try:
            for upload_file in files:
                if not upload_file.filename:
                    logger.warning("Skipping file with no filename")
                    continue

                # Sanitize filename (security)
                sanitized_filename = self._sanitize_filename(upload_file.filename)

                # Read file content
                content = await upload_file.read()
                file_size = len(content)

                # Security: Check individual file size
                if file_size > self.MAX_FILE_SIZE_BYTES:
                    raise ValueError(
                        f"File {sanitized_filename} exceeds maximum size limit "
                        f"({self.MAX_FILE_SIZE_MB} MB). File size: {file_size / 1024 / 1024:.2f} MB"
                    )

                # Security: Check total upload size
                total_size += file_size
                if total_size > self.MAX_TOTAL_SIZE_BYTES:
                    raise ValueError(
                        f"Total upload size exceeds maximum limit "
                        f"({self.MAX_TOTAL_SIZE_MB} MB). Current total: {total_size / 1024 / 1024:.2f} MB"
                    )

                # Save file to configs subdirectory
                file_path = configs_dir / sanitized_filename

                # Security: Ensure file_path is within configs_dir
                file_path_resolved = file_path.resolve()
                if not str(file_path_resolved).startswith(str(configs_dir)):
                    raise ValueError(f"Invalid file path: path traversal detected")

                with open(file_path, "wb") as f:
                    f.write(content)

                saved_files.append(file_path)
                logger.debug(
                    "File saved",
                    extra={
                        "file_name": sanitized_filename,
                        "size_bytes": file_size,
                        "file_path": str(file_path)
                    }
                )

            logger.info(
                "All files saved successfully",
                extra={
                    "snapshot": snapshot_name,
                    "files_saved": len(saved_files)
                }
            )

            return snapshot_dir

        except Exception as e:
            # Cleanup on error
            logger.error(
                "Error saving files, cleaning up",
                extra={"snapshot": snapshot_name, "error": str(e)},
                exc_info=True
            )
            self.cleanup_snapshot_dir(snapshot_name)
            raise IOError(f"Failed to save configuration files: {str(e)}") from e

    def cleanup_snapshot_dir(self, snapshot_name: str) -> None:
        """
        Remove temporary snapshot directory and all its contents.

        Args:
            snapshot_name: Snapshot name (directory name to remove)
        """
        snapshot_dir = self.temp_dir / snapshot_name
        if snapshot_dir.exists():
            try:
                shutil.rmtree(snapshot_dir)
                logger.info(
                    "Snapshot directory cleaned up",
                    extra={"snapshot": snapshot_name, "directory": str(snapshot_dir)}
                )
            except Exception as e:
                logger.error(
                    "Failed to cleanup snapshot directory",
                    extra={"snapshot": snapshot_name, "error": str(e)},
                    exc_info=True
                )

    def get_uploaded_file_count(self, snapshot_name: str) -> int:
        """
        Count uploaded configuration files for a snapshot.

        Args:
            snapshot_name: Snapshot name

        Returns:
            Number of files in snapshot configs directory
        """
        configs_dir = self.temp_dir / snapshot_name / "configs"
        if not configs_dir.exists():
            return 0

        file_count = len([f for f in configs_dir.iterdir() if f.is_file()])
        logger.debug(
            "Counted uploaded files",
            extra={"snapshot": snapshot_name, "file_count": file_count}
        )
        return file_count


# Global file service instance
_file_service: FileService = None


def get_file_service(temp_dir: str = "./uploads") -> FileService:
    """
    Get or create global file service instance (singleton pattern).

    Args:
        temp_dir: Temporary upload directory

    Returns:
        FileService instance
    """
    global _file_service
    if _file_service is None:
        _file_service = FileService(temp_dir=temp_dir)
    return _file_service
