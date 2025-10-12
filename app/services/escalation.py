from typing import Dict, List
from datetime import datetime

class EscalationService:
    def __init__(self):
        self.escalation_queue = []
    
    def escalate_session(
        self, 
        session_id: str, 
        reason: str, 
        conversation_summary: str,
        messages: List[Dict]
    ) -> Dict:
        """Escalate session to human support"""
        
        escalation_ticket = {
            'ticket_id': f"ESC-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            'session_id': session_id,
            'reason': reason,
            'summary': conversation_summary,
            'escalated_at': datetime.utcnow().isoformat(),
            'status': 'pending',
            'priority': self._calculate_priority(reason, messages)
        }
        
        self.escalation_queue.append(escalation_ticket)
        
        return escalation_ticket
    
    def _calculate_priority(self, reason: str, messages: List[Dict]) -> str:
        """Calculate escalation priority"""
        urgent_keywords = ['urgent', 'emergency', 'critical', 'immediately', 'asap']
        
        # Check reason and recent messages for urgency
        text_to_check = reason.lower()
        for msg in messages[-3:]:  # Check last 3 messages
            text_to_check += " " + msg.get('content', '').lower()
        
        if any(keyword in text_to_check for keyword in urgent_keywords):
            return 'high'
        elif len(messages) > 8:
            return 'medium'
        else:
            return 'normal'
    
    def get_escalation_status(self, session_id: str) -> Dict:
        """Get escalation status for a session"""
        for ticket in self.escalation_queue:
            if ticket['session_id'] == session_id:
                return ticket
        
        return {'status': 'not_escalated'}
