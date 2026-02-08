"""Screen Recorder - Record browser sessions for debugging and review."""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()


class ScreenRecorder:
    """
    Records browser sessions as video for:
    - Test run documentation
    - Bug reproduction
    - User flow verification
    - Demo generation

    Uses Playwright's built-in video recording capabilities.
    """

    def __init__(self, output_dir: str = ".jeph2sworm/recordings"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._active_recordings: Dict[str, Dict[str, Any]] = {}

    async def start_recording(
        self,
        context: Any,
        name: str = "recording",
        video_size: Optional[Dict[str, int]] = None,
    ) -> str:
        """
        Start recording a browser context.

        Must be called before creating pages in the context,
        or use a context created with record_video_dir set.

        Args:
            context: Playwright browser context
            name: Recording name/label
            video_size: Optional dict with 'width' and 'height'

        Returns:
            Recording ID for stop_recording()
        """
        recording_id = f"{name}_{int(time.time())}"
        recording_dir = self.output_dir / recording_id
        recording_dir.mkdir(parents=True, exist_ok=True)

        self._active_recordings[recording_id] = {
            "name": name,
            "context": context,
            "output_dir": str(recording_dir),
            "started_at": time.time(),
            "video_size": video_size or {"width": 1280, "height": 720},
        }

        logger.info("recording_started", recording_id=recording_id, output_dir=str(recording_dir))
        return recording_id

    async def stop_recording(self, recording_id: str) -> Dict[str, Any]:
        """
        Stop a recording and return the video file path.

        Note: Playwright saves videos when the context is closed,
        so we close the context and find the video file.
        """
        recording = self._active_recordings.pop(recording_id, None)
        if not recording:
            return {"error": f"Recording {recording_id} not found"}

        output_dir = recording["output_dir"]
        duration = time.time() - recording["started_at"]

        # Get all pages and their video paths
        context = recording["context"]
        video_paths: List[str] = []

        try:
            for page in context.pages:
                video = page.video
                if video:
                    path = await video.path()
                    if path:
                        video_paths.append(str(path))
        except Exception as e:
            logger.warning("video_path_retrieval_failed", error=str(e))

        logger.info(
            "recording_stopped",
            recording_id=recording_id,
            duration_seconds=round(duration, 1),
            videos=len(video_paths),
        )

        return {
            "recording_id": recording_id,
            "duration_seconds": round(duration, 1),
            "output_dir": output_dir,
            "video_paths": video_paths,
        }

    async def create_recording_context(
        self,
        browser: Any,
        name: str = "recording",
        video_size: Optional[Dict[str, int]] = None,
    ) -> Any:
        """
        Create a new browser context with video recording enabled.

        Returns the Playwright browser context.
        """
        size = video_size or {"width": 1280, "height": 720}
        recording_dir = self.output_dir / f"{name}_{int(time.time())}"
        recording_dir.mkdir(parents=True, exist_ok=True)

        context = await browser.new_context(
            record_video_dir=str(recording_dir),
            record_video_size=size,
            viewport=size,
        )

        recording_id = recording_dir.name
        self._active_recordings[recording_id] = {
            "name": name,
            "context": context,
            "output_dir": str(recording_dir),
            "started_at": time.time(),
            "video_size": size,
        }

        return context

    def list_recordings(self) -> List[Dict[str, Any]]:
        """List all saved recordings."""
        recordings = []
        for d in sorted(self.output_dir.iterdir()):
            if d.is_dir():
                videos = list(d.glob("*.webm")) + list(d.glob("*.mp4"))
                recordings.append({
                    "id": d.name,
                    "path": str(d),
                    "videos": [str(v) for v in videos],
                    "total_size_bytes": sum(v.stat().st_size for v in videos),
                    "created": d.stat().st_mtime,
                })
        return recordings

    def cleanup(self, max_age_hours: int = 48) -> int:
        """Remove recordings older than max_age_hours."""
        import shutil

        cutoff = time.time() - (max_age_hours * 3600)
        removed = 0
        for d in self.output_dir.iterdir():
            if d.is_dir() and d.stat().st_mtime < cutoff:
                shutil.rmtree(d)
                removed += 1
        return removed

    @property
    def active_count(self) -> int:
        return len(self._active_recordings)
