/**
 * JavaScript for the AI chatbot functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const courseSelect = document.getElementById('course-context');
    
    // Function to add a message to the chat window
    function addMessage(message, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'message user-message' : 'message bot-message';
        
        // Create message content
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = message;
        
        // Create timestamp
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        const now = new Date();
        messageTime.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // Add content and timestamp to message div
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);
        
        // Add message to chat window
        chatMessages.appendChild(messageDiv);
        
        // Scroll to the bottom of the chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Handle chat form submission
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const message = chatInput.value.trim();
            if (!message) return;
            
            // Add user message to chat
            addMessage(message, true);
            
            // Clear input
            chatInput.value = '';
            
            // Get selected course context
            const courseId = courseSelect ? courseSelect.value : null;
            
            // Loading indicator
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message bot-message';
            loadingDiv.innerHTML = '<div class="spinner-border spinner-border-sm text-light" role="status"></div> Thinking...';
            chatMessages.appendChild(loadingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // Send message to server for AI processing
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    course_id: courseId
                })
            })
            .then(response => response.json())
            .then(data => {
                // Remove loading indicator
                chatMessages.removeChild(loadingDiv);
                
                // Add bot response
                if (data.status === 'success') {
                    addMessage(data.response, false);
                } else {
                    addMessage('Sorry, I encountered an error. Please try again.', false);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                // Remove loading indicator
                chatMessages.removeChild(loadingDiv);
                
                // Add error message
                addMessage('Sorry, I encountered an error connecting to my brain. Please try again.', false);
            });
        });
    }
    
    // Handle Enter key in chat input
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
    }
    
    // Scroll to the bottom of the chat when page loads
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
