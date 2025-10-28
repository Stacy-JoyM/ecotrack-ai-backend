import google.generativeai as genai
from config import Config

class ChatbotModel:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.active_chats = {}  # Store chat sessions by user_id
    
    def get_or_create_chat(self, user_id):
        """Get existing chat or create new one for user"""
        if user_id not in self.active_chats:
            self.active_chats[user_id] = self.model.start_chat(history=[])
        return self.active_chats[user_id]
    
    def send_message(self, user_id, message):
        """Send message and get response"""
        chat = self.get_or_create_chat(user_id)
        response = chat.send_message(message)
        return response.text
    
    def clear_chat(self, user_id):
        """Clear chat history for user"""
        if user_id in self.active_chats:
            del self.active_chats[user_id]