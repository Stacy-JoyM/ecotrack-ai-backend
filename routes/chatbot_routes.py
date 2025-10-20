from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.ai_service import AIService
from models.chat import Conversation, ChatMessage, AIRecommendation
from app import db
from typing import Dict, Any

chatbot_bp = Blueprint('chatbot', __name__)

def get_ai_service():
    """Get AI service instance"""
    return AIService()


@chatbot_bp.route('/chat', methods=['POST'])
@jwt_required()
def send_message():
    """
    AI-002: Chatbot API endpoint for handling user queries
    Send a message to the AI chatbot and get response
    """
    try:
        user_id = get_jwt_identity()
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message content is required'}), 400
        
        message_content = data['message'].strip()
        if not message_content:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        conversation_id = data.get('conversation_id')
        
        # Send message to AI service
        ai_service = get_ai_service()
        result = ai_service.send_message(
            user_id=user_id,
            message_content=message_content,
            conversation_id=conversation_id
        )
        
        if result.get('status') == 'error':
            return jsonify({'error': result.get('error', 'Unknown error')}), 500
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """Get user's conversation history"""
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        conversations = Conversation.query.filter_by(user_id=user_id)\
            .order_by(Conversation.updated_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': {
                'conversations': [conv.serialize() for conv in conversations.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': conversations.total,
                    'pages': conversations.pages,
                    'has_next': conversations.has_next,
                    'has_prev': conversations.has_prev
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation_detail(conversation_id):
    """Get detailed conversation with messages"""
    try:
        user_id = get_jwt_identity()
        
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=user_id
        ).first()
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        ai_service = get_ai_service()
        messages = ai_service.get_conversation_history(conversation_id)
        
        return jsonify({
            'success': True,
            'data': {
                'conversation': conversation.serialize(),
                'messages': messages
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/context', methods=['POST'])
@jwt_required()
def update_context():
    """
    AI-003: Context management system for personalized responses
    Update conversation context for better personalization
    """
    try:
        user_id = get_jwt_identity()
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Context data is required'}), 400
        
        conversation_id = data.get('conversation_id')
        context_type = data.get('context_type')
        context_data = data.get('context_data')
        
        if not all([conversation_id, context_type, context_data]):
            return jsonify({
                'error': 'conversation_id, context_type, and context_data are required'
            }), 400
        
        # Verify conversation belongs to user
        conversation = Conversation.query.filter_by(
            id=conversation_id,
            user_id=user_id
        ).first()
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        ai_service = get_ai_service()
        success = ai_service.update_context(conversation_id, context_type, context_data)
        
        if success:
            return jsonify({'success': True, 'message': 'Context updated successfully'}), 200
        else:
            return jsonify({'error': 'Failed to update context'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/recommendations', methods=['POST'])
@jwt_required()
def generate_recommendations():
    """
    AI-006: Recommendation engine based on user data
    Generate AI-powered recommendations for the user
    """
    try:
        user_id = get_jwt_identity()
        
        data = request.get_json() or {}
        conversation_id = data.get('conversation_id')
        
        ai_service = get_ai_service()
        recommendations = ai_service.generate_recommendations(
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        return jsonify({
            'success': True,
            'data': {
                'recommendations': recommendations,
                'count': len(recommendations)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """Get user's AI recommendations"""
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        read_status = request.args.get('read')  # 'read', 'unread', or None for all
        
        query = AIRecommendation.query.filter_by(user_id=user_id)
        
        if read_status == 'read':
            query = query.filter_by(is_read=True)
        elif read_status == 'unread':
            query = query.filter_by(is_read=False)
        
        recommendations = query.order_by(AIRecommendation.priority_score.desc(), AIRecommendation.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': {
                'recommendations': [rec.serialize() for rec in recommendations.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': recommendations.total,
                    'pages': recommendations.pages,
                    'has_next': recommendations.has_next,
                    'has_prev': recommendations.has_prev
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/recommendations/<int:recommendation_id>/read', methods=['PUT'])
@jwt_required()
def mark_recommendation_read(recommendation_id):
    """Mark a recommendation as read"""
    try:
        user_id = get_jwt_identity()
        
        recommendation = AIRecommendation.query.filter_by(
            id=recommendation_id,
            user_id=user_id
        ).first()
        
        if not recommendation:
            return jsonify({'error': 'Recommendation not found'}), 404
        
        recommendation.is_read = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Recommendation marked as read'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/recommendations/<int:recommendation_id>/complete', methods=['PUT'])
@jwt_required()
def mark_recommendation_complete(recommendation_id):
    """Mark a recommendation as completed"""
    try:
        user_id = get_jwt_identity()
        
        recommendation = AIRecommendation.query.filter_by(
            id=recommendation_id,
            user_id=user_id
        ).first()
        
        if not recommendation:
            return jsonify({'error': 'Recommendation not found'}), 404
        
        recommendation.is_completed = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Recommendation marked as completed'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@chatbot_bp.route('/health', methods=['GET'])
def chatbot_health():
    """Health check for chatbot service"""
    try:
        # Test OpenAI connection
        ai_service = get_ai_service()
        ai_service._initialize_client()
        
        return jsonify({
            'status': 'healthy',
            'service': 'chatbot',
            'openai_configured': bool(current_app.config.get('OPENAI_API_KEY'))
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'chatbot',
            'error': str(e)
        }), 500
