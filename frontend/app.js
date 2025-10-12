// ===== CONFIGURATION =====
const API_BASE_URL = 'http://localhost:8000';

// ===== STATE MANAGEMENT =====
let currentSessionId = null;
let isWaitingForResponse = false;

// ===== DOM ELEMENTS =====
const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const typingIndicator = document.getElementById('typingIndicator');
const sessionInfo = document.getElementById('sessionInfo');
const sessionText = document.getElementById('sessionText');
const newSessionBtn = document.getElementById('newSessionBtn');
const clearChatBtn = document.getElementById('clearChatBtn');
const minimizeBtn = document.getElementById('minimizeBtn');
const escalationModal = document.getElementById('escalationModal');
const closeModal = document.getElementById('closeModal');
const continueChattingBtn = document.getElementById('continueChattingBtn');
const viewTicketBtn = document.getElementById('viewTicketBtn');

// ===== UTILITY FUNCTIONS =====
function formatTime(date = new Date()) {
    return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
    });
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    typingIndicator.style.display = 'flex';
    scrollToBottom();
}

function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
}

function disableInput() {
    messageInput.disabled = true;
    sendBtn.disabled = true;
    isWaitingForResponse = true;
}

function enableInput() {
    messageInput.disabled = false;
    sendBtn.disabled = false;
    isWaitingForResponse = false;
    messageInput.focus();
}

// ===== MESSAGE RENDERING =====
function addMessage(content, isUser = false, options = {}) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    
    const avatarUrl = isUser 
        ? 'https://api.dicebear.com/7.x/avataaars/svg?seed=user'
        : 'https://api.dicebear.com/7.x/bottts/svg?seed=support';
    
    let messageHTML = `
        <div class="message-avatar">
            <img src="${avatarUrl}" alt="${isUser ? 'User' : 'Bot'}">
        </div>
        <div class="message-content">
            <div class="message-bubble ${options.error ? 'error-message' : ''} ${options.success ? 'success-message' : ''}">
                <p>${content}</p>
            </div>
            <span class="message-time">${formatTime()}</span>
        </div>
    `;
    
    messageDiv.innerHTML = messageHTML;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
    
    return messageDiv;
}

function addFAQBadge(messageDiv, confidence) {
    const bubble = messageDiv.querySelector('.message-bubble');
    const badge = document.createElement('div');
    badge.style.cssText = `
        display: inline-block;
        background: #10b981;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        margin-top: 8px;
    `;
    badge.innerHTML = `<i class="fas fa-check-circle"></i> FAQ Match (${confidence}%)`;
    bubble.appendChild(badge);
}

// ===== API FUNCTIONS =====
async function createSession() {
    try {
        sessionText.textContent = 'Creating session...';
        const response = await fetch(`${API_BASE_URL}/session/new`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to create session');
        }
        
        const data = await response.json();
        currentSessionId = data.session_id;
        sessionText.textContent = `Session: ${currentSessionId.substring(0, 8)}...`;
        console.log('Session created:', currentSessionId);
        return currentSessionId;
        
    } catch (error) {
        console.error('Error creating session:', error);
        sessionText.textContent = 'Session creation failed';
        addMessage('⚠️ Failed to create session. Please refresh the page.', false, { error: true });
        return null;
    }
}

async function sendMessage(message) {
    if (!currentSessionId) {
        await createSession();
        if (!currentSessionId) return;
    }
    
    try {
        disableInput();
        showTypingIndicator();
        
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                message: message
            })
        });
        
        hideTypingIndicator();
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Add bot response
        const botMessage = addMessage(data.response, false);
        
        // Add FAQ badge if matched
        if (data.faq_matched && data.confidence) {
            addFAQBadge(botMessage, data.confidence);
        }
        
        // Handle escalation
        if (data.escalated && data.escalation_info) {
            showEscalationModal(data.escalation_info);
        }
        
        enableInput();
        
    } catch (error) {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        addMessage('❌ Sorry, I encountered an error. Please try again.', false, { error: true });
        enableInput();
    }
}

async function loadChatHistory() {
    if (!currentSessionId) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat/history/${currentSessionId}`);
        
        if (!response.ok) {
            throw new Error('Failed to load history');
        }
        
        const data = await response.json();
        
        // Clear existing messages except welcome
        const welcomeMsg = chatMessages.querySelector('.welcome-message');
        chatMessages.innerHTML = '';
        if (welcomeMsg) {
            chatMessages.appendChild(welcomeMsg);
        }
        
        // Add history messages
        data.messages.forEach(msg => {
            addMessage(msg.content, msg.role === 'user');
        });
        
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

// ===== ESCALATION MODAL =====
function showEscalationModal(escalationInfo) {
    const ticketId = document.getElementById('ticketId');
    const ticketPriority = document.getElementById('ticketPriority');
    
    ticketId.textContent = escalationInfo.ticket_id;
    ticketPriority.textContent = escalationInfo.priority.charAt(0).toUpperCase() + escalationInfo.priority.slice(1);
    
    // Set priority color
    const priorityColors = {
        high: '#ef4444',
        medium: '#f59e0b',
        normal: '#10b981'
    };
    ticketPriority.style.background = priorityColors[escalationInfo.priority] || priorityColors.normal;
    
    escalationModal.classList.add('active');
}

function hideEscalationModal() {
    escalationModal.classList.remove('active');
}

// ===== EVENT HANDLERS =====
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message || isWaitingForResponse) return;
    
    // Add user message to UI
    addMessage(message, true);
    messageInput.value = '';
    
    // Send to API
    await sendMessage(message);
});

// Quick reply buttons
chatMessages.addEventListener('click', async (e) => {
    if (e.target.classList.contains('quick-reply-btn') || 
        e.target.closest('.quick-reply-btn')) {
        
        const btn = e.target.classList.contains('quick-reply-btn') 
            ? e.target 
            : e.target.closest('.quick-reply-btn');
        
        const message = btn.dataset.message;
        if (message && !isWaitingForResponse) {
            addMessage(message, true);
            await sendMessage(message);
        }
    }
});

// New session button
newSessionBtn.addEventListener('click', async () => {
    if (confirm('Start a new session? Current conversation will be saved.')) {
        currentSessionId = null;
        const welcomeMsg = chatMessages.querySelector('.welcome-message');
        chatMessages.innerHTML = '';
        if (welcomeMsg) {
            chatMessages.appendChild(welcomeMsg);
        }
        await createSession();
    }
});

// Clear chat button
clearChatBtn.addEventListener('click', () => {
    if (confirm('Clear all messages? This cannot be undone.')) {
        const welcomeMsg = chatMessages.querySelector('.welcome-message');
        chatMessages.innerHTML = '';
        if (welcomeMsg) {
            chatMessages.appendChild(welcomeMsg);
        }
    }
});

// Minimize button (demo only)
minimizeBtn.addEventListener('click', () => {
    alert('Minimize functionality - would collapse chat in production');
});

// Modal close buttons
closeModal.addEventListener('click', hideEscalationModal);
continueChattingBtn.addEventListener('click', hideEscalationModal);
viewTicketBtn.addEventListener('click', () => {
    alert('View ticket details - would redirect to ticket system');
    hideEscalationModal();
});

// Close modal on outside click
escalationModal.addEventListener('click', (e) => {
    if (e.target === escalationModal) {
        hideEscalationModal();
    }
});

// ===== INITIALIZATION =====
async function init() {
    console.log('Initializing chat application...');
    await createSession();
    messageInput.focus();
}

// Start application when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Auto-resize textarea (bonus feature)
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});
