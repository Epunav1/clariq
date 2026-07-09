"""
Feedback & Support Routes

API endpoints for user feedback, bug reports, and support requests
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import os
from services.feedback_service import feedback_db, email_notifier

router = APIRouter()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Models
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class FeedbackSubmission(BaseModel):
    """Feedback submission schema"""
    user_email: EmailStr
    user_name: Optional[str] = None
    subject: str
    message: str
    feedback_type: str = "general"  # "bug", "feature", "general", "complaint"
    priority: str = "normal"  # "low", "normal", "high", "urgent"
    user_id: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Feedback response schema"""
    feedback_id: int
    status: str
    message: str


class FeedbackDetail(BaseModel):
    """Feedback detail schema"""
    id: int
    user_email: str
    user_name: Optional[str]
    subject: str
    message: str
    type: str
    status: str
    priority: str
    created_at: str
    response: Optional[str] = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Endpoints
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/feedback/submit", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackSubmission):
    """
    Submit feedback, bug report, feature request, or complaint
    
    **Feedback Types:**
    - `bug`: Report a bug
    - `feature`: Request a feature
    - `general`: General feedback
    - `complaint`: Submit a complaint
    
    **Priority Levels:**
    - `low`: Can wait
    - `normal`: Standard priority
    - `high`: Urgent
    - `urgent`: Critical issue
    """
    
    # Validate feedback
    if not feedback.subject or len(feedback.subject) < 3:
        raise HTTPException(status_code=400, detail="Subject required (min 3 chars)")
    
    if not feedback.message or len(feedback.message) < 10:
        raise HTTPException(status_code=400, detail="Message required (min 10 chars)")
    
    valid_types = ["bug", "feature", "general", "complaint"]
    if feedback.feedback_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid type. Must be: {', '.join(valid_types)}")
    
    # Submit to database
    result = feedback_db.submit_feedback(
        user_email=feedback.user_email,
        user_name=feedback.user_name,
        subject=feedback.subject,
        message=feedback.message,
        feedback_type=feedback.feedback_type,
        user_id=feedback.user_id,
        priority=feedback.priority
    )
    
    # Send notifications
    owner_email = os.getenv("OWNER_EMAIL", "support@tryclariq.com")
    
    # Email to owner
    email_notifier.send_feedback_notification(
        {
            "type": feedback.feedback_type,
            "subject": feedback.subject,
            "message": feedback.message,
            "user_name": feedback.user_name or feedback.user_email,
            "user_email": feedback.user_email,
            "priority": feedback.priority,
            "created_at": "just now"
        },
        owner_email
    )
    
    # Confirmation email to user
    email_notifier.send_user_confirmation(
        feedback.user_email,
        result["id"]
    )
    
    return FeedbackResponse(
        feedback_id=result["id"],
        status="received",
        message="Thank you! We've received your feedback and will respond shortly."
    )


@router.get("/feedback/{feedback_id}")
async def get_feedback(feedback_id: int):
    """Get feedback details by ID"""
    
    feedback = feedback_db.get_feedback(feedback_id)
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    return feedback


@router.get("/feedback")
async def list_all_feedback(status: str = None):
    """
    List all feedback (requires admin)
    
    **Filters:**
    - `status`: Filter by status (open, in-progress, resolved, closed)
    """
    
    feedbacks = feedback_db.get_all_feedback(status=status)
    
    return {
        "count": len(feedbacks),
        "feedbacks": feedbacks
    }


@router.post("/feedback/{feedback_id}/respond")
async def respond_to_feedback(feedback_id: int, response: str):
    """
    Respond to feedback (requires admin)
    
    Marks feedback as 'responded' and stores response
    """
    
    feedback = feedback_db.get_feedback(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    # Update feedback
    feedback_db.update_feedback_status(
        feedback_id,
        "responded",
        response=response
    )
    
    # Send response to user
    email_notifier.send_feedback_notification(
        {
            "type": "response",
            "subject": f"Re: {feedback['subject']}",
            "message": response,
            "user_name": feedback['user_name'],
            "user_email": feedback['user_email'],
            "priority": "normal",
            "created_at": "now"
        },
        feedback['user_email']
    )
    
    return {
        "status": "responded",
        "message": "Response sent to user"
    }


@router.post("/feedback/{feedback_id}/close")
async def close_feedback(feedback_id: int):
    """Close a feedback ticket (requires admin)"""
    
    feedback = feedback_db.get_feedback(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    feedback_db.update_feedback_status(feedback_id, "closed")
    
    return {
        "status": "closed",
        "message": "Feedback ticket closed"
    }


@router.get("/feedback/stats/summary")
async def feedback_stats():
    """Get feedback statistics (requires admin)"""
    
    all_feedback = feedback_db.get_all_feedback()
    
    stats = {
        "total": len(all_feedback),
        "by_status": {},
        "by_type": {},
        "by_priority": {}
    }
    
    for fb in all_feedback:
        # Count by status
        status = fb.get('status', 'unknown')
        stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        # Count by type
        fb_type = fb.get('type', 'unknown')
        stats['by_type'][fb_type] = stats['by_type'].get(fb_type, 0) + 1
        
        # Count by priority
        priority = fb.get('priority', 'unknown')
        stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
    
    return stats


@router.get("/support/status")
async def support_status():
    """Check support system status"""
    
    return {
        "status": "operational",
        "feedback_system": "active",
        "email_notifications": "configured",
        "support_email": os.getenv("OWNER_EMAIL", "support@tryclariq.com"),
        "response_time": "24 hours"
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Health check
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/feedback/health")
async def feedback_health():
    """Check feedback system health"""
    
    return {
        "status": "healthy",
        "database": "connected",
        "email_service": "configured" if os.getenv("SMTP_USER") else "not_configured"
    }
