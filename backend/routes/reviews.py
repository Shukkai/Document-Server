"""
Review routes for Document Center
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime

from ..models import db, File, User, DocumentReview, Notification
from ..utils.file_utils import get_content_for_version

bp = Blueprint('reviews', __name__)


@bp.route('/request-review/<int:file_id>', methods=['POST'])
@login_required
def request_review(file_id):
    """Request a review for a document"""
    file = File.query.get_or_404(file_id)
    if file.owner_id != current_user.id:
        return {"error": "Access denied to file"}, 403
    
    if file.is_under_review:
        return {"error": "File is already under review"}, 400
    
    data = request.json
    reviewer_id = data.get('reviewer_id')
    if not reviewer_id:
        return {"error": "Reviewer ID is required"}, 400
    
    reviewer = User.query.get(reviewer_id)
    if not reviewer:
        return {"error": "Reviewer not found"}, 404
    
    if reviewer.id == current_user.id:
        return {"error": "Cannot assign review to yourself"}, 400
    
    try:
        # Refresh the file data to ensure we have the latest version information
        db.session.refresh(file)
        
        # Get the current version (which contains the latest changes)
        current_version = file.current_version or 1
        
        # For comparison purposes:
        # - modified_version should be the current version (with latest changes)
        # - original_version should be the previous version (before the changes)
        # If this is version 1, there's no previous version to compare
        if current_version > 1:
            original_version = current_version - 1
            modified_version = current_version
        else:
            # For the first version, we compare against nothing (no original)
            original_version = None
            modified_version = current_version
        
        # Create review record
        review = DocumentReview(
            file_id=file_id,
            reviewer_id=reviewer_id,
            requester_id=current_user.id,
            status='pending',
            original_version=original_version,
            modified_version=modified_version
        )
        db.session.add(review)
        
        # Mark file as under review
        file.is_under_review = True
        
        # Create notification for reviewer
        notification = Notification(
            user_id=reviewer_id,
            title="New Document Review Request",
            message=f"{current_user.username} has requested you to review '{file.filename}'",
            type="review_request",
            related_file_id=file_id,
            related_review_id=review.id
        )
        db.session.add(notification)
        db.session.commit()
        
        # Log the review creation for debugging
        current_app.logger.info(f"Review created for file {file_id}: original_version={original_version}, modified_version={modified_version}")
        
        return {"message": "Review request sent successfully", "original_version": original_version, "modified_version": modified_version}, 201
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error creating review request: {str(e)}"}, 500


@bp.route('/my-reviews', methods=['GET'])
@login_required
def get_my_reviews():
    """Get reviews assigned to current user"""
    reviews = DocumentReview.query.filter_by(reviewer_id=current_user.id).order_by(DocumentReview.requested_at.desc()).all()
    
    return jsonify([{
        "id": review.id,
        "file_id": review.file_id,
        "filename": review.file.filename,
        "requester": review.requester.username,
        "status": review.status,
        "requested_at": review.requested_at.isoformat(),
        "reviewed_at": review.reviewed_at.isoformat() if review.reviewed_at else None,
        "comments": review.comments,
        "original_version": review.original_version,
        "modified_version": review.modified_version,
        "has_comparison": review.original_version is not None and review.modified_version is not None
    } for review in reviews])


@bp.route('/review/<int:review_id>', methods=['POST'])
@login_required
def submit_review(review_id):
    """Submit a review decision"""
    review = DocumentReview.query.get_or_404(review_id)
    if review.reviewer_id != current_user.id:
        return {"error": "Access denied"}, 403
    
    if review.status != 'pending':
        return {"error": "Review has already been completed"}, 400
    
    data = request.json
    decision = data.get('decision')  # 'approved' or 'rejected'
    comments = data.get('comments', '')
    
    if decision not in ['approved', 'rejected']:
        return {"error": "Decision must be 'approved' or 'rejected'"}, 400
    
    try:
        # Update review
        review.status = decision
        review.comments = comments
        review.reviewed_at = datetime.utcnow()
        
        # Update file status
        review.file.is_under_review = False
        review.file.is_published = True
        
        # Create notification for requester
        notification = Notification(
            user_id=review.requester_id,
            title=f"Review {decision.title()}",
            message=f"Your document '{review.file.filename}' has been {decision} by {current_user.username}",
            type="review_completed",
            related_file_id=review.file_id,
            related_review_id=review_id
        )
        db.session.add(notification)
        db.session.commit()
        
        return {"message": f"Review {decision} successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error submitting review: {str(e)}"}, 500


@bp.route('/cancel-review/<int:file_id>', methods=['POST'])
@login_required
def cancel_review(file_id):
    """Cancel a pending review request"""
    file = File.query.get_or_404(file_id)
    if file.owner_id != current_user.id:
        return {"error": "Access denied to file"}, 403
    
    review = DocumentReview.query.filter_by(file_id=file_id, status='pending').first()
    if not review:
        return {"error": "No pending review found for this file"}, 404
    
    try:
        # Update review status
        review.status = 'cancelled'
        
        # Update file status
        file.is_under_review = False
        file.is_published = False
        
        # Create notification for reviewer
        notification = Notification(
            user_id=review.reviewer_id,
            title="Review Request Cancelled",
            message=f"The review request for '{file.filename}' has been cancelled by {current_user.username}",
            type="info",
            related_file_id=file_id,
            related_review_id=review.id
        )
        db.session.add(notification)
        db.session.commit()
        
        return {"message": "Review request cancelled successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error cancelling review: {str(e)}"}, 500


@bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Get user's notifications"""
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    
    return jsonify([{
        "id": notif.id,
        "title": notif.title,
        "message": notif.message,
        "type": notif.type,
        "is_read": notif.is_read,
        "created_at": notif.created_at.isoformat(),
        "related_file_id": notif.related_file_id,
        "related_review_id": notif.related_review_id
    } for notif in notifications])


@bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    """Mark a notification as read"""
    notification = Notification.query.get_or_404(notif_id)
    if notification.user_id != current_user.id:
        return {"error": "Access denied"}, 403
    
    notification.is_read = True
    db.session.commit()
    
    return {"message": "Notification marked as read"}, 200


@bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    
    for notification in notifications:
        notification.is_read = True
    
    db.session.commit()
    
    return {"message": f"Marked {len(notifications)} notifications as read"}, 200


@bp.route('/review-comparison/<int:review_id>', methods=['GET'])
@login_required
def get_review_comparison(review_id):
    """Get version comparison for a review"""
    review = DocumentReview.query.get_or_404(review_id)
    
    # Check if user is the reviewer or the requester
    if review.reviewer_id != current_user.id and review.requester_id != current_user.id:
        return {"error": "Access denied"}, 403
    
    if not review.original_version or not review.modified_version:
        return {"error": "No comparison available for this review"}, 400
    
    try:
        # Get content for both versions
        original_content = get_content_for_version(review.file, review.original_version)
        modified_content = get_content_for_version(review.file, review.modified_version)
        
        # Simple line-by-line comparison
        original_lines = original_content.splitlines()
        modified_lines = modified_content.splitlines()
        
        # Find differences
        differences = []
        max_lines = max(len(original_lines), len(modified_lines))
        
        for i in range(max_lines):
            original_line = original_lines[i] if i < len(original_lines) else ""
            modified_line = modified_lines[i] if i < len(modified_lines) else ""
            
            if original_line != modified_line:
                differences.append({
                    "line_number": i + 1,
                    "original": original_line,
                    "modified": modified_line
                })
        
        return jsonify({
            "review_id": review_id,
            "file_id": review.file_id,
            "filename": review.file.filename,
            "original_version": review.original_version,
            "modified_version": review.modified_version,
            "differences": differences,
            "total_differences": len(differences)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting review comparison for review {review_id}: {str(e)}")
        return {"error": "Failed to get comparison"}, 500 