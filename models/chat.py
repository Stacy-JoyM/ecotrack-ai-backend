import google.generativeai as genai
from config import Config

class ChatbotModel:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        
        # System instruction to focus on carbon emissions
        system_instruction = """
        You are a specialized chatbot focused exclusively on carbon emissions and climate change.
        
        Your role:
        - Answer questions about carbon emissions, greenhouse gases, and their impact
        - Provide information about carbon footprints (personal, corporate, national)
        - Explain carbon reduction strategies and sustainability practices
        - Discuss carbon offsetting, carbon credits, and net-zero initiatives
        - Share data about emission sources (transportation, energy, agriculture, industry)
        - Explain climate policies and international agreements (Paris Agreement, etc.)
        
        Important guidelines:
        - If a question is NOT related to carbon emissions or climate change, politely redirect the user back to the topic
        - Say something like: "I'm specialized in carbon emissions and climate topics. Could you ask me something about carbon footprints, greenhouse gases, or climate change?"
        - Be informative, accurate, and helpful within your domain
        - Use data and examples when possible
        
        Stay focused on your specialty: carbon emissions and climate change.
        """
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash',
            system_instruction=system_instruction
        )
        
        self.active_chats = {}  # Store chat sessions by user_id
        self.last_request_time = {}  # Track last request time per user
        
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