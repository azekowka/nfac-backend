# A2A Chatbot Frontend

A modern, responsive web interface for the A2A Multi-Agent Chatbot system. This frontend provides a clean, intuitive chat experience with real-time communication, sentiment analysis visualization, and comprehensive session management.

## 🚀 Features

### 💬 **Chat Interface**
- Real-time messaging with the A2A chatbot system
- Modern, responsive design that works on all devices
- Typing indicators and smooth animations
- Message history with timestamps
- Character count and input validation

### 🤖 **Multi-Agent Integration**
- Connects to LangChain Agent (Google Gemini)
- Integrates with PydanticAI Agent (OpenAI + TextBlob)
- Displays AI analysis results (sentiment, keywords)
- Real-time response time tracking

### 📊 **Analytics & Monitoring**
- Live connection status indicator
- Session duration tracking
- Message count statistics
- Average response time calculation
- Real-time health checks

### 🎨 **User Experience**
- Dark/light theme support (auto-detection)
- Keyboard shortcuts for power users
- Export chat history as JSON
- Clear chat functionality
- Error handling with retry mechanisms

### ♿ **Accessibility**
- WCAG 2.1 compliant design
- Keyboard navigation support
- Screen reader friendly
- High contrast mode support
- Reduced motion preferences

## 🛠️ Quick Start

### Prerequisites
- A2A Chatbot backend running on `http://localhost:8102`
- Modern web browser (Chrome 80+, Firefox 75+, Safari 13+)

### Option 1: Simple HTTP Server (Python)
```bash
# Navigate to frontend directory
cd frontend

# Start simple HTTP server
python -m http.server 3000

# Open browser
open http://localhost:3000
```

### Option 2: Live Server (Node.js)
```bash
# Install live-server globally
npm install -g live-server

# Navigate to frontend directory
cd frontend

# Start live server
live-server --port=3000

# Browser will auto-open
```

### Option 3: Direct File Access
```bash
# Simply open index.html in your browser
open frontend/index.html
```

## 🔧 Configuration

The frontend automatically connects to the A2A chatbot at `http://localhost:8102`. To modify the connection settings, edit the `CONFIG` object in `script.js`:

```javascript
const CONFIG = {
    API_BASE_URL: 'http://localhost:8102',  // Backend URL
    HEALTH_CHECK_INTERVAL: 30000,          // Health check frequency (ms)
    TYPING_DELAY: 1000,                    // Typing indicator delay (ms)
    MAX_RETRIES: 3,                        // Connection retry attempts
    RETRY_DELAY: 2000,                     // Retry delay (ms)
    SESSION_TIMEOUT: 30 * 60 * 1000,       // Session timeout (ms)
};
```

## 📱 Usage Guide

### Basic Chat
1. Type your message in the input field
2. Press `Enter` or click the send button
3. View AI responses with analysis tags
4. Monitor connection status in the header

### Keyboard Shortcuts
- `Enter` - Send message
- `Ctrl/Cmd + K` - Clear chat
- `Ctrl/Cmd + S` - Export chat
- `Escape` - Close modals

### Features Panel
- **Statistics**: View session metrics
- **Actions**: Clear chat or export history
- **Features**: Overview of AI capabilities

### Export Chat
Click "Export Chat" to download conversation history as JSON:
```json
{
  "session_id": "session_1703123456789_abc123def",
  "export_time": "2023-12-21T10:30:45.123Z",
  "session_duration": 1234567,
  "message_count": 15,
  "average_response_time": 2.3,
  "chat_history": [...]
}
```

## 🎨 Theming

The frontend supports automatic dark/light theme detection based on system preferences. Custom CSS variables make it easy to customize:

```css
:root {
    --primary-color: #4f46e5;      /* Main brand color */
    --bg-primary: #ffffff;         /* Background color */
    --text-primary: #1e293b;       /* Text color */
    /* ... more variables */
}
```

## 🔌 API Integration

### Connection Status
The frontend continuously monitors the backend connection:
- 🟢 **Connected** - Ready to chat
- 🟡 **Connecting** - Attempting connection
- 🔴 **Disconnected** - Connection failed

### Message Format
Messages sent to the A2A backend:
```json
{
    "message": "Your message text",
    "session_id": "unique_session_identifier"
}
```

Response format:
```json
{
    "response": "AI response text",
    "analysis": {
        "sentiment": "positive|negative|neutral",
        "keywords": ["keyword1", "keyword2"],
        "response_time": 1234
    }
}
```

## 🚨 Troubleshooting

### Connection Issues
1. **Backend Not Running**
   ```bash
   cd 3lecture
   docker-compose up -d
   ```

2. **Port Conflicts**
   - Check if port 8102 is available
   - Verify A2A chatbot service status

3. **CORS Errors**
   - Ensure backend allows frontend origin
   - Use HTTP server (not file:// protocol)

### Browser Compatibility
- **Modern Features**: Uses ES6+, Fetch API, CSS Grid
- **Fallbacks**: Graceful degradation for older browsers
- **Testing**: Tested on Chrome 90+, Firefox 88+, Safari 14+

### Performance Issues
1. **Slow Responses**
   - Check network connection
   - Monitor backend logs
   - Verify API key configuration

2. **Memory Usage**
   - Chat history is stored in memory
   - Use "Clear Chat" for long sessions
   - Export and refresh for heavy usage

## 🧪 Development

### File Structure
```
frontend/
├── index.html          # Main HTML structure
├── styles.css          # Complete CSS styling
├── script.js           # JavaScript functionality
└── README.md          # This documentation
```

### Adding Features
1. **New UI Components**: Add to `index.html` and style in `styles.css`
2. **JavaScript Features**: Extend `script.js` with new functions
3. **API Integration**: Modify `sendMessage()` and related functions

### Testing
```javascript
// Access global app state for testing
console.log(window.A2A_CHATBOT.APP_STATE);

// Test connection manually
window.A2A_CHATBOT.checkConnection();

// Export chat programmatically
window.A2A_CHATBOT.exportChat();
```

## 🔒 Security

- **XSS Protection**: All user inputs are escaped
- **HTTPS Ready**: Works with secure connections
- **No Data Persistence**: Sensitive data not stored locally
- **Session Management**: Unique session IDs for tracking

## 📈 Performance

- **Lightweight**: ~25KB total (HTML + CSS + JS)
- **Responsive**: Optimized for mobile and desktop
- **Fast Loading**: Minimal dependencies
- **Efficient**: Debounced input handling

## 🤝 Integration Examples

### Custom Backend
```javascript
// Change API endpoint
CONFIG.API_BASE_URL = 'https://your-backend.com/api';

// Add authentication
const authHeaders = {
    'Authorization': 'Bearer your-token',
    'Content-Type': 'application/json'
};
```

### Embedding in Website
```html
<!-- Embed in existing site -->
<iframe 
    src="http://localhost:3000" 
    width="400" 
    height="600" 
    frameborder="0">
</iframe>
```

### React/Vue Integration
```javascript
// Export functions for framework integration
export const { sendMessage, clearChat, exportChat } = window.A2A_CHATBOT;
```

## 📝 License

Part of the NFAC Backend Project. See main project README for licensing information.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Verify backend is running and accessible
3. Check browser developer console for errors
4. Ensure API keys are properly configured in backend

---

**Happy Chatting! 🚀** 