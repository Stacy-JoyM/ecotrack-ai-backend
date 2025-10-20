import openai
from flask import current_app
from models.chat import Conversation, ChatMessage, ChatContext, AIRecommendation
from models.user import User
from models.carbon import Carbon
from models.activity import Activity
from app import db
from typing import List, Dict, Any, Optional
import json
import uuid
from datetime import datetime


class AIService:
    """Service for AI/LLM integration and chatbot functionality"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        api_key = current_app.config.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not configured")
        
        self.client = openai.OpenAI(api_key=api_key)
    
    def _get_carbon_footprint_system_prompt(self) -> str:
        """Get the system prompt for carbon footprint guidance"""
        return """You are an AI assistant for EcoTrack, an AI-powered personal carbon tracker. Your role is to help users reduce their carbon footprint and make more sustainable choices.

Key responsibilities:
1. Provide personalized carbon footprint guidance based on user data
2. Suggest actionable ways to reduce environmental impact
3. Answer questions about sustainability and carbon emissions
4. Motivate users with positive, encouraging language
5. Provide educational content about environmental impact

Guidelines:
- Always be encouraging and positive
- Provide specific, actionable advice
- Use data from the user's profile when available
- Focus on practical steps that users can take immediately
- Explain the environmental impact of different actions
- Be educational but not preachy
- Prioritize suggestions based on impact and feasibility

User context may include:
- Current carbon footprint data
- Activity history
- Goals and preferences
- Location and lifestyle factors

Respond in a helpful, friendly, and informative manner."""

    def _build_conversation_context(self, conversation_id: int, user_id: int) -> List[Dict[str, str]]:
        """Build conversation history for context"""
        messages = ChatMessage.query.filter_by(conversation_id=conversation_id).order_by(ChatMessage.timestamp).all()
        context_messages = []
        
        # Add system message
        context_messages.append({
            "role": "system",
            "content": self._get_carbon_footprint_system_prompt()
        })
        
        # Add user context data
        user_context = self._get_user_context(user_id)
        if user_context:
            context_messages.append({
                "role": "system",
                "content": f"User context: {json.dumps(user_context, indent=2)}"
            })
        
        # Add conversation history (limit to last 10 messages to avoid token limits)
        recent_messages = messages[-10:] if len(messages) > 10 else messages
        for message in recent_messages:
            context_messages.append({
                "role": message.role,
                "content": message.content
            })
        
        return context_messages
    
    def _get_user_context(self, user_id: int) -> Dict[str, Any]:
        """Get user-specific context for personalized responses"""
        try:
            # Get user data
            user = User.query.get(user_id)
            if not user:
                return {}
            
            # Get recent carbon data
            recent_carbon = Carbon.query.filter_by(user_id=user_id).order_by(Carbon.created_at.desc()).first()
            
            # Get recent activities
            recent_activities = Activity.query.filter_by(user_id=user_id).order_by(Activity.created_at.desc()).limit(5).all()
            
            # Get conversation context - this needs to be fixed based on actual model structure
            conversation_contexts = []
            
            context = {
                "user_id": user_id,
                "profile": {
                    "name": getattr(user, 'name', 'User'),
                    "location": getattr(user, 'location', 'Unknown'),
                    "lifestyle": getattr(user, 'lifestyle_type', 'Unknown')
                } if user else {},
                "carbon_footprint": {
                    "current_monthly": getattr(recent_carbon, 'monthly_footprint', 0) if recent_carbon else 0,
                    "target_footprint": getattr(user, 'carbon_goal', 0) if user else 0,
                    "trend": "increasing" if recent_carbon and getattr(recent_carbon, 'monthly_footprint', 0) > 1000 else "stable"
                } if recent_carbon else {},
                "recent_activities": [
                    {
                        "type": getattr(activity, 'activity_type', 'Unknown'),
                        "carbon_impact": getattr(activity, 'carbon_footprint', 0),
                        "date": getattr(activity, 'date', None).isoformat() if hasattr(activity, 'date') and getattr(activity, 'date', None) else None
                    }
                    for activity in recent_activities
                ],
                "preferences": {}
            }
            
            # Add stored context preferences
            for ctx in conversation_contexts:
                if ctx.context_type == 'preferences':
                    context["preferences"].update(ctx.context_data)
            
            return context
            
        except Exception as e:
            current_app.logger.error(f"Error getting user context: {str(e)}")
            return {}
    
    def send_message(self, user_id: int, message_content: str, conversation_id: Optional[int] = None) -> Dict[str, Any]:
        """Send a message to the AI and get response"""
        try:
            # Get or create conversation
            if conversation_id:
                conversation = Conversation.query.get(conversation_id)
                if not conversation or conversation.user_id != user_id:
                    raise ValueError("Invalid conversation")
            else:
                # Create new conversation
                session_id = str(uuid.uuid4())
                conversation = Conversation(
                    user_id=user_id,
                    session_id=session_id
                )
                db.session.add(conversation)
                db.session.flush()  # Get the ID
                conversation_id = conversation.id
            
            # Save user message
            user_message = ChatMessage(
                conversation_id=conversation_id,
                role='user',
                content=message_content
            )
            db.session.add(user_message)
            
            # Build context and get AI response
            context_messages = self._build_conversation_context(conversation_id, user_id)
            
            # Add current user message
            context_messages.append({
                "role": "user",
                "content": message_content
            })
            
            # Get AI response
            response = self.client.chat.completions.create(
                model=current_app.config.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=context_messages,
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response_content = response.choices[0].message.content
            
            # Save AI response
            ai_message = ChatMessage(
                conversation_id=conversation_id,
                role='assistant',
                content=ai_response_content,
                message_metadata={
                    "model": current_app.config.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
                    "tokens_used": response.usage.total_tokens if response.usage else 0
                }
            )
            db.session.add(ai_message)
            
            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                "conversation_id": conversation_id,
                "session_id": conversation.session_id,
                "user_message": user_message.serialize(),
                "ai_response": ai_message.serialize(),
                "status": "success"
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error in AI chat: {str(e)}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    def generate_recommendations(self, user_id: int, conversation_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Generate AI-powered recommendations based on user data"""
        try:
            user_context = self._get_user_context(user_id)
            
            # Create prompt for recommendations
            prompt = f"""
Based on this user data, generate 3-5 specific, actionable recommendations for reducing carbon footprint:

User Context: {json.dumps(user_context, indent=2)}

For each recommendation, provide:
1. A clear title (max 50 chars)
2. Detailed description explaining the impact and how to implement it
3. Specific action items (array of actionable steps)
4. Estimated carbon impact reduction (in kg CO2/month)
5. Priority score (0-100, based on impact and feasibility)
6. Recommendation type (carbon_reduction, activity_suggestion, lifestyle_change, education)

Return as JSON array with this structure.
"""
            
            response = self.client.chat.completions.create(
                model=current_app.config.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "You are an expert in carbon footprint reduction. Generate specific, actionable recommendations based on user data. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            recommendations_data = json.loads(response.choices[0].message.content)
            
            # Save recommendations to database
            saved_recommendations = []
            for rec_data in recommendations_data:
                recommendation = AIRecommendation(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    recommendation_type=rec_data.get('recommendation_type', 'carbon_reduction'),
                    title=rec_data.get('title', ''),
                    description=rec_data.get('description', ''),
                    action_items=rec_data.get('action_items', []),
                    carbon_impact=float(rec_data.get('carbon_impact', 0)),
                    priority_score=float(rec_data.get('priority_score', 0))
                )
                db.session.add(recommendation)
                saved_recommendations.append(recommendation)
            
            db.session.commit()
            
            return [rec.serialize() for rec in saved_recommendations]
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def update_context(self, conversation_id: int, context_type: str, context_data: Dict[str, Any]) -> bool:
        """Update conversation context for better personalization"""
        try:
            # Find or create context
            context = ChatContext.query.filter_by(
                conversation_id=conversation_id,
                context_type=context_type
            ).first()
            
            if not context:
                context = ChatContext(
                    conversation_id=conversation_id,
                    context_type=context_type,
                    context_data=context_data
                )
                db.session.add(context)
            else:
                context.context_data.update(context_data)
                context.updated_at = db.session.func.now()
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating context: {str(e)}")
            return False
    
    def get_conversation_history(self, conversation_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history"""
        messages = ChatMessage.query.filter_by(
            conversation_id=conversation_id
        ).order_by(ChatMessage.timestamp.desc()).limit(limit).all()
        
        return [message.serialize() for message in reversed(messages)]
