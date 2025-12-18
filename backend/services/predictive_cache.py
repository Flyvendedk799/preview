"""
Predictive Cache - Smart caching for preview generation.

This module implements intelligent caching that:
1. Caches based on URL patterns (not just exact URLs)
2. Pre-warms cache for common site patterns
3. Uses tiered TTLs based on content type
4. Implements cache-aside pattern with async refresh

Key Features:
- Pattern-based cache keys (domain + page type)
- Tiered TTL (static sites longer, dynamic shorter)
- Background cache refresh before expiry
- Cache statistics and hit rate tracking
"""

import logging
import time
import hashlib
import json
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse
import threading

logger = logging.getLogger(__name__)


class CacheTier(str, Enum):
    """Cache tier with different TTLs."""
    STATIC = "static"  # Static content, long TTL (24h)
    DYNAMIC = "dynamic"  # Dynamic content, medium TTL (1h)
    REAL_TIME = "real_time"  # Real-time content, short TTL (5min)
    NO_CACHE = "no_cache"  # Don't cache


# TTL in seconds for each tier
TIER_TTL: Dict[CacheTier, int] = {
    CacheTier.STATIC: 86400,  # 24 hours
    CacheTier.DYNAMIC: 3600,  # 1 hour
    CacheTier.REAL_TIME: 300,  # 5 minutes
    CacheTier.NO_CACHE: 0
}

# Domain patterns for tier classification
STATIC_DOMAINS = [
    "wikipedia.org",
    "medium.com",
    "github.com",
    "linkedin.com",
    "about.me"
]

DYNAMIC_DOMAINS = [
    "twitter.com",
    "x.com",
    "facebook.com",
    "instagram.com",
    "tiktok.com"
]

REALTIME_DOMAINS = [
    "news.",
    "bloomberg.com",
    "reuters.com",
    "cnn.com"
]


@dataclass
class CacheEntry:
    """A cache entry with metadata."""
    key: str
    data: Dict[str, Any]
    created_at: float
    ttl_seconds: int
    tier: CacheTier
    hit_count: int = 0
    last_accessed: float = 0.0
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.tier == CacheTier.NO_CACHE:
            return True
        age = time.time() - self.created_at
        return age > self.ttl_seconds
    
    def should_refresh(self, refresh_threshold: float = 0.8) -> bool:
        """Check if entry should be refreshed (before expiry)."""
        if self.tier == CacheTier.NO_CACHE:
            return False
        age = time.time() - self.created_at
        threshold_age = self.ttl_seconds * refresh_threshold
        return age > threshold_age
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "data": self.data,
            "created_at": self.created_at,
            "ttl_seconds": self.ttl_seconds,
            "tier": self.tier.value,
            "hit_count": self.hit_count,
            "last_accessed": self.last_accessed
        }


@dataclass
class CacheStats:
    """Cache statistics."""
    total_hits: int = 0
    total_misses: int = 0
    total_entries: int = 0
    total_refreshes: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate hit rate."""
        total = self.total_hits + self.total_misses
        return self.total_hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_hits": self.total_hits,
            "total_misses": self.total_misses,
            "total_entries": self.total_entries,
            "total_refreshes": self.total_refreshes,
            "hit_rate": self.hit_rate
        }


class PredictiveCache:
    """
    Smart predictive cache for preview data.
    
    Features:
    - Pattern-based cache keys
    - Tiered TTLs based on content type
    - Background refresh before expiry
    - Memory-efficient LRU eviction
    """
    
    def __init__(
        self,
        max_entries: int = 1000,
        refresh_callback: Optional[Callable[[str], Dict[str, Any]]] = None,
        use_redis: bool = False
    ):
        """
        Initialize the cache.
        
        Args:
            max_entries: Maximum cache entries
            refresh_callback: Callback to refresh expired entries
            use_redis: Whether to use Redis backend (else memory)
        """
        self.max_entries = max_entries
        self.refresh_callback = refresh_callback
        self.use_redis = use_redis
        
        # In-memory cache (could be replaced with Redis)
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = CacheStats()
        
        # Background refresh thread
        self._refresh_thread: Optional[threading.Thread] = None
        self._stop_refresh = threading.Event()
        
        logger.info(f"📦 PredictiveCache initialized (max={max_entries})")
    
    def get(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get cached preview data for URL.
        
        Args:
            url: URL to look up
            
        Returns:
            Cached data or None if not found/expired
        """
        key = self._generate_cache_key(url)
        
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats.total_misses += 1
                logger.debug(f"Cache miss: {key}")
                return None
            
            if entry.is_expired():
                # Remove expired entry
                del self._cache[key]
                self._stats.total_misses += 1
                self._stats.total_entries = len(self._cache)
                logger.debug(f"Cache expired: {key}")
                return None
            
            # Update access stats
            entry.hit_count += 1
            entry.last_accessed = time.time()
            self._stats.total_hits += 1
            
            # Check if needs background refresh
            if entry.should_refresh() and self.refresh_callback:
                self._trigger_background_refresh(url)
            
            logger.debug(f"Cache hit: {key} (hits={entry.hit_count})")
            return entry.data
    
    def set(
        self,
        url: str,
        data: Dict[str, Any],
        tier: Optional[CacheTier] = None
    ) -> None:
        """
        Cache preview data for URL.
        
        Args:
            url: URL to cache
            data: Preview data
            tier: Optional cache tier (auto-detected if not provided)
        """
        key = self._generate_cache_key(url)
        
        # Auto-detect tier if not provided
        if tier is None:
            tier = self._classify_url_tier(url)
        
        if tier == CacheTier.NO_CACHE:
            return
        
        ttl = TIER_TTL[tier]
        
        entry = CacheEntry(
            key=key,
            data=data,
            created_at=time.time(),
            ttl_seconds=ttl,
            tier=tier,
            hit_count=0,
            last_accessed=time.time()
        )
        
        with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.max_entries:
                self._evict_lru()
            
            self._cache[key] = entry
            self._stats.total_entries = len(self._cache)
        
        logger.debug(f"Cached: {key} (tier={tier.value}, ttl={ttl}s)")
    
    def invalidate(self, url: str) -> bool:
        """
        Invalidate cache entry for URL.
        
        Args:
            url: URL to invalidate
            
        Returns:
            True if entry was found and removed
        """
        key = self._generate_cache_key(url)
        
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.total_entries = len(self._cache)
                logger.debug(f"Invalidated: {key}")
                return True
        
        return False
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._stats
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._stats = CacheStats()
        
        logger.info("Cache cleared")
    
    def _generate_cache_key(self, url: str) -> str:
        """
        Generate cache key from URL.
        
        Uses a pattern-based approach that normalizes URLs
        for better cache hit rates.
        """
        parsed = urlparse(url)
        
        # Normalize domain
        domain = parsed.netloc.lower().replace("www.", "")
        
        # Normalize path (remove trailing slashes, query params for some sites)
        path = parsed.path.rstrip("/")
        
        # For known dynamic sites, include more of the path
        # For static sites, use simpler keys
        if any(d in domain for d in DYNAMIC_DOMAINS + REALTIME_DOMAINS):
            # Include full path for dynamic content
            key_base = f"{domain}{path}"
        else:
            # For static content, use domain + first path segment
            path_parts = [p for p in path.split("/") if p][:2]
            key_base = f"{domain}/" + "/".join(path_parts)
        
        # Hash for consistent key length
        key_hash = hashlib.md5(key_base.encode()).hexdigest()[:16]
        
        return f"preview:{domain}:{key_hash}"
    
    def _classify_url_tier(self, url: str) -> CacheTier:
        """Classify URL into cache tier."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check for static domains
        for pattern in STATIC_DOMAINS:
            if pattern in domain:
                return CacheTier.STATIC
        
        # Check for real-time domains
        for pattern in REALTIME_DOMAINS:
            if pattern in domain:
                return CacheTier.REAL_TIME
        
        # Check for dynamic domains
        for pattern in DYNAMIC_DOMAINS:
            if pattern in domain:
                return CacheTier.DYNAMIC
        
        # Default to dynamic
        return CacheTier.DYNAMIC
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed
        )
        
        del self._cache[lru_key]
        logger.debug(f"Evicted LRU: {lru_key}")
    
    def _trigger_background_refresh(self, url: str) -> None:
        """Trigger background refresh for URL."""
        if not self.refresh_callback:
            return
        
        def refresh():
            try:
                logger.debug(f"Background refresh: {url}")
                data = self.refresh_callback(url)
                if data:
                    self.set(url, data)
                    self._stats.total_refreshes += 1
            except Exception as e:
                logger.warning(f"Background refresh failed: {e}")
        
        # Run in background thread
        thread = threading.Thread(target=refresh, daemon=True)
        thread.start()


class PatternBasedPreloader:
    """
    Preloads cache based on URL patterns.
    
    Learns common URL patterns and pre-warms cache
    for likely requests.
    """
    
    def __init__(self, cache: PredictiveCache):
        """Initialize with cache reference."""
        self.cache = cache
        self.patterns: Dict[str, int] = {}  # pattern -> access count
        self.max_patterns = 100
    
    def record_access(self, url: str) -> None:
        """Record URL access for pattern learning."""
        pattern = self._extract_pattern(url)
        
        self.patterns[pattern] = self.patterns.get(pattern, 0) + 1
        
        # Trim to max patterns
        if len(self.patterns) > self.max_patterns:
            # Keep top patterns
            sorted_patterns = sorted(
                self.patterns.items(),
                key=lambda x: x[1],
                reverse=True
            )
            self.patterns = dict(sorted_patterns[:self.max_patterns])
    
    def get_preload_candidates(self, url: str) -> List[str]:
        """
        Get candidate URLs to preload based on current URL.
        
        Args:
            url: Current URL
            
        Returns:
            List of URLs likely to be requested next
        """
        pattern = self._extract_pattern(url)
        
        # Find similar patterns
        candidates = []
        for p, count in sorted(self.patterns.items(), key=lambda x: x[1], reverse=True):
            if self._patterns_similar(pattern, p):
                candidates.append(p)
                if len(candidates) >= 3:
                    break
        
        return candidates
    
    def _extract_pattern(self, url: str) -> str:
        """Extract pattern from URL."""
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        path_parts = [p for p in parsed.path.split("/") if p][:2]
        return f"{domain}/" + "/".join(path_parts)
    
    def _patterns_similar(self, p1: str, p2: str) -> bool:
        """Check if two patterns are similar."""
        # Same domain
        d1 = p1.split("/")[0]
        d2 = p2.split("/")[0]
        return d1 == d2


# Singleton cache
_cache_instance: Optional[PredictiveCache] = None


def get_predictive_cache(
    max_entries: int = 1000,
    refresh_callback: Optional[Callable[[str], Dict[str, Any]]] = None
) -> PredictiveCache:
    """Get or create the predictive cache singleton."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = PredictiveCache(max_entries, refresh_callback)
    return _cache_instance


def cache_preview(url: str, data: Dict[str, Any]) -> None:
    """Convenience function to cache preview data."""
    cache = get_predictive_cache()
    cache.set(url, data)


def get_cached_preview(url: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get cached preview."""
    cache = get_predictive_cache()
    return cache.get(url)

