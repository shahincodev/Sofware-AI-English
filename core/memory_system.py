# SPDX-License-Identifier: NOASSERTION
# Copyright (c) 2025 Shahin

"""
Memory System Module: Support for short-term memory (in-process with TTL)
and long-term memory (persistent with sqlite). This implementation is minimal, secure,
and importable while remaining compatible with MVP architecture.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Iterable, List, Optional, Tuple

@dataclass
class MemoryItem:
    id: str
    content: str
    metadata: Dict[str, Any]
    created_at: float
    expires_at: Optional[float] = None

class ShortTermMemory:
    """Short-term memory: Storage in RAM with expiration time (TTL).

    Behavior:
    - Add with ttl (seconds) or without ttl (temporary until manual cleanup)
    - Simple retrieval and text-based search
    - Automatic cleanup of expired items
    """

    def __init__(self) -> None:
        self._store: Dict[str, MemoryItem] = {}
        self._lock = Lock()

    def add(self, content: str, ttl: Optional[float] = None, metadata: Optional[Dict[str, Any]] = None) -> MemoryItem:
        """Add an item to short-term memory. Returns the created MemoryItem."""
        if metadata is None: 
            metadata= {}
        item_id = str(uuid.uuid4())
        now = time.time()
        expires_at = now + ttl if ttl is not None else None
        item = MemoryItem(id=item_id, content=content, metadata=metadata, created_at=now, expires_at=expires_at)
        with self._lock:
            self._store[item_id] = item
        return item
    
    def get(self, item_id: str) -> Optional[MemoryItem]:
         """Get item by ID. Returns None if expired."""
         with self._lock:
             item = self._store.get(item_id)
             if item is None: 
                 return None
             if item.expires_at is not None and time.time() > item.expires_at:
                # Item is expired; delete and return None
                del self._store[item_id]
                return None
                return item
             
    def query(self, keyword: str, limit: int = 10) -> List[MemoryItem]:
        """Simple search based on keyword presence in content or metadata (strings)."""
        keyword_lover = keyword.lower()
        matches: List[MemoryItem] = []
        with self._lock:
            # Clean up expired items before searching
            self._cleanup_locked()
            for item in self._store.values():
                if (keyword_lover in item.content.lower() or
                    any(keyword_lover in str(v).lower() for v in item.metadata.values())):
                    matches.append(item)
                    if len(matches) >= limit:
                        break

                else: 
                    # Search in metadata as string
                    meta_str = json.dumps(item.metadata, ensure_ascii=False).lower()
                    if keyword_lover in meta_str:
                        matches.append(item)
                        if len(matches) >= limit:
                            break

        return matches
    def all_items(self) -> List[MemoryItem]:
        """Return all non-expired items in memory."""
        with self._lock:
            self._cleanup_locked()
            return list(self._store.values())
        
    def _cleanup_locked(self) -> None:
        """Delete expired items; assumes lock is already held."""
        now = time.time()
        to_delete = [item_id for item_id, item in self._store.items()
                     if item.expires_at is not None and now > item.expires_at]
        for item_id in to_delete:
            del self._store[item_id]

    def cleanup(self) -> None:
        """Safe cleanup of expired items."""
        with self._lock:
            self._cleanup_locked()

    def pop_oldest(self) -> Optional[MemoryItem]:
        """Remove the oldest item (for migration to long-term memory)."""
        with self._lock:
            if not self._store:
                return None
            oldest_item = min(self._store.values(), key=lambda item: item.created_at)
            del self._store[oldest_item.id]
            return oldest_item
        
class LongTermMemory:
    """Long-term memory: Persistent storage with SQLite.

    Behavior:
    - Add, retrieve and search based on text
    - Secure storage using SQL parameters to prevent injection
    """

    """Long-term memory: Persistent storage in SQLite.

    Minimal design:
    - memories table(id TEXT PRIMARY KEY, content TEXT, metadata TEXT, created_at REAL)
    - Simple LIKE search for text; embedding/FAISS can be added in the future.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            db_path = str(Path("./data").resolve() / "memories.sqlite3")
        self._db_path = db_path
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._lock = Lock()
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Create memory table if it doesn't exist."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at REAL NOT NULL
                )
            """)
            self._conn.commit()

    def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> MemoryItem:
        """Add an item to long-term memory and return its MemoryItem."""
        if metadata is None:
            metadata = {}
        item_id = str(uuid.uuid4())
        now = time.time()
        meta_json = json.dumps(metadata, ensure_ascii=False)
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT INTO memories (id, content, metadata, created_at)
                VALUES (?, ?, ?, ?)
            """, (item_id, content, meta_json, now))
            self._conn.commit()

        return MemoryItem(id=item_id, content=content, metadata=metadata, created_at=now)
    def get(self, item_id: str) -> Optional[MemoryItem]:
        """Get item by ID from the database."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT id, content, metadata, created_at FROM memories WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            meta_dict = json.loads(row[2]) if row[2] else {}
            return MemoryItem(id=row[0], content=row[1], metadata=meta_dict, created_at=row[3])
        
    def search(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """Simple search using LIKE on content and metadata columns."""
        like_q = f"%{query}%"
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT id, content, metadata, created_at FROM memories
                WHERE content LIKE ? OR metadata LIKE ?
                LIMIT ?
            """, (like_q, like_q, limit))
            rows = cursor.fetchall()
            results: List[MemoryItem] = []
            for row in rows:
                meta_dict = json.loads(row[2]) if row[2] else {}
                results.append(MemoryItem(id=row[0], content=row[1], metadata=meta_dict, created_at=row[3]))
            return results
    def delete(self, item_id: str) -> bool: 
        """Delete item by ID. Returns True if the item was deleted."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (item_id,))
            self._conn.commit()
            return cursor.rowcount > 0
        
    def all(self, limit: int = 100) -> List[MemoryItem]:
        """Get a collection of items (newest first)."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT id, content, metadata, created_at FROM memories
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            results: List[MemoryItem] = []
            for row in rows:
                meta_dict = json.loads(row[2]) if row[2] else {}
                results.append(MemoryItem(id=row[0], content=row[1], metadata=meta_dict, created_at=row[3]))
            return results
        
    def close(self) -> None:
        """Close the database connection."""
        with self._lock:
            try:
                self._conn.commit()
            finally: 
                self._conn.close()


class MemoryManager:
    """Integrated memory management: Combining short-term and long-term with simple consolidation policy.

    Features:
    - Add to short-term with ttl and then automatic transfer of old/large items to long-term
    - Direct addition to long-term
    - Unified search (first short-term then long-term)
    - Helper methods for cleanup and shutdown
    """

    def __init__(self, *, lt_db_path: Optional[str] = None, consolidation_threshold: int = 50) -> None:
        # consolidation_threshold: if short-term items exceed this, old items are transferred
        self.short = ShortTermMemory()
        self.long = LongTermMemory(db_path=lt_db_path)
        self._consolidation_threshold = max(1, int(consolidation_threshold))
        self._lock = Lock()

    def remember_short(self, content: str, ttl: Optional[float] = 60.0, metadata: Optional[Dict[str, Any]] = None) -> MemoryItem:
        """Quick storage in short-term memory. May automatically transfer to long-term memory."""
        item = self.short.add(content, ttl=ttl, metadata=metadata)
        # Simple consolidation policy: if count exceeds limit, transfer oldest to long-term
        self._maybe_consolidate()
        return item
    
    def remember_long(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> MemoryItem:
        """Permanent storage in long-term memory."""
        return self.long.add(content, metadata=metadata)
    def recall(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """Unified search: first in short-term then in long-term."""
        results: List[MemoryItem] = []
        # جستجو در short-term
        results.extend(self.short.query(query, limit=limit))
        if len(results) < limit:
            # کمبود نتایج: جستجو در long-term
            remaining = limit - len(results)
            results.extend(self.long.search(query, limit=remaining))
        return results

    def forget_long(self, item_id: str) -> bool:
        """Delete item from long-term memory by ID. Returns True if deleted."""
        return self.long.delete(item_id)
    
    def _maybe_consolidate(self) -> None:
        """If needed, transfers one or more items from short-term to long-term."""
        with self._lock: 
            items = self.short.all_items()
            if len(items) > self._consolidation_threshold:
                return
            # Transfer until reaching threshold (remove oldest ones)
            to_move_count = len(items) - self._consolidation_threshold
            for _ in range(to_move_count):
                old = self.short.pop_oldest()
                if old is None:
                    continue
                self.long.add(content=old.content, metadata=old.metadata)

    def shutdown(self) -> None:
        """Safe shutdown of long-term memory."""
        self.short.cleanup()
        self.long.close()