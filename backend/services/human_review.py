"""
Human-in-the-Loop System - Quality Escalation and Feedback

Manages human review for:
- Quality escalation
- Feedback loop
- Approval workflow
- Continuous learning
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ReviewStatus(str, Enum):
    """Review status."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CORRECTED = "corrected"


@dataclass
class ReviewRequest:
    """Human review request."""
    review_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    preview_id: str = ""
    url: str = ""
    quality_score: float = 0.0
    reason: str = ""
    status: ReviewStatus = ReviewStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewer_id: Optional[str] = None
    feedback: Optional[str] = None
    corrections: Optional[Dict[str, Any]] = None


class HumanReviewSystem:
    """
    Human-in-the-loop system for quality escalation and feedback.
    
    Features:
    - Quality escalation
    - Feedback loop
    - Approval workflow
    - Continuous learning
    """
    
    def __init__(self, quality_threshold: float = 0.60):
        """
        Initialize human review system.
        
        Args:
            quality_threshold: Quality threshold for escalation
        """
        self.quality_threshold = quality_threshold
        self.reviews: Dict[str, ReviewRequest] = {}
        self.logger = logging.getLogger(__name__)
    
    def should_escalate(
        self,
        quality_score: float,
        preview_data: Dict[str, Any]
    ) -> bool:
        """
        Determine if preview should be escalated for human review.
        
        Args:
            quality_score: Quality score
            preview_data: Preview data
            
        Returns:
            True if should escalate
        """
        # Escalate if quality below threshold
        if quality_score < self.quality_threshold:
            return True
        
        # Escalate if critical issues detected
        issues = preview_data.get("issues", [])
        critical_issues = [i for i in issues if "critical" in i.lower() or "error" in i.lower()]
        if critical_issues:
            return True
        
        return False
    
    def create_review_request(
        self,
        preview_id: str,
        url: str,
        quality_score: float,
        reason: str,
        preview_data: Dict[str, Any]
    ) -> ReviewRequest:
        """
        Create a human review request.
        
        Args:
            preview_id: Preview identifier
            url: URL
            quality_score: Quality score
            reason: Reason for review
            preview_data: Preview data
            
        Returns:
            ReviewRequest
        """
        review = ReviewRequest(
            preview_id=preview_id,
            url=url,
            quality_score=quality_score,
            reason=reason,
            status=ReviewStatus.PENDING
        )
        
        self.reviews[review.review_id] = review
        
        self.logger.info(
            f"Created review request: {review.review_id} "
            f"for {url}, quality: {quality_score:.2f}, reason: {reason}"
        )
        
        return review
    
    def submit_feedback(
        self,
        review_id: str,
        reviewer_id: str,
        approved: bool,
        feedback: Optional[str] = None,
        corrections: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Submit human feedback.
        
        Args:
            review_id: Review identifier
            reviewer_id: Reviewer identifier
            approved: Whether preview was approved
            feedback: Feedback text
            corrections: Corrections made
        """
        if review_id not in self.reviews:
            raise ValueError(f"Review not found: {review_id}")
        
        review = self.reviews[review_id]
        review.reviewer_id = reviewer_id
        review.reviewed_at = datetime.utcnow()
        review.feedback = feedback
        review.corrections = corrections
        
        if approved:
            review.status = ReviewStatus.APPROVED
        else:
            review.status = ReviewStatus.REJECTED
            if corrections:
                review.status = ReviewStatus.CORRECTED
        
        self.logger.info(
            f"Review {review_id} feedback submitted: "
            f"approved={approved}, reviewer={reviewer_id}"
        )
        
        # Learn from feedback (would integrate with learning system)
        self._learn_from_feedback(review)
    
    def _learn_from_feedback(
        self,
        review: ReviewRequest
    ) -> None:
        """
        Learn from human feedback to improve system.
        
        Args:
            review: Review with feedback
        """
        # This would integrate with a learning system to:
        # 1. Update prompts based on corrections
        # 2. Adjust quality thresholds
        # 3. Improve extraction logic
        # 4. Update design DNA extraction
        
        if review.corrections:
            self.logger.info(
                f"Learning from corrections: {review.corrections.keys()}"
            )
            # Would update system based on corrections

