"""
Font Manager - Font Personality Mapping and Caching System.

PHASE 7 IMPLEMENTATION:
Provides intelligent font selection based on typography personality
and manages font downloading/caching for consistent typography.

Features:
- Font personality mapping (authoritative, friendly, elegant, etc.)
- Web-safe font alternatives for each personality
- Font downloading and caching for popular fonts
- Typography consistency validation
"""

import os
import logging
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import urllib.request
from io import BytesIO

logger = logging.getLogger(__name__)


# =============================================================================
# FONT PERSONALITY MAPPING
# =============================================================================

FONT_PERSONALITY_MAP = {
    "authoritative": {
        "primary": ["Oswald", "Bebas Neue", "Impact", "Anton"],
        "fallback": "DejaVuSans-Bold",
        "web_safe": ["Impact", "Arial Black", "sans-serif"],
        "letter_spacing": -0.02,
        "weight": 700,
        "style": "bold",
        "characteristics": ["strong", "commanding", "serious"]
    },
    "elegant": {
        "primary": ["Playfair Display", "Cormorant", "Libre Baskerville", "Crimson Text"],
        "fallback": "DejaVuSerif",
        "web_safe": ["Georgia", "Times New Roman", "serif"],
        "letter_spacing": 0.05,
        "weight": 400,
        "style": "normal",
        "characteristics": ["refined", "sophisticated", "luxurious"]
    },
    "friendly": {
        "primary": ["Nunito", "Poppins", "Quicksand", "Lato"],
        "fallback": "DejaVuSans",
        "web_safe": ["Trebuchet MS", "Verdana", "sans-serif"],
        "letter_spacing": 0,
        "weight": 600,
        "style": "semibold",
        "characteristics": ["approachable", "warm", "inviting"]
    },
    "technical": {
        "primary": ["JetBrains Mono", "Fira Code", "Source Code Pro", "IBM Plex Mono"],
        "fallback": "DejaVuSansMono",
        "web_safe": ["Consolas", "Courier New", "monospace"],
        "letter_spacing": 0,
        "weight": 500,
        "style": "medium",
        "characteristics": ["precise", "modern", "developer-focused"]
    },
    "bold": {
        "primary": ["Montserrat", "Oswald", "Anton", "Black Ops One"],
        "fallback": "DejaVuSans-Bold",
        "web_safe": ["Impact", "Arial Black", "sans-serif"],
        "letter_spacing": -0.03,
        "weight": 900,
        "style": "black",
        "characteristics": ["powerful", "impactful", "strong"]
    },
    "expressive": {
        "primary": ["Abril Fatface", "Lobster", "Pacifico", "Dancing Script"],
        "fallback": "DejaVuSans",
        "web_safe": ["Brush Script MT", "Comic Sans MS", "cursive"],
        "letter_spacing": 0.03,
        "weight": 400,
        "style": "normal",
        "characteristics": ["creative", "playful", "artistic"]
    },
    "subtle": {
        "primary": ["Lato", "Open Sans", "Roboto", "Source Sans Pro"],
        "fallback": "DejaVuSans",
        "web_safe": ["Segoe UI", "Helvetica", "sans-serif"],
        "letter_spacing": 0,
        "weight": 400,
        "style": "normal",
        "characteristics": ["clean", "neutral", "professional"]
    },
    "refined": {
        "primary": ["Crimson Text", "Merriweather", "Libre Baskerville", "EB Garamond"],
        "fallback": "DejaVuSerif",
        "web_safe": ["Georgia", "Palatino", "serif"],
        "letter_spacing": 0.04,
        "weight": 400,
        "style": "normal",
        "characteristics": ["classic", "tasteful", "editorial"]
    },
    "modern": {
        "primary": ["Inter", "DM Sans", "Space Grotesk", "Outfit"],
        "fallback": "DejaVuSans",
        "web_safe": ["Segoe UI", "Roboto", "sans-serif"],
        "letter_spacing": -0.01,
        "weight": 500,
        "style": "medium",
        "characteristics": ["contemporary", "clean", "minimal"]
    },
    "geometric": {
        "primary": ["Futura", "Century Gothic", "Gilroy", "Avenir"],
        "fallback": "DejaVuSans",
        "web_safe": ["Century Gothic", "Arial", "sans-serif"],
        "letter_spacing": 0.02,
        "weight": 500,
        "style": "medium",
        "characteristics": ["geometric", "balanced", "structured"]
    }
}


# =============================================================================
# FONT CACHE CONFIGURATION
# =============================================================================

# Cache directory for downloaded fonts
FONT_CACHE_DIR = Path("/tmp/metaview_fonts")

# Google Fonts API URLs
GOOGLE_FONTS_CSS_URL = "https://fonts.googleapis.com/css2?family={font_name}:wght@{weights}&display=swap"
GOOGLE_FONTS_DOWNLOAD_URL = "https://fonts.google.com/download?family={font_name}"

# Common weights to download
DEFAULT_WEIGHTS = [400, 500, 600, 700]

# Cache TTL in seconds (7 days)
FONT_CACHE_TTL = 7 * 24 * 60 * 60

# Popular fonts that can be downloaded (subset for performance)
DOWNLOADABLE_FONTS = {
    "Inter": "Inter",
    "Roboto": "Roboto",
    "Open Sans": "Open+Sans",
    "Lato": "Lato",
    "Montserrat": "Montserrat",
    "Poppins": "Poppins",
    "Nunito": "Nunito",
    "Playfair Display": "Playfair+Display",
    "Oswald": "Oswald",
    "Source Sans Pro": "Source+Sans+Pro",
    "Merriweather": "Merriweather",
    "Raleway": "Raleway",
    "Ubuntu": "Ubuntu",
    "Fira Code": "Fira+Code",
    "JetBrains Mono": "JetBrains+Mono"
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class FontConfig:
    """Configuration for a specific font."""
    name: str
    path: Optional[str] = None
    weight: int = 400
    style: str = "normal"
    is_cached: bool = False
    is_system: bool = False
    letter_spacing: float = 0.0


@dataclass
class TypographySet:
    """Complete typography set for a design."""
    headline_font: FontConfig
    body_font: FontConfig
    accent_font: FontConfig
    personality: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "headline_font": {
                "name": self.headline_font.name,
                "weight": self.headline_font.weight,
                "letter_spacing": self.headline_font.letter_spacing
            },
            "body_font": {
                "name": self.body_font.name,
                "weight": self.body_font.weight
            },
            "accent_font": {
                "name": self.accent_font.name,
                "weight": self.accent_font.weight
            },
            "personality": self.personality
        }


# =============================================================================
# FONT MANAGER CLASS
# =============================================================================

class FontManager:
    """
    Manages font selection, downloading, and caching.
    
    Provides intelligent font selection based on typography personality
    and handles font caching for improved performance.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize FontManager.
        
        Args:
            cache_dir: Directory for font cache (default: /tmp/metaview_fonts)
        """
        self.cache_dir = cache_dir or FONT_CACHE_DIR
        self._ensure_cache_dir()
        self._system_fonts = self._discover_system_fonts()
        
        logger.info(f"FontManager initialized: cache_dir={self.cache_dir}, system_fonts={len(self._system_fonts)}")
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create font cache directory: {e}")
    
    def _discover_system_fonts(self) -> Dict[str, str]:
        """Discover available system fonts."""
        system_fonts = {}
        
        # Common font directories
        font_dirs = [
            "/usr/share/fonts",
            "/usr/local/share/fonts",
            "/System/Library/Fonts",
            "C:\\Windows\\Fonts"
        ]
        
        # Common font extensions
        font_extensions = [".ttf", ".otf", ".woff", ".woff2"]
        
        for font_dir in font_dirs:
            if os.path.exists(font_dir):
                for root, dirs, files in os.walk(font_dir):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in font_extensions):
                            font_path = os.path.join(root, file)
                            font_name = os.path.splitext(file)[0]
                            system_fonts[font_name.lower()] = font_path
        
        # Add common DejaVu fallbacks (usually available on Linux)
        dejavu_paths = {
            "dejavusans": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "dejavusans-bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "dejavuserif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "dejavusansmono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
        }
        
        for name, path in dejavu_paths.items():
            if os.path.exists(path):
                system_fonts[name] = path
        
        return system_fonts
    
    def get_typography_for_personality(
        self,
        personality: str,
        prefer_cached: bool = True
    ) -> TypographySet:
        """
        Get a complete typography set for a personality.
        
        Args:
            personality: Typography personality (authoritative, friendly, etc.)
            prefer_cached: Prefer cached fonts over downloading
            
        Returns:
            TypographySet with headline, body, and accent fonts
        """
        personality_lower = personality.lower()
        
        # Get personality config or default to 'subtle'
        config = FONT_PERSONALITY_MAP.get(personality_lower, FONT_PERSONALITY_MAP["subtle"])
        
        # Find best available headline font
        headline_font = self._find_best_font(
            config["primary"],
            config["fallback"],
            config["weight"],
            config["letter_spacing"],
            prefer_cached
        )
        
        # Body font - use subtle/friendly personality
        body_config = FONT_PERSONALITY_MAP["subtle"]
        body_font = self._find_best_font(
            body_config["primary"],
            body_config["fallback"],
            400,
            0,
            prefer_cached
        )
        
        # Accent font - match headline personality
        accent_font = self._find_best_font(
            config["primary"],
            config["fallback"],
            config["weight"] - 100 if config["weight"] > 400 else config["weight"],
            config["letter_spacing"],
            prefer_cached
        )
        
        return TypographySet(
            headline_font=headline_font,
            body_font=body_font,
            accent_font=accent_font,
            personality=personality_lower
        )
    
    def _find_best_font(
        self,
        primary_fonts: List[str],
        fallback: str,
        weight: int,
        letter_spacing: float,
        prefer_cached: bool,
        download_if_missing: bool = True
    ) -> FontConfig:
        """
        Find the best available font from a list.
        
        PHASE 2: Now includes font downloading capability.
        """
        
        # Check cached fonts first
        if prefer_cached:
            for font_name in primary_fonts:
                cached_path = self._get_cached_font_path(font_name, weight)
                if cached_path and os.path.exists(cached_path):
                    return FontConfig(
                        name=font_name,
                        path=cached_path,
                        weight=weight,
                        letter_spacing=letter_spacing,
                        is_cached=True
                    )
        
        # Check system fonts
        for font_name in primary_fonts:
            font_key = font_name.lower().replace(" ", "")
            if font_key in self._system_fonts:
                return FontConfig(
                    name=font_name,
                    path=self._system_fonts[font_key],
                    weight=weight,
                    letter_spacing=letter_spacing,
                    is_system=True
                )
        
        # PHASE 2: Try downloading fonts if not found
        if download_if_missing:
            for font_name in primary_fonts:
                if font_name in DOWNLOADABLE_FONTS:
                    downloaded_path = self.download_font(font_name, weight)
                    if downloaded_path and os.path.exists(downloaded_path):
                        return FontConfig(
                            name=font_name,
                            path=downloaded_path,
                            weight=weight,
                            letter_spacing=letter_spacing,
                            is_cached=True
                        )
        
        # Use fallback
        fallback_key = fallback.lower().replace("-", "")
        fallback_path = self._system_fonts.get(fallback_key)
        
        return FontConfig(
            name=fallback,
            path=fallback_path,
            weight=weight,
            letter_spacing=letter_spacing,
            is_system=bool(fallback_path)
        )
    
    def _get_cached_font_path(self, font_name: str, weight: int) -> Optional[str]:
        """Get path to cached font file."""
        safe_name = font_name.lower().replace(" ", "-")
        cached_file = self.cache_dir / f"{safe_name}-{weight}.ttf"
        
        if cached_file.exists():
            # Check if cache is still valid (TTL check)
            try:
                import time
                file_age = time.time() - cached_file.stat().st_mtime
                if file_age < FONT_CACHE_TTL:
                    return str(cached_file)
                else:
                    logger.debug(f"Font cache expired for {font_name}: {file_age}s old")
            except:
                pass
            return str(cached_file)  # Use even if TTL check fails
        
        return None
    
    def download_font(
        self,
        font_name: str,
        weight: int = 400,
        force: bool = False
    ) -> Optional[str]:
        """
        PHASE 2: Download a font from Google Fonts and cache it.
        
        Args:
            font_name: Name of the font (e.g., "Inter", "Roboto")
            weight: Font weight to download
            force: Force re-download even if cached
            
        Returns:
            Path to downloaded font file or None if download fails
        """
        # Check cache first (unless force)
        if not force:
            cached = self._get_cached_font_path(font_name, weight)
            if cached:
                logger.debug(f"Font {font_name} weight {weight} found in cache")
                return cached
        
        # Check if font is in downloadable list
        if font_name not in DOWNLOADABLE_FONTS:
            logger.debug(f"Font {font_name} not in downloadable list")
            return None
        
        try:
            import re
            
            # Construct Google Fonts CSS URL
            font_param = DOWNLOADABLE_FONTS[font_name]
            weights_param = ";".join(str(w) for w in [weight])
            css_url = f"https://fonts.googleapis.com/css2?family={font_param}:wght@{weights_param}&display=swap"
            
            logger.info(f"📥 Downloading font {font_name} weight {weight} from Google Fonts")
            
            # Fetch CSS to get font URL
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            request = urllib.request.Request(css_url, headers=headers)
            with urllib.request.urlopen(request, timeout=10) as response:
                css_content = response.read().decode('utf-8')
            
            # Extract font URL from CSS (look for woff2 or ttf)
            # Pattern: src: url(https://fonts.gstatic.com/...)
            url_pattern = r'src:\s*url\((https://fonts\.gstatic\.com/[^)]+\.(?:woff2|ttf))\)'
            matches = re.findall(url_pattern, css_content)
            
            if not matches:
                logger.warning(f"No font URL found in CSS for {font_name}")
                return None
            
            font_url = matches[0]
            
            # Download the font file
            font_request = urllib.request.Request(font_url, headers=headers)
            with urllib.request.urlopen(font_request, timeout=30) as response:
                font_data = response.read()
            
            # Determine file extension
            ext = ".woff2" if ".woff2" in font_url else ".ttf"
            
            # Save to cache
            safe_name = font_name.lower().replace(" ", "-")
            cached_file = self.cache_dir / f"{safe_name}-{weight}{ext}"
            
            with open(cached_file, 'wb') as f:
                f.write(font_data)
            
            logger.info(f"✅ Font {font_name} cached at {cached_file} ({len(font_data)} bytes)")
            
            # For woff2, we need to convert to ttf for PIL compatibility
            # For now, just return the path if it's woff2 (PIL may not support it)
            if ext == ".woff2":
                logger.warning(f"Font {font_name} is WOFF2 format - may not be compatible with PIL")
                # Try to find a TTF fallback
                return None
            
            return str(cached_file)
            
        except urllib.error.URLError as e:
            logger.warning(f"Failed to download font {font_name}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Font download error for {font_name}: {e}")
            return None
    
    def ensure_fonts_available(
        self,
        personality: str,
        download_if_missing: bool = True
    ) -> bool:
        """
        PHASE 2: Ensure fonts for a personality are available.
        
        Args:
            personality: Typography personality
            download_if_missing: Whether to download missing fonts
            
        Returns:
            True if at least one font is available
        """
        config = FONT_PERSONALITY_MAP.get(personality.lower(), FONT_PERSONALITY_MAP["subtle"])
        primary_fonts = config["primary"]
        
        # Check if any primary font is available
        for font_name in primary_fonts:
            # Check system fonts
            font_key = font_name.lower().replace(" ", "")
            if font_key in self._system_fonts:
                return True
            
            # Check cache
            cached = self._get_cached_font_path(font_name, config["weight"])
            if cached:
                return True
            
            # Try to download
            if download_if_missing and font_name in DOWNLOADABLE_FONTS:
                downloaded = self.download_font(font_name, config["weight"])
                if downloaded:
                    return True
        
        # Fallback should always be available (system font)
        fallback = config["fallback"]
        fallback_key = fallback.lower().replace("-", "")
        return fallback_key in self._system_fonts
    
    def get_font_path(
        self,
        font_name: str,
        weight: int = 400,
        fallback: bool = True
    ) -> Optional[str]:
        """
        Get path to a font file.
        
        Args:
            font_name: Name of the font
            weight: Font weight
            fallback: Use fallback if font not found
            
        Returns:
            Path to font file or None
        """
        # Check cache
        cached_path = self._get_cached_font_path(font_name, weight)
        if cached_path:
            return cached_path
        
        # Check system fonts
        font_key = font_name.lower().replace(" ", "")
        if font_key in self._system_fonts:
            return self._system_fonts[font_key]
        
        # Use fallback
        if fallback:
            fallback_fonts = ["dejavusans-bold", "dejavusans", "arial"]
            for fb in fallback_fonts:
                if fb in self._system_fonts:
                    return self._system_fonts[fb]
        
        return None
    
    def get_pillow_font_path(
        self,
        personality: str,
        prefer_bold: bool = True
    ) -> Optional[str]:
        """
        Get font path suitable for PIL/Pillow.
        
        Args:
            personality: Typography personality
            prefer_bold: Prefer bold weight
            
        Returns:
            Path to TTF font file
        """
        config = FONT_PERSONALITY_MAP.get(personality.lower(), FONT_PERSONALITY_MAP["subtle"])
        weight = 700 if prefer_bold else config["weight"]
        
        # Try each primary font
        for font_name in config["primary"]:
            path = self.get_font_path(font_name, weight)
            if path and path.endswith(('.ttf', '.otf')):
                return path
        
        # Fallback to system fonts
        fallback = config["fallback"]
        fallback_key = fallback.lower().replace("-", "")
        
        if fallback_key in self._system_fonts:
            return self._system_fonts[fallback_key]
        
        # Ultimate fallback
        for fb_name in ["dejavusans-bold", "dejavusans"]:
            if fb_name in self._system_fonts:
                return self._system_fonts[fb_name]
        
        return None
    
    def validate_typography_consistency(
        self,
        typography_set: TypographySet
    ) -> Tuple[bool, List[str]]:
        """
        Validate that a typography set is consistent and usable.
        
        Args:
            typography_set: Typography set to validate
            
        Returns:
            Tuple of (is_valid, issues)
        """
        issues = []
        
        # Check headline font
        if not typography_set.headline_font.path:
            issues.append(f"Headline font '{typography_set.headline_font.name}' not available")
        
        # Check body font
        if not typography_set.body_font.path:
            issues.append(f"Body font '{typography_set.body_font.name}' not available")
        
        # Check accent font
        if not typography_set.accent_font.path:
            issues.append(f"Accent font '{typography_set.accent_font.name}' not available")
        
        # Check weight consistency (headline should be heavier than body)
        if typography_set.headline_font.weight < typography_set.body_font.weight:
            issues.append("Headline font should be heavier than body font")
        
        is_valid = len(issues) == 0
        
        if not is_valid:
            logger.warning(f"Typography validation issues: {issues}")
        
        return is_valid, issues


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_font_manager_instance: Optional[FontManager] = None


def get_font_manager() -> FontManager:
    """Get the singleton FontManager instance."""
    global _font_manager_instance
    
    if _font_manager_instance is None:
        _font_manager_instance = FontManager()
    
    return _font_manager_instance


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_fonts_for_personality(personality: str) -> TypographySet:
    """
    Get typography set for a personality.
    
    Args:
        personality: Typography personality
        
    Returns:
        TypographySet
    """
    return get_font_manager().get_typography_for_personality(personality)


def get_headline_font_path(personality: str) -> Optional[str]:
    """
    Get headline font path for a personality.
    
    Args:
        personality: Typography personality
        
    Returns:
        Path to font file or None
    """
    return get_font_manager().get_pillow_font_path(personality, prefer_bold=True)


def get_personality_characteristics(personality: str) -> List[str]:
    """
    Get characteristics for a typography personality.
    
    Args:
        personality: Typography personality
        
    Returns:
        List of characteristics
    """
    config = FONT_PERSONALITY_MAP.get(personality.lower(), {})
    return config.get("characteristics", [])


def get_letter_spacing_for_personality(personality: str) -> float:
    """
    Get recommended letter spacing for a personality.
    
    Args:
        personality: Typography personality
        
    Returns:
        Letter spacing value
    """
    config = FONT_PERSONALITY_MAP.get(personality.lower(), {})
    return config.get("letter_spacing", 0.0)


def get_font_weight_for_personality(personality: str) -> int:
    """
    Get recommended font weight for a personality.
    
    Args:
        personality: Typography personality
        
    Returns:
        Font weight (100-900)
    """
    config = FONT_PERSONALITY_MAP.get(personality.lower(), {})
    return config.get("weight", 400)

