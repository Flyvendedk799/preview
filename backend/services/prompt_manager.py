"""
Prompt Manager - Versioning, Testing, and Management for AI Prompts

Manages AI prompts with:
- Versioning
- A/B testing
- Performance tracking
- Rollback capability
- Template system
"""

import json
import logging
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import os

logger = logging.getLogger(__name__)


class PromptStatus(str, Enum):
    """Prompt status."""
    DRAFT = "draft"
    ACTIVE = "active"
    TESTING = "testing"
    DEPRECATED = "deprecated"


@dataclass
class PromptVersion:
    """Version of a prompt."""
    prompt_id: str
    version: str
    content: str
    variables: List[str] = field(default_factory=list)
    status: PromptStatus = PromptStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    test_results: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "prompt_id": self.prompt_id,
            "version": self.version,
            "content": self.content,
            "variables": self.variables,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "performance_metrics": self.performance_metrics,
            "test_results": self.test_results
        }


class PromptManager:
    """
    Manages AI prompts with versioning and testing.
    
    Features:
    - Prompt versioning
    - A/B testing
    - Performance tracking
    - Rollback capability
    - Template system
    """
    
    def __init__(self, prompts_dir: str = "backend/prompts"):
        """
        Initialize prompt manager.
        
        Args:
            prompts_dir: Directory containing prompt files
        """
        self.prompts_dir = prompts_dir
        self.prompts: Dict[str, List[PromptVersion]] = {}
        self.active_versions: Dict[str, str] = {}  # prompt_id -> version
        self.logger = logging.getLogger(__name__)
        
        # Load prompts from directory
        self._load_prompts()
    
    def _load_prompts(self):
        """Load prompts from directory."""
        if not os.path.exists(self.prompts_dir):
            self.logger.warning(f"Prompts directory not found: {self.prompts_dir}")
            return
        
        # Load prompt files
        for filename in os.listdir(self.prompts_dir):
            if filename.endswith(".txt"):
                prompt_id = filename[:-4]  # Remove .txt extension
                filepath = os.path.join(self.prompts_dir, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    version = PromptVersion(
                        prompt_id=prompt_id,
                        version="1.0.0",
                        content=content,
                        status=PromptStatus.ACTIVE
                    )
                    
                    if prompt_id not in self.prompts:
                        self.prompts[prompt_id] = []
                    
                    self.prompts[prompt_id].append(version)
                    self.active_versions[prompt_id] = "1.0.0"
                    
                    self.logger.info(f"Loaded prompt: {prompt_id} v1.0.0")
                except Exception as e:
                    self.logger.error(f"Failed to load prompt {filename}: {e}")
    
    def get_prompt(
        self,
        prompt_id: str,
        version: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Get prompt content.
        
        Args:
            prompt_id: Prompt identifier
            version: Specific version (defaults to active)
            variables: Variables to substitute
            
        Returns:
            Prompt content with variables substituted
        """
        if prompt_id not in self.prompts:
            raise ValueError(f"Prompt not found: {prompt_id}")
        
        # Get version
        if version:
            prompt_version = next(
                (v for v in self.prompts[prompt_id] if v.version == version),
                None
            )
            if not prompt_version:
                raise ValueError(f"Version {version} not found for prompt {prompt_id}")
        else:
            # Get active version
            active_version = self.active_versions.get(prompt_id)
            if not active_version:
                raise ValueError(f"No active version for prompt {prompt_id}")
            
            prompt_version = next(
                (v for v in self.prompts[prompt_id] if v.version == active_version),
                None
            )
            if not prompt_version:
                raise ValueError(f"Active version {active_version} not found")
        
        # Substitute variables
        content = prompt_version.content
        if variables:
            for key, value in variables.items():
                content = content.replace(f"{{{key}}}", str(value))
        
        return content
    
    def create_version(
        self,
        prompt_id: str,
        content: str,
        version: Optional[str] = None
    ) -> PromptVersion:
        """
        Create new version of a prompt.
        
        Args:
            prompt_id: Prompt identifier
            content: Prompt content
            version: Version string (auto-increments if not provided)
            
        Returns:
            Created PromptVersion
        """
        if prompt_id not in self.prompts:
            self.prompts[prompt_id] = []
        
        # Generate version if not provided
        if not version:
            existing_versions = [v.version for v in self.prompts[prompt_id]]
            if existing_versions:
                # Increment patch version
                latest = max(existing_versions, key=lambda v: tuple(map(int, v.split('.'))))
                parts = latest.split('.')
                parts[2] = str(int(parts[2]) + 1)
                version = '.'.join(parts)
            else:
                version = "1.0.0"
        
        # Extract variables from content
        import re
        variables = re.findall(r'\{(\w+)\}', content)
        
        prompt_version = PromptVersion(
            prompt_id=prompt_id,
            version=version,
            content=content,
            variables=list(set(variables)),
            status=PromptStatus.DRAFT
        )
        
        self.prompts[prompt_id].append(prompt_version)
        
        self.logger.info(f"Created prompt version: {prompt_id} v{version}")
        
        return prompt_version
    
    def activate_version(
        self,
        prompt_id: str,
        version: str
    ) -> None:
        """
        Activate a prompt version.
        
        Args:
            prompt_id: Prompt identifier
            version: Version to activate
        """
        if prompt_id not in self.prompts:
            raise ValueError(f"Prompt not found: {prompt_id}")
        
        prompt_version = next(
            (v for v in self.prompts[prompt_id] if v.version == version),
            None
        )
        
        if not prompt_version:
            raise ValueError(f"Version {version} not found")
        
        # Deactivate current version
        current_version = self.active_versions.get(prompt_id)
        if current_version:
            current = next(
                (v for v in self.prompts[prompt_id] if v.version == current_version),
                None
            )
            if current:
                current.status = PromptStatus.DEPRECATED
        
        # Activate new version
        prompt_version.status = PromptStatus.ACTIVE
        self.active_versions[prompt_id] = version
        
        self.logger.info(f"Activated prompt version: {prompt_id} v{version}")
    
    def record_performance(
        self,
        prompt_id: str,
        version: str,
        metrics: Dict[str, float]
    ) -> None:
        """
        Record performance metrics for a prompt version.
        
        Args:
            prompt_id: Prompt identifier
            version: Version
            metrics: Performance metrics
        """
        if prompt_id not in self.prompts:
            return
        
        prompt_version = next(
            (v for v in self.prompts[prompt_id] if v.version == version),
            None
        )
        
        if prompt_version:
            prompt_version.performance_metrics.update(metrics)
            self.logger.debug(f"Recorded performance for {prompt_id} v{version}: {metrics}")

