import google.generativeai as genai
from typing import AsyncGenerator, Optional
import re
from src.models.conversation import ConversationCategory
from src.config.env import env_config
import asyncio
import json

class AIService:
    def __init__(self):
        self.api_key = env_config.GOOGLE_AI_STUDIO_API_KEY
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Category detection patterns
        self.category_patterns = {
            ConversationCategory.CODE_GENERATION: [
                r'\b(write|create|generate|build|make)\s+(code|function|class|script|program|app)',
                r'\b(implement|develop|code)\b',
                r'\b(python|javascript|java|c\+\+|react|node|html|css)\b',
                r'write.*code',
                r'create.*function',
                r'build.*app'
            ],
            ConversationCategory.DOCUMENTATION: [
                r'\b(document|documentation|readme|api\s+docs|comments|docstring)',
                r'write.*documentation',
                r'create.*readme',
                r'api\s+documentation',
                r'code\s+comments'
            ],
            ConversationCategory.CODE_ANALYSIS: [
                r'\b(analyze|review|debug|fix|optimize|refactor|explain)\s+(code|function|script)',
                r'what\s+does\s+this\s+code',
                r'code\s+review',
                r'find\s+bugs?',
                r'optimize.*code',
                r'explain.*function'
            ],
            ConversationCategory.DATABASE_QUERIES: [
                r'\b(sql|mysql|postgresql|mongodb|database|query|select|insert|update|delete)',
                r'database.*query',
                r'write.*sql',
                r'create.*table',
                r'join.*tables?'
            ],
            ConversationCategory.CALCULATIONS: [
                r'\b(calculate|compute|solve|math|mathematics|equation|formula)',
                r'what\s+is.*\+|\-|\*|\/|\%',
                r'\d+.*[\+\-\*\/\%].*\d+',
                r'solve.*equation',
                r'mathematical.*problem'
            ]
        }

    def detect_category(self, message: str) -> ConversationCategory:
        """Detect conversation category based on message content"""
        message_lower = message.lower()
        
        # Check each category's patterns
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return category
        
        # Default to general chat if no specific category is detected
        return ConversationCategory.GENERAL_CHAT

    def get_system_prompt(self, category: ConversationCategory) -> str:
        """Get system prompt based on category"""
        system_prompts = {
            ConversationCategory.GENERAL_CHAT: """You are an AI assistant. Provide helpful, accurate, and friendly responses to general questions and conversations.""",
            
            ConversationCategory.CODE_GENERATION: """You are an expert software developer. Generate clean, efficient, and well-commented code. Always explain your code and provide usage examples when appropriate. Use best practices and modern coding standards.""",
            
            ConversationCategory.DOCUMENTATION: """You are a technical documentation specialist. Create clear, comprehensive, and well-structured documentation. Include examples, usage instructions, and any relevant technical details.""",
            
            ConversationCategory.CODE_ANALYSIS: """You are a senior code reviewer and debugger. Analyze code thoroughly, identify issues, suggest improvements, and explain complex code logic clearly. Focus on performance, security, and maintainability.""",
            
            ConversationCategory.DATABASE_QUERIES: """You are a database expert. Write efficient, secure SQL queries and database operations. Always consider performance, security (SQL injection prevention), and data integrity. Explain query logic when helpful.""",
            
            ConversationCategory.CALCULATIONS: """You are a mathematics and computation expert. Solve mathematical problems step by step, show your work, and provide clear explanations. Handle complex calculations accurately."""
        }
        return system_prompts.get(category, system_prompts[ConversationCategory.GENERAL_CHAT])

    async def generate_response_stream(
        self, 
        message: str, 
        category: ConversationCategory,
        conversation_history: list = None
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from Google AI Studio"""
        try:
            # Prepare conversation context
            system_prompt = self.get_system_prompt(category)
            
            # Build conversation history for context
            conversation_text = f"System: {system_prompt}\n\n"
            
            if conversation_history:
                for msg in conversation_history[-10:]:  # Last 10 messages for context
                    role = "Human" if msg["role"] == "user" else "Assistant"
                    conversation_text += f"{role}: {msg['content']}\n"
            
            conversation_text += f"Human: {message}\nAssistant: "
            
            # Generate response with streaming
            response = await asyncio.to_thread(
                self.model.generate_content,
                conversation_text,
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            yield f"Error: Unable to generate response. Please try again."

    async def generate_conversation_title(self, first_message: str) -> str:
        """Generate a title for the conversation based on the first message"""
        try:
            prompt = f"Generate a short, descriptive title (max 50 characters) for a conversation that starts with: '{first_message[:100]}...'. Only return the title, nothing else."
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            title = response.text.strip().strip('"').strip("'")
            return title[:50] if len(title) > 50 else title
            
        except Exception:
            return "New Conversation"
