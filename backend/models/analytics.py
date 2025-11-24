"""Analytics model definitions."""
from typing import List


class TopDomain:
    """Top domain model for analytics."""
    
    def __init__(self, domain: str, clicks: int, ctr: float):
        self.domain = domain
        self.clicks = clicks
        self.ctr = ctr
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "clicks": self.clicks,
            "ctr": self.ctr,
        }

