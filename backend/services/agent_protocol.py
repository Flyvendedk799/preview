"""
Agent Communication Protocol - Standardized Communication for Multi-Agent AI System

Defines the protocol for communication between specialized AI agents in the preview generation system.
This ensures consistent data formats, error handling, and coordination between agents.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Types of specialized agents."""
    VISUAL_ANALYST = "visual_analyst"
    CONTENT_CURATOR = "content_curator"
    DESIGN_ARCHAEOLOGIST = "design_archaeologist"
    CONTEXT_FUSION = "context_fusion"
    REASONING_CHAIN = "reasoning_chain"
    QUALITY_CRITIC = "quality_critic"
    REFINEMENT = "refinement"
    DESIGN_OPTIMIZATION = "design_optimization"
    QUALITY_GATE_JUDGE = "quality_gate_judge"


class MessageStatus(str, Enum):
    """Message status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentMessage:
    """Standardized message format for agent communication."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_type: AgentType = AgentType.VISUAL_ANALYST
    operation: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5  # 1-10, higher = more important
    timeout: float = 30.0  # seconds
    created_at: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result["agent_type"] = self.agent_type.value
        result["status"] = MessageStatus.PENDING.value
        result["created_at"] = self.created_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Create from dictionary."""
        data = data.copy()
        data["agent_type"] = AgentType(data["agent_type"])
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class AgentResponse:
    """Standardized response format from agents."""
    message_id: str
    agent_type: AgentType
    success: bool
    output_data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    cost: float = 0.0
    latency_ms: float = 0.0
    reasoning: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    completed_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result["agent_type"] = self.agent_type.value
        result["completed_at"] = self.completed_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentResponse":
        """Create from dictionary."""
        data = data.copy()
        data["agent_type"] = AgentType(data["agent_type"])
        if isinstance(data.get("completed_at"), str):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])
        return cls(**data)


@dataclass
class FusionResult:
    """Result from context fusion agent combining multiple agent outputs."""
    fused_data: Dict[str, Any]
    source_agents: List[AgentType]
    confidence_scores: Dict[str, float]  # agent_type -> confidence
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    resolution_strategy: str = "weighted_average"
    overall_confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result["source_agents"] = [agent.value for agent in self.source_agents]
        return result


class AgentProtocol:
    """
    Protocol handler for agent communication.
    
    Provides:
    - Message serialization/deserialization
    - Validation
    - Error handling
    - Context management
    """
    
    @staticmethod
    def serialize_message(message: AgentMessage) -> str:
        """Serialize message to JSON string."""
        return json.dumps(message.to_dict(), default=str)
    
    @staticmethod
    def deserialize_message(data: str) -> AgentMessage:
        """Deserialize message from JSON string."""
        return AgentMessage.from_dict(json.loads(data))
    
    @staticmethod
    def serialize_response(response: AgentResponse) -> str:
        """Serialize response to JSON string."""
        return json.dumps(response.to_dict(), default=str)
    
    @staticmethod
    def deserialize_response(data: str) -> AgentResponse:
        """Deserialize response from JSON string."""
        return AgentResponse.from_dict(json.loads(data))
    
    @staticmethod
    def validate_message(message: AgentMessage) -> Tuple[bool, Optional[str]]:
        """
        Validate message format.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not message.operation:
            return (False, "Operation is required")
        
        if not message.input_data:
            return (False, "Input data is required")
        
        if message.priority < 1 or message.priority > 10:
            return (False, "Priority must be between 1 and 10")
        
        if message.timeout <= 0:
            return (False, "Timeout must be positive")
        
        return (True, None)
    
    @staticmethod
    def create_error_response(
        message_id: str,
        agent_type: AgentType,
        error: str,
        errors: Optional[List[str]] = None
    ) -> AgentResponse:
        """Create error response."""
        return AgentResponse(
            message_id=message_id,
            agent_type=agent_type,
            success=False,
            errors=errors or [error],
            confidence=0.0,
            cost=0.0,
            latency_ms=0.0
        )
    
    @staticmethod
    def merge_responses(
        responses: List[AgentResponse],
        strategy: str = "weighted_average"
    ) -> FusionResult:
        """
        Merge multiple agent responses into unified result.
        
        Args:
            responses: List of agent responses
            strategy: Fusion strategy (weighted_average, priority, consensus)
            
        Returns:
            FusionResult with merged data
        """
        if not responses:
            raise ValueError("Cannot merge empty response list")
        
        source_agents = [r.agent_type for r in responses]
        confidence_scores = {r.agent_type.value: r.confidence for r in responses}
        
        # Calculate overall confidence
        if strategy == "weighted_average":
            total_confidence = sum(r.confidence for r in responses)
            overall_confidence = total_confidence / len(responses) if responses else 0.0
        elif strategy == "priority":
            # Use highest confidence
            overall_confidence = max(r.confidence for r in responses)
        elif strategy == "consensus":
            # Average of responses with confidence > 0.7
            high_confidence = [r for r in responses if r.confidence > 0.7]
            overall_confidence = sum(r.confidence for r in high_confidence) / len(high_confidence) if high_confidence else 0.0
        else:
            overall_confidence = sum(r.confidence for r in responses) / len(responses) if responses else 0.0
        
        # Merge output data (simple merge, conflicts detected)
        fused_data = {}
        conflicts = []
        
        for response in responses:
            for key, value in response.output_data.items():
                if key in fused_data:
                    # Conflict detected
                    if fused_data[key] != value:
                        conflicts.append({
                            "key": key,
                            "agent": response.agent_type.value,
                            "value": value,
                            "existing_value": fused_data[key]
                        })
                        # Use value from highest confidence agent
                        if response.confidence > confidence_scores.get(key, 0.0):
                            fused_data[key] = value
                else:
                    fused_data[key] = value
        
        return FusionResult(
            fused_data=fused_data,
            source_agents=source_agents,
            confidence_scores=confidence_scores,
            conflicts=conflicts,
            resolution_strategy=strategy,
            overall_confidence=overall_confidence
        )

