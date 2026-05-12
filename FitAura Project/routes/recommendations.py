from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from models.database import db, Recommendation, Preference
import json
import traceback

recommendations_bp = Blueprint('recommendations', __name__)

@recommendations_bp.route('/recommendations')
@login_required
def view_recommendations():
    """View all saved recommendations (registered users only)"""
    try:
        print("🔄 Loading recommendations page...")
        
        # Get recommendations
        recommendations = Recommendation.query.filter_by(
            user_id=current_user.id,
            is_saved=True
        ).order_by(Recommendation.created_at.desc()).all()
        
        print(f"✅ Found {len(recommendations)} recommendations")
        
        # Parse image paths for each recommendation
        for rec in recommendations:
            if rec.image_paths:
                try:
                    rec.image_paths_list = json.loads(rec.image_paths)
                    print(f"📷 Recommendation {rec.id}: {len(rec.image_paths_list)} images")
                except Exception as e:
                    print(f"⚠️ Error parsing image paths for rec {rec.id}: {e}")
                    rec.image_paths_list = []
            else:
                rec.image_paths_list = []
        
        return render_template('recommendations.html', recommendations=recommendations)
        
    except Exception as e:
        print(f"❌ Error loading recommendations: {e}")
        traceback.print_exc()
        flash(f'Error loading recommendations: {str(e)}', 'error')
        return redirect(url_for('index'))

@recommendations_bp.route('/profile')
@login_required
def profile():
    """View user profile (registered users only)"""
    try:
        print("🔄 Loading profile page...")
        
        user = current_user
        
        # Get statistics
        recommendation_count = Recommendation.query.filter_by(
            user_id=user.id,
            is_saved=True
        ).count()
        
        # Get workflow breakdown
        workflow_stats = db.session.query(
            Recommendation.workflow_type,
            db.func.count(Recommendation.id)
        ).filter_by(
            user_id=user.id,
            is_saved=True
        ).group_by(Recommendation.workflow_type).all()
        
        workflow_breakdown = {wf: count for wf, count in workflow_stats}
        
        # Get recent preferences
        recent_preferences = Preference.query.filter_by(
            user_id=user.id
        ).order_by(Preference.timestamp.desc()).limit(10).all()
        
        print(f"✅ Profile loaded: {user.username}, {recommendation_count} recs")
        
        return render_template(
            'profile.html',
            user=user,
            recommendation_count=recommendation_count,
            workflow_breakdown=workflow_breakdown,
            recent_preferences=recent_preferences
        )
        
    except Exception as e:
        print(f"❌ Error loading profile: {e}")
        traceback.print_exc()
        flash(f'Error loading profile: {str(e)}', 'error')
        return redirect(url_for('index'))

# API Routes

@recommendations_bp.route('/api/recommendations')
@login_required
def get_recommendations_api():
    """Get recommendations via API"""
    try:
        recommendations = Recommendation.query.filter_by(
            user_id=current_user.id,
            is_saved=True
        ).order_by(Recommendation.created_at.desc()).all()
        
        recommendations_list = []
        for rec in recommendations:
            recommendations_list.append({
                'id': rec.id,
                'workflow_type': rec.workflow_type,
                'recommendation_text': rec.recommendation_text,
                'image_paths': rec.image_paths,
                'sd_prompt': rec.sd_prompt,
                'created_at': rec.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'success': True,
            'recommendations': recommendations_list
        })
    except Exception as e:
        print(f"Error loading recommendations: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load recommendations'
        }), 500

@recommendations_bp.route('/api/recommendations/<int:rec_id>')
@login_required
def get_recommendation_detail(rec_id):
    """Get specific recommendation by ID"""
    try:
        recommendation = Recommendation.query.filter_by(
            id=rec_id,
            user_id=current_user.id
        ).first()
        
        if not recommendation:
            return jsonify({
                'success': False,
                'error': 'Recommendation not found'
            }), 404
        
        return jsonify({
            'success': True,
            'recommendation': {
                'id': recommendation.id,
                'workflow_type': recommendation.workflow_type,
                'recommendation_text': recommendation.recommendation_text,
                'image_paths': recommendation.image_paths,
                'sd_prompt': recommendation.sd_prompt,
                'created_at': recommendation.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        print(f"Error loading recommendation: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load recommendation'
        }), 500

@recommendations_bp.route('/api/recommendations/<int:rec_id>/delete', methods=['POST', 'DELETE'])
@login_required
def delete_recommendation(rec_id):
    """Delete a recommendation"""
    try:
        recommendation = Recommendation.query.filter_by(
            id=rec_id,
            user_id=current_user.id
        ).first()
        
        if recommendation:
            db.session.delete(recommendation)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Recommendation deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Recommendation not found'
            }), 404
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting recommendation: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete recommendation'
        }), 500

@recommendations_bp.route('/api/save-recommendation', methods=['POST'])
@login_required
def save_recommendation():
    """Save a recommendation (mark as saved)"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    recommendation_id = data.get('recommendation_id')
    
    if recommendation_id:
        # Update existing recommendation
        try:
            recommendation = Recommendation.query.filter_by(
                id=recommendation_id,
                user_id=current_user.id
            ).first()
            
            if recommendation:
                recommendation.is_saved = True
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Recommendation saved successfully',
                    'recommendation_id': recommendation.id
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Recommendation not found'
                }), 404
        except Exception as e:
            db.session.rollback()
            print(f"Error updating recommendation: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to save recommendation'
            }), 500
    else:
        # Create new recommendation
        recommendation_text = data.get('recommendation_text')
        image_paths = data.get('image_paths', [])
        session_id = data.get('session_id', 'manual')
        workflow_type = data.get('workflow_type', 'generate_new')
        sd_prompt = data.get('sd_prompt')
        
        if not recommendation_text:
            return jsonify({
                'success': False,
                'error': 'Recommendation text is required'
            }), 400
        
        try:
            image_paths_str = json.dumps(image_paths) if isinstance(image_paths, list) else image_paths
            
            recommendation = Recommendation(
                user_id=current_user.id,
                session_id=session_id,
                workflow_type=workflow_type,
                recommendation_text=recommendation_text,
                image_paths=image_paths_str,
                sd_prompt=sd_prompt,
                is_saved=True
            )
            
            db.session.add(recommendation)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Recommendation saved successfully',
                'recommendation_id': recommendation.id
            })
        except Exception as e:
            db.session.rollback()
            print(f"Error saving recommendation: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to save recommendation'
            }), 500