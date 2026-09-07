# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_video_ai_creator/src/cache_manager.py"
# purpose: "Asset and Rendered Video Cache Manager for DNK-MEDIA-001 (Phase 4)."
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

"""
Cache Manager for dnk_video_ai_creator.
Provides deterministic asset caching, cache key computation, CDN URL formatting,
and cache invalidation mechanisms.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class CacheEntry:
    """Represents a cached media render entry."""
    key: str
    file_path: str
    cdn_url: str
    file_size_bytes: int
    mime_type: str
    created_at: float
    metadata: Dict[str, Any]


class CacheManager:
    """
    Deterministic Cache Manager for rendered media files and assets.
    Enforces security boundary (no path traversal) and provides CDN path resolution.
    """

    def __init__(
        self,
        cache_dir: str = "./cache/media_renders",
        cdn_base_url: str = "https://cdn.dnk-os.internal/media",
    ) -> None:
        """
        Initialize the CacheManager.

        Args:
            cache_dir: Relative or absolute path for cache storage.
            cdn_base_url: Base URL for CDN asset resolution.
        """
        self.cache_dir = Path(cache_dir).resolve()
        self.cdn_base_url = cdn_base_url.rstrip("/")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self.cache_dir / "_cache_index.json"
        self._index: Dict[str, Dict[str, Any]] = self._load_index()

    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """Load persistent cache index if available."""
        if self._index_file.exists():
            try:
                with open(self._index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_index(self) -> None:
        """Persist cache index to disk."""
        try:
            with open(self._index_file, "w", encoding="utf-8") as f:
                json.dump(self._index, f, indent=2)
        except Exception:
            pass

    @staticmethod
    def compute_key(payload: Dict[str, Any] | str) -> str:
        """
        Compute deterministic SHA-256 cache key from payload dictionary or string.

        Args:
            payload: Composition dictionary, template configuration, or string.

        Returns:
            64-character hexadecimal SHA-256 hash.
        """
        if isinstance(payload, dict):
            serialized = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
        else:
            serialized = str(payload)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get_cdn_url(self, key: str, extension: str = "mp4") -> str:
        """Generate CDN-ready URL for a given cache key."""
        clean_ext = extension.lstrip(".")
        return f"{self.cdn_base_url}/{key}.{clean_ext}"

    def get_file_path(self, key: str, extension: str = "mp4") -> Path:
        """
        Resolve cache file path securely.
        Enforces security boundary preventing directory traversal.
        """
        clean_ext = extension.lstrip(".")
        safe_filename = f"{key}.{clean_ext}"
        target_path = (self.cache_dir / safe_filename).resolve()

        # Strict security boundary check
        if not str(target_path).startswith(str(self.cache_dir)):
            raise ValueError(f"Path traversal violation detected for key: {key}")

        return target_path

    def get(self, key: str, extension: str = "mp4") -> Optional[CacheEntry]:
        """
        Retrieve a cached entry if it exists on disk and in index.

        Args:
            key: SHA-256 cache key.
            extension: Expected file extension.

        Returns:
            CacheEntry if valid and present, None otherwise.
        """
        file_path = self.get_file_path(key, extension)
        if not file_path.exists():
            if key in self._index:
                del self._index[key]
                self._save_index()
            return None

        entry_data = self._index.get(key)
        if not entry_data:
            # Reconstruct from disk
            size = file_path.stat().st_size
            cdn_url = self.get_cdn_url(key, extension)
            mime = "video/mp4" if extension == "mp4" else ("image/gif" if extension == "gif" else "application/octet-stream")
            return CacheEntry(
                key=key,
                file_path=str(file_path),
                cdn_url=cdn_url,
                file_size_bytes=size,
                mime_type=mime,
                created_at=file_path.stat().st_mtime,
                metadata={},
            )

        return CacheEntry(
            key=key,
            file_path=str(file_path),
            cdn_url=entry_data.get("cdn_url", self.get_cdn_url(key, extension)),
            file_size_bytes=file_path.stat().st_size,
            mime_type=entry_data.get("mime_type", "video/mp4"),
            created_at=entry_data.get("created_at", file_path.stat().st_mtime),
            metadata=entry_data.get("metadata", {}),
        )

    def put(
        self,
        key: str,
        source_file_path: str | Path,
        extension: str = "mp4",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CacheEntry:
        """
        Store a rendered output file in cache.

        Args:
            key: SHA-256 cache key.
            source_file_path: Path to rendered source file.
            extension: Output file extension.
            metadata: Additional metadata dictionary.

        Returns:
            Created CacheEntry.
        """
        src = Path(source_file_path).resolve()
        if not src.exists():
            raise FileNotFoundError(f"Source file for cache does not exist: {source_file_path}")

        dest = self.get_file_path(key, extension)
        if src != dest:
            shutil.copy2(src, dest)

        cdn_url = self.get_cdn_url(key, extension)
        mime = "video/mp4" if extension == "mp4" else ("image/gif" if extension == "gif" else "application/octet-stream")
        stat = dest.stat()

        entry_dict = {
            "key": key,
            "cdn_url": cdn_url,
            "file_size_bytes": stat.st_size,
            "mime_type": mime,
            "created_at": stat.st_mtime,
            "metadata": metadata or {},
        }
        self._index[key] = entry_dict
        self._save_index()

        return CacheEntry(
            key=key,
            file_path=str(dest),
            cdn_url=cdn_url,
            file_size_bytes=stat.st_size,
            mime_type=mime,
            created_at=stat.st_mtime,
            metadata=metadata or {},
        )

    def invalidate(self, key: str, extension: str = "mp4") -> bool:
        """
        Invalidate a single cache entry.

        Returns:
            True if entry existed and was removed, False otherwise.
        """
        target_path = self.get_file_path(key, extension)
        removed = False
        if target_path.exists():
            target_path.unlink()
            removed = True

        if key in self._index:
            del self._index[key]
            self._save_index()
            removed = True

        return removed

    def invalidate_template(self, template_id: str) -> int:
        """
        Invalidate all cached items associated with a specific template ID.

        Returns:
            Number of invalidated entries.
        """
        keys_to_remove = []
        for k, entry in self._index.items():
            if entry.get("metadata", {}).get("template_id") == template_id:
                keys_to_remove.append(k)

        count = 0
        for k in keys_to_remove:
            if self.invalidate(k):
                count += 1
        return count

    def clear(self) -> int:
        """
        Purge all cached files and reset index.

        Returns:
            Count of deleted items.
        """
        count = 0
        for item in self.cache_dir.iterdir():
            if item.is_file() and item != self._index_file:
                try:
                    item.unlink()
                    count += 1
                except Exception:
                    pass
        self._index.clear()
        self._save_index()
        return count

    def get_stats(self) -> Dict[str, Any]:
        """Get cache storage statistics."""
        total_size = 0
        if self.cache_dir.exists():
            for item in self.cache_dir.iterdir():
                if item.is_file() and item != self._index_file:
                    total_size += item.stat().st_size
        return {
            "cached_entries": len(self._index),
            "total_size_bytes": total_size,
            "cache_dir": str(self.cache_dir),
        }


_DEFAULT_CACHE_MANAGER: Optional[CacheManager] = None


def get_default_cache_manager() -> CacheManager:
    """Get or instantiate default global CacheManager."""
    global _DEFAULT_CACHE_MANAGER
    if _DEFAULT_CACHE_MANAGER is None:
        _DEFAULT_CACHE_MANAGER = CacheManager()
    return _DEFAULT_CACHE_MANAGER
