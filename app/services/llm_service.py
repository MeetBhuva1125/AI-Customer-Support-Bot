from google import genai
from google.genai import types
import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        #initialize Gemini Client
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash-lite"

    async def generate_response(
        self, 
        query: str, 
        conversation_history: List[Dict],
        faq_context: str
    ) -> str:
        """Generate response using Gemini with conversation Context"""

        #System instructions for customer support bot
        system_instruction = f"""You are a helpful customer support assistant. 
        Your role:
        - Answer customer queries professionally and concisely
        - Use the FAQ context when relevant
        - Be empathetic and solution-oriented
        - If you cannot answer confidently, suggest escalation to human support

        {faq_context}

        Guidelines:
        - Keep responses clear and under 3 paragraphs
        - Provide actionable solutions
        - If information is missing, ask clarifying questions
        """
        
        #Build consversation history for Gemini
        #Gemini expects format: [{"role": "user/model", "parts": [{"text": "..."}]}]
        contents = []

        #Convert conversation history to Gemini format
        max_history = int(os.getenv("MAX_CONTEXT_MESSAGES", 14))
        for msg in conversation_history[-max_history:]:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({
                "role": "user",
                "parts": [{"text":query}]
            })

        #Add current query 
        contents.append({
            "role": "user",
            "parts": [{"text":query}]
        })

        try:
            #Generate reponse with Gemini
            response = self.client.models.generate_content(
                model = self.model,
                contents = contents,
                config = types.GenerateContentConfig(
                    system_instruction = system_instruction,
                    temperature = 0.7,
                    max_output_tokens = 500
                )
            )

            return response.text
        except Exception as e:
            return f"I apologize, but I'm experiencing technical difficulties. Error: {str(e)}"
        
    async def summarize_conversation(self, messages: List[Dict]) -> str:
        """Summarize conversation for escalation handoff"""
        
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}" for msg in messages
        ])
        
        prompt = f"""Summarize this customer support conversation concisel{conversation_text}
        Provide a brief summary including:
        1. Main issue/concern
        2. Key points discussed
        3. Current status

        Summary:"""

        try:
            response = self.client.models.generate_content(
                model = self.model,
                contents = prompt,
                config = types.GenearateContentConfig(
                    temperature = 0.6,
                    max_outuput_tokens=210
                )
            )

            return response.text

        except Exception as e:
            return "Unable to generate summary."
        
    async def detect_escalation_need(self,query:str, attempt_count: int) -> Dict:
        """Detect if query needs escalation using Gemini"""
        
        escalation_threshold = int(os.getenv("ESCALATION_THRESHOLD", 3))
        
        # Automatic escalation after threshold attempts
        if attempt_count >= escalation_threshold:
            return {
                'needs_escalation': True,
                'reason': f'Query attempted {attempt_count} times without resolution'
            }
        
        # Gemini-based escalation detection
        prompt = f"""Analyze if this customer query requires human escalation:
        Query: "{query}"

        Escalate if query involves:
        -Complex technical issues
        -Account-specific problems
        -Complaints or refund requests
        -Urgent/emergency matters
        -Sensitive information

        Respond in JSON format:
        {{"needs_escalation": true/false, "reason":"brief explaination"}}
        """

        try:
            reponse = self.client.models.generate_content(
                model = self.model,
                contents = prompt,
                config = types.GenearateContentConfig(
                    temperature = 0.35,
                    max_output_tokens = 100,
                    response_mime_type="application/json"
                )
            )

            import json
            result = json.loads(reponse.text)
            return result
        
        except Exception:
            return {'needs_escalation':False, 'reason':'Unable to determine'}
        