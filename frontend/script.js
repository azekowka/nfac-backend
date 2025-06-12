// Configuration
const CONFIG = {
    API_BASE_URL: 'http://localhost:8102',
    HEALTH_CHECK_INTERVAL: 30000, // 30 seconds
    TYPING_DELAY: 1000, // 1 second
    MAX_RETRIES: 3,
    RETRY_DELAY: 2000, // 2 seconds
    SESSION_TIMEOUT: 30 * 60 * 1000, // 30 minutes
};

// Global state
const APP_STATE = {
    isConnected: false,
    messageCount: 0,
    sessionStartTime: Date.now(),
    responseTimes: [],
    retryCount: 0,
    sessionId: generateSessionId(),
    chatHistory: [],
    currentTask: null,
};

// DOM Elements
const elements = {
    statusDot: document.getElementById('statusDot'),
    statusText: document.getElementById('statusText'),
    chatMessages: document.getElementById('chatMessages'),
    messageInput: document.getElementById('messageInput'),
    sendButton: document.getElementById('sendButton'),
    chatForm: document.getElementById('chatForm'),
    typingIndicator: document.getElementById('typingIndicator'),
    charCount: document.getElementById('charCount'),
    messageCount: document.getElementById('messageCount'),
    sessionTime: document.getElementById('sessionTime'),
    avgResponse: document.getElementById('avgResponse'),
    clearChatBtn: document.getElementById('clearChatBtn'),
    exportChatBtn: document.getElementById('exportChatBtn'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    errorModal: document.getElementById('errorModal'),
    errorMessage: document.getElementById('errorMessage'),
    closeErrorModal: document.getElementById('closeErrorModal'),
    retryConnection: document.getElementById('retryConnection'),
};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    showLoading(true);
    setupEventListeners();
    await checkConnection();
    startSessionTimer();
    showLoading(false);
    
    // Auto-focus input
    elements.messageInput.focus();
}

function setupEventListeners() {
    // Chat form submission
    elements.chatForm.addEventListener('submit', handleMessageSubmit);
    
    // Input events
    elements.messageInput.addEventListener('input', handleInputChange);
    elements.messageInput.addEventListener('keydown', handleKeyDown);
    
    // Action buttons
    elements.clearChatBtn.addEventListener('click', clearChat);
    elements.exportChatBtn.addEventListener('click', exportChat);
    
    // Modal events
    elements.closeErrorModal.addEventListener('click', hideErrorModal);
    elements.retryConnection.addEventListener('click', retryConnection);
    
    // Click outside modal to close
    elements.errorModal.addEventListener('click', (e) => {
        if (e.target === elements.errorModal) {
            hideErrorModal();
        }
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case 'Enter':
                    e.preventDefault();
                    if (elements.messageInput.value.trim()) {
                        handleMessageSubmit(e);
                    }
                    break;
                case 'k':
                    e.preventDefault();
                    clearChat();
                    break;
                case 's':
                    e.preventDefault();
                    exportChat();
                    break;
            }
        }
        
        if (e.key === 'Escape') {
            hideErrorModal();
        }
    });
}

async function checkConnection() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/health`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            signal: AbortSignal.timeout(5000),
        });
        
        if (response.ok) {
            setConnectionStatus(true);
            APP_STATE.retryCount = 0;
            scheduleHealthCheck();
        } else {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
    } catch (error) {
        console.error('Connection check failed:', error);
        setConnectionStatus(false, error.message);
        scheduleRetry();
    }
}

function setConnectionStatus(connected, errorMsg = '') {
    APP_STATE.isConnected = connected;
    elements.statusDot.className = `status-dot ${connected ? 'connected' : 'error'}`;
    elements.statusText.textContent = connected ? 'Connected' : `Disconnected${errorMsg ? `: ${errorMsg}` : ''}`;
    elements.sendButton.disabled = !connected || !elements.messageInput.value.trim();
    
    if (!connected && !elements.errorModal.classList.contains('show')) {
        showErrorModal(errorMsg || 'Connection lost to A2A Chatbot service');
    }
}

function scheduleHealthCheck() {
    setTimeout(checkConnection, CONFIG.HEALTH_CHECK_INTERVAL);
}

function scheduleRetry() {
    if (APP_STATE.retryCount < CONFIG.MAX_RETRIES) {
        APP_STATE.retryCount++;
        setTimeout(checkConnection, CONFIG.RETRY_DELAY * APP_STATE.retryCount);
    }
}

async function handleMessageSubmit(e) {
    e.preventDefault();
    
    const message = elements.messageInput.value.trim();
    if (!message || !APP_STATE.isConnected) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input and show typing indicator
    elements.messageInput.value = '';
    updateCharCount();
    showTypingIndicator(true);
    
    try {
        const startTime = Date.now();
        const response = await sendMessage(message);
        const endTime = Date.now();
        const responseTime = endTime - startTime;
        
        // Update stats
        APP_STATE.responseTimes.push(responseTime);
        APP_STATE.messageCount++;
        updateStats();
        
        // Add assistant response
        addMessage(response.response, 'assistant', response.analysis);
        
        // Store in chat history
        APP_STATE.chatHistory.push(
            { role: 'user', content: message, timestamp: startTime },
            { role: 'assistant', content: response.response, timestamp: endTime, analysis: response.analysis }
        );
        
    } catch (error) {
        console.error('Failed to send message:', error);
        addMessage(
            'Sorry, I encountered an error processing your message. Please try again.',
            'assistant',
            null,
            true
        );
        setConnectionStatus(false, error.message);
    } finally {
        showTypingIndicator(false);
        elements.messageInput.focus();
    }
}

async function sendMessage(message) {
    const response = await fetch(`${CONFIG.API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            session_id: APP_STATE.sessionId,
        }),
        signal: AbortSignal.timeout(30000), // 30 second timeout
    });
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
}

function addMessage(content, sender, analysis = null, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    if (isError) bubble.style.borderLeft = '4px solid var(--error-color)';
    bubble.textContent = content;
    
    const meta = document.createElement('div');
    meta.className = 'message-meta';
    
    const timestamp = document.createElement('span');
    timestamp.textContent = new Date().toLocaleTimeString();
    meta.appendChild(timestamp);
    
    messageContent.appendChild(bubble);
    
    // Add analysis tags for assistant messages
    if (sender === 'assistant' && analysis && !isError) {
        const tags = document.createElement('div');
        tags.className = 'analysis-tags';
        
        if (analysis.sentiment) {
            const sentimentTag = document.createElement('span');
            sentimentTag.className = `tag sentiment-${analysis.sentiment.toLowerCase()}`;
            sentimentTag.textContent = `Sentiment: ${analysis.sentiment}`;
            tags.appendChild(sentimentTag);
        }
        
        if (analysis.keywords && analysis.keywords.length > 0) {
            analysis.keywords.slice(0, 3).forEach(keyword => {
                const keywordTag = document.createElement('span');
                keywordTag.className = 'tag';
                keywordTag.textContent = keyword;
                tags.appendChild(keywordTag);
            });
        }
        
        if (analysis.response_time) {
            const timeTag = document.createElement('span');
            timeTag.className = 'tag';
            timeTag.textContent = `${analysis.response_time}ms`;
            tags.appendChild(timeTag);
        }
        
        if (tags.children.length > 0) {
            messageContent.appendChild(tags);
        }
    }
    
    messageContent.appendChild(meta);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    
    // Remove welcome message if it exists
    const welcomeMessage = elements.chatMessages.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function handleInputChange(e) {
    updateCharCount();
    updateSendButton();
}

function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (elements.messageInput.value.trim() && APP_STATE.isConnected) {
            handleMessageSubmit(e);
        }
    }
}

function updateCharCount() {
    const length = elements.messageInput.value.length;
    elements.charCount.textContent = `${length}/1000`;
    
    if (length > 800) {
        elements.charCount.style.color = 'var(--warning-color)';
    } else if (length > 900) {
        elements.charCount.style.color = 'var(--error-color)';
    } else {
        elements.charCount.style.color = 'var(--text-muted)';
    }
}

function updateSendButton() {
    const hasText = elements.messageInput.value.trim().length > 0;
    elements.sendButton.disabled = !hasText || !APP_STATE.isConnected;
}

function showTypingIndicator(show) {
    if (show) {
        elements.typingIndicator.classList.add('show');
        scrollToBottom();
    } else {
        elements.typingIndicator.classList.remove('show');
    }
}

function scrollToBottom() {
    setTimeout(() => {
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    }, 100);
}

function updateStats() {
    elements.messageCount.textContent = APP_STATE.messageCount;
    
    if (APP_STATE.responseTimes.length > 0) {
        const avgTime = APP_STATE.responseTimes.reduce((a, b) => a + b, 0) / APP_STATE.responseTimes.length;
        elements.avgResponse.textContent = `${(avgTime / 1000).toFixed(1)}s`;
    }
}

function startSessionTimer() {
    setInterval(() => {
        const elapsed = Date.now() - APP_STATE.sessionStartTime;
        const minutes = Math.floor(elapsed / 60000);
        const seconds = Math.floor((elapsed % 60000) / 1000);
        elements.sessionTime.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }, 1000);
}

function clearChat() {
    const messages = elements.chatMessages.querySelectorAll('.message');
    messages.forEach(msg => msg.remove());
    
    // Reset welcome message
    const welcomeDiv = document.createElement('div');
    welcomeDiv.className = 'welcome-message';
    welcomeDiv.innerHTML = `
        <div class="welcome-content">
            <i class="fas fa-robot welcome-icon"></i>
            <h3>Welcome back to A2A Chatbot!</h3>
            <p>I'm ready to help you with thoughtful, analyzed responses.</p>
            <p>Chat cleared - let's start fresh!</p>
        </div>
    `;
    elements.chatMessages.appendChild(welcomeDiv);
    
    // Reset stats
    APP_STATE.messageCount = 0;
    APP_STATE.responseTimes = [];
    APP_STATE.chatHistory = [];
    updateStats();
    
    elements.messageInput.focus();
}

function exportChat() {
    if (APP_STATE.chatHistory.length === 0) {
        alert('No chat history to export.');
        return;
    }
    
    const exportData = {
        session_id: APP_STATE.sessionId,
        export_time: new Date().toISOString(),
        session_duration: Date.now() - APP_STATE.sessionStartTime,
        message_count: APP_STATE.messageCount,
        average_response_time: APP_STATE.responseTimes.reduce((a, b) => a + b, 0) / APP_STATE.responseTimes.length,
        chat_history: APP_STATE.chatHistory,
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `a2a-chat-export-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function showLoading(show) {
    if (show) {
        elements.loadingOverlay.classList.add('show');
    } else {
        elements.loadingOverlay.classList.remove('show');
    }
}

function showErrorModal(message) {
    elements.errorMessage.textContent = message;
    elements.errorModal.classList.add('show');
}

function hideErrorModal() {
    elements.errorModal.classList.remove('show');
}

function retryConnection() {
    hideErrorModal();
    APP_STATE.retryCount = 0;
    checkConnection();
}

function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Error handling
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
    if (!APP_STATE.isConnected) {
        showErrorModal('An unexpected error occurred. Please refresh the page.');
    }
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
    e.preventDefault();
});

// Visibility change handling
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && !APP_STATE.isConnected) {
        checkConnection();
    }
});

// Service Worker registration (for PWA support)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}

// Export for testing
window.A2A_CHATBOT = {
    APP_STATE,
    CONFIG,
    checkConnection,
    sendMessage,
    clearChat,
    exportChat,
}; 