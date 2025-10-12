import json 
from typing import Optional, Dict
from pathlib import Path

class FAQService:
    def __init__(self):
        self.faqs = self.load_faqs()

    def load_faqs(self)->list:
        """Load FAQS from JSON file"""
        faq_path = Path("data/faqs/json")
        if faq_path.exists():
            with open(faq_path,'r') as f:
                return json.load(f)
        return []

    def find_matching_faq(self,query:str) -> Optional[Dict]:
        """Simple Keyword-based FAQ matching"""
        query_lower = query.lower()

        for faq in self.faqs:
            # Check if query keywords match FAQ keywords
            keywords = faq.get('keywords', [])
            if any(keyword.lower() in query_lower for keyword in keywords):
                return {
                    'question': faq['question'],
                    'answer': faq['answer'],
                    'confidence': 85,
                    'matched': True
                }
        
        return None
    
    def get_faq_context(self) -> str:
        """Get all FAQs as context for LLM"""
        context = "Available FAQs:\n\n"
        for idx, faq in enumerate(self.faqs, 1):
            context += f"{idx}. Q: {faq['question']}\n   A: {faq['answer']}\n\n"
        return context