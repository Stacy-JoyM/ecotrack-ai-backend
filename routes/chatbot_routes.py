from flask import Blueprint, request, jsonify
from models.chat import ChatbotModel

chatbot_bp = Blueprint('chatbot', __name__)
chatbot_model = ChatbotModel()

@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    """Send message to chatbot"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        message = data.get('message')
        
        if not user_id or not message:
            return jsonify({'error': 'user_id and message required'}), 400
        
        # Get response from chatbot
        response = chatbot_model.send_message(user_id, message)
        
        # Additional cleaning if needed (already done in model)
        # But we can add extra validation here
        
        return jsonify({
            'success': True,
            'response': response
        }), 200
        
    except Exception as e:
        print(f"Chatbot error: {str(e)}")  # Log error
        return jsonify({
            'success': False,
            'error': 'Failed to get response from chatbot',
            'message': str(e)
        }), 500

@chatbot_bp.route('/chat/clear', methods=['POST'])
def clear_chat():
    """Clear chat history"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        chatbot_model.clear_chat(user_id)
        
        return jsonify({
            'success': True,
            'message': 'Chat history cleared'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@chatbot_bp.route('/chat/history', methods=['GET'])
def get_chat_history():
    """Get chat history for a user (optional endpoint)"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        # Check if chat exists
        has_history = user_id in chatbot_model.active_chats
        
        return jsonify({
            'success': True,
            'has_history': has_history
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500