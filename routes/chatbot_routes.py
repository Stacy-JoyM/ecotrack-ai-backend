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
        
        response = chatbot_model.send_message(user_id, message)
        
        return jsonify({
            'success': True,
            'response': response
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        return jsonify({'error': str(e)}), 500