"""Visual Regression - Screenshot comparison for visual testing."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger()


class VisualRegression:
    """
    Visual regression testing by comparing screenshots.

    Workflow:
    1. Capture baseline screenshots
    2. After changes, capture new screenshots
    3. Compare pixel-by-pixel and report differences

    Uses Pillow for image comparison when available,
    falls back to file hash comparison.
    """

    def __init__(self, baselines_dir: str = ".jeph2sworm/visual_baselines"):
        self.baselines_dir = Path(baselines_dir)
        self.baselines_dir.mkdir(parents=True, exist_ok=True)
        self._has_pillow = False

        try:
            from PIL import Image, ImageChops
            self._has_pillow = True
        except ImportError:
            logger.warning("pillow_not_installed", msg="Visual regression limited to hash comparison")

    async def save_baseline(self, name: str, screenshot_path: str) -> Dict[str, Any]:
        """Save a screenshot as a baseline for future comparison."""
        import shutil

        baseline_path = self.baselines_dir / f"{name}.png"
        shutil.copy2(screenshot_path, baseline_path)

        file_hash = self._file_hash(str(baseline_path))
        logger.info("baseline_saved", name=name, path=str(baseline_path))

        return {
            "name": name,
            "path": str(baseline_path),
            "hash": file_hash,
        }

    async def compare(
        self,
        name: str,
        current_screenshot_path: str,
        threshold: float = 0.01,
    ) -> Dict[str, Any]:
        """
        Compare a current screenshot against its baseline.

        Args:
            name: Baseline name
            current_screenshot_path: Path to current screenshot
            threshold: Maximum allowed difference ratio (0.0 = identical, 1.0 = completely different)

        Returns:
            Dict with match result, difference ratio, and diff image path
        """
        baseline_path = self.baselines_dir / f"{name}.png"

        if not baseline_path.exists():
            return {
                "match": False,
                "error": f"No baseline found for '{name}'",
                "suggestion": "Run save_baseline() first",
            }

        if self._has_pillow:
            return await self._compare_pixels(
                str(baseline_path), current_screenshot_path, name, threshold
            )
        else:
            return self._compare_hash(str(baseline_path), current_screenshot_path)

    async def _compare_pixels(
        self,
        baseline_path: str,
        current_path: str,
        name: str,
        threshold: float,
    ) -> Dict[str, Any]:
        """Pixel-by-pixel comparison using Pillow."""
        from PIL import Image, ImageChops

        baseline = Image.open(baseline_path)
        current = Image.open(current_path)

        # Resize if dimensions differ
        if baseline.size != current.size:
            current = current.resize(baseline.size)

        # Calculate difference
        diff = ImageChops.difference(baseline.convert("RGB"), current.convert("RGB"))

        # Calculate difference ratio
        diff_pixels = sum(1 for pixel in diff.getdata() if sum(pixel) > 30)
        total_pixels = baseline.size[0] * baseline.size[1]
        diff_ratio = diff_pixels / total_pixels if total_pixels > 0 else 1.0

        is_match = diff_ratio <= threshold

        # Save diff image
        diff_path = self.baselines_dir / f"{name}_diff.png"
        diff.save(str(diff_path))

        result = {
            "match": is_match,
            "diff_ratio": round(diff_ratio, 6),
            "diff_pixels": diff_pixels,
            "total_pixels": total_pixels,
            "threshold": threshold,
            "diff_image": str(diff_path),
            "baseline_size": baseline.size,
            "current_size": Image.open(current_path).size,
        }

        if not is_match:
            logger.warning(
                "visual_regression_detected",
                name=name,
                diff_ratio=round(diff_ratio, 4),
            )

        return result

    def _compare_hash(self, baseline_path: str, current_path: str) -> Dict[str, Any]:
        """Simple hash-based comparison (fallback when Pillow unavailable)."""
        baseline_hash = self._file_hash(baseline_path)
        current_hash = self._file_hash(current_path)
        is_match = baseline_hash == current_hash

        return {
            "match": is_match,
            "method": "hash",
            "baseline_hash": baseline_hash,
            "current_hash": current_hash,
        }

    def _file_hash(self, filepath: str) -> str:
        """Calculate SHA-256 hash of a file."""
        sha = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha.update(chunk)
        return sha.hexdigest()

    def list_baselines(self) -> List[Dict[str, Any]]:
        """List all saved baselines."""
        baselines = []
        for f in sorted(self.baselines_dir.glob("*.png")):
            if not f.name.endswith("_diff.png"):
                baselines.append({
                    "name": f.stem,
                    "path": str(f),
                    "size_bytes": f.stat().st_size,
                    "created": f.stat().st_mtime,
                })
        return baselines

    async def update_baseline(self, name: str, new_screenshot_path: str) -> Dict[str, Any]:
        """Update a baseline with a new screenshot (accept current as new baseline)."""
        return await self.save_baseline(name, new_screenshot_path)

    def delete_baseline(self, name: str) -> bool:
        """Delete a baseline."""
        baseline_path = self.baselines_dir / f"{name}.png"
        diff_path = self.baselines_dir / f"{name}_diff.png"

        deleted = False
        if baseline_path.exists():
            baseline_path.unlink()
            deleted = True
        if diff_path.exists():
            diff_path.unlink()

        return deleted
