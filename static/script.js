// static/script.js
document.addEventListener('DOMContentLoaded', () => {
    const chatbox = document.getElementById('chatbox');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const clearButton = document.getElementById('clearButton');
    const loadingIndicator = document.getElementById('loading');
    const errorIndicator = document.getElementById('error-message');

    // Function to add a message to the chatbox
    function addMessage(sender, message) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender === 'user' ? 'user-message' : 'ai-message');

        const paragraph = document.createElement('p');
        // Basic sanitization (replace with a more robust library if needed for security)
        const safeMessage = message.replace(/</g, "<").replace(/>/g, ">");
        paragraph.innerHTML = safeMessage; // Use innerHTML to render potential basic markdown later if needed

        messageDiv.appendChild(paragraph);
        chatbox.appendChild(messageDiv);

        // Scroll to the bottom
        chatbox.scrollTop = chatbox.scrollHeight;
    }

    // Function to handle sending a message
    async function sendMessage() {
        const messageText = userInput.value.trim();
        if (!messageText) return; // Don't send empty messages

        // Display user message
        addMessage('user', messageText);
        userInput.value = ''; // Clear input field
        userInput.style.height = 'auto'; // Reset height after clearing

        // Show loading indicator and hide error
        loadingIndicator.style.display = 'block';
        errorIndicator.style.display = 'none';
        sendButton.disabled = true;
        clearButton.disabled = true;
        userInput.disabled = true;

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: messageText }),
            });

            if (!response.ok) {
                // Try to get error details from response body
                let errorMsg = 'Failed to get response from AI.';
                try {
                    const errorData = await response.json();
                    errorMsg = errorData.error || errorMsg;
                } catch (e) { /* Ignore parsing error */ }
                throw new Error(errorMsg);
            }

            const data = await response.json();

            // Display AI response
            addMessage('ai', data.response);

        } catch (error) {
            console.error('Error sending message:', error);
            errorIndicator.textContent = `Error: ${error.message || 'Could not connect to the server.'}`;
            errorIndicator.style.display = 'block';
            // Optionally add an error message to the chatbox itself
            // addMessage('ai', `Sorry, I encountered an error: ${error.message}`);
        } finally {
            // Hide loading indicator and re-enable input/buttons
            loadingIndicator.style.display = 'none';
            sendButton.disabled = false;
            clearButton.disabled = false;
            userInput.disabled = false;
            userInput.focus(); // Put cursor back in input
        }
    }

     // Function to clear chat history
    async function clearChat() {
        if (!confirm("Are you sure you want to clear the chat history?")) {
            return;
        }
        try {
            loadingIndicator.style.display = 'block'; // Show loading briefly
            const response = await fetch('/clear', { method: 'POST' });
            if (response.ok) {
                // Clear frontend chatbox
                chatbox.innerHTML = '<div class="message ai-message"><p>Chat history cleared. Ask me something new!</p></div>';
                console.log("Chat history cleared successfully.");
            } else {
                throw new Error('Failed to clear chat history on the server.');
            }
        } catch (error) {
            console.error('Error clearing chat:', error);
            errorIndicator.textContent = `Error: ${error.message || 'Could not clear history.'}`;
            errorIndicator.style.display = 'block';
        } finally {
             loadingIndicator.style.display = 'none';
        }
    }

    // --- Event Listeners ---

    // Send message on button click
    sendButton.addEventListener('click', sendMessage);

    // Send message on Enter key press in textarea (Shift+Enter for newline)
    userInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault(); // Prevent default newline insertion
            sendMessage();
        }
    });

    // Clear chat on button click
    clearButton.addEventListener('click', clearChat);

     // Auto-resize textarea
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto'; // Reset height
        userInput.style.height = `${userInput.scrollHeight}px`; // Set to content height
    });

});