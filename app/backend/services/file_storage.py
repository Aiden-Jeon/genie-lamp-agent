"""File storage service using Unity Catalog Volumes."""

import os
from typing import List
from fastapi import UploadFile


class FileStorageService:
    """Manages file uploads to Unity Catalog Volumes."""

    def __init__(self, volume_path: str = "/Volumes/main/genie_lamp/uploads"):
        """
        Initialize file storage service.

        Args:
            volume_path: Base path in Unity Catalog Volume
        """
        # Use local storage if Volumes path is not accessible
        if volume_path.startswith("/Volumes"):
            local_storage = os.path.join(os.getcwd(), "storage", "uploads")
            print(f"Warning: Using local storage at {local_storage} (Unity Catalog Volumes not available locally)")
            self.volume_path = local_storage
        else:
            self.volume_path = volume_path
        os.makedirs(self.volume_path, exist_ok=True)

    async def save_uploads(self, files: List[UploadFile], session_id: str) -> List[str]:
        """
        Save uploaded files to session-specific directory.

        Args:
            files: List of uploaded files
            session_id: Session identifier

        Returns:
            List of saved file paths
        """
        session_dir = f"{self.volume_path}/{session_id}"
        os.makedirs(session_dir, exist_ok=True)

        file_paths = []
        for file in files:
            path = f"{session_dir}/{file.filename}"
            with open(path, 'wb') as f:
                content = await file.read()
                f.write(content)
            file_paths.append(path)

        return file_paths

    def get_session_dir(self, session_id: str) -> str:
        """Get the directory path for a session."""
        return f"{self.volume_path}/{session_id}"

    def create_session_dir(self, session_id: str) -> str:
        """Create and return session directory."""
        session_dir = self.get_session_dir(session_id)
        os.makedirs(session_dir, exist_ok=True)
        return session_dir
