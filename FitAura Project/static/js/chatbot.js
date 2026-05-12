/**
 * FITAURA - Enhanced Chatbot Interface
 * Supports: Guest mode, 5 workflows, intent routing, localStorage
 */

// State management
const chatState = {
    currentQuestion: 1,
    totalQuestions: 11,
    answers: {},
    isProcessing: false,
    sessionId: null,
    currentWorkflow: 'generate',
    currentRecommendation: null,
    conversationContext: {}
};

// Guest storage helper
const GuestStorage = {
    save(key, data) {
        if (typeof IS_GUEST !== 'undefined' && IS_GUEST) {
            localStorage.setItem(`fitaura_${key}`, JSON.stringify(data));
            console.log(`💾 Saved to localStorage: ${key}`);
        }
    },
    
    load(key) {
        if (typeof IS_GUEST !== 'undefined' && IS_GUEST) {
            const data = localStorage.getItem(`fitaura_${key}`);
            return data ? JSON.parse(data) : null;
        }
        return null;
    },
    
    saveRecommendation(rec) {
        const recs = this.load('recommendations') || [];
        recs.unshift(rec);
        this.save('recommendations', recs.slice(0, 20));
    },
    
    getRecommendations() {
        return this.load('recommendations') || [];
    }
};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeChatbot();
    setupEventListeners();
});

function initializeChatbot() {
    const userInput = document.getElementById('userInput');
    const charCount = document.getElementById('charCount');
    
    if (userInput && charCount) {
        userInput.addEventListener('input', function() {
            charCount.textContent = this.value.length;
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        userInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
}

function setupEventListeners() {
    const sendButton = document.getElementById('sendButton');
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
}

function loadFirstQuestion() {
    fetch('/chatbot/get-question/1')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayBotMessage(data.question.question, data.question);
                updateProgress();
            }
        })
        .catch(error => {
            console.error('Error loading question:', error);
            displayBotMessage("Let's start! What is the occasion for your outfit?");
        });
}

function sendMessage() {
    const userInput = document.getElementById('userInput');
    const message = userInput.value.trim();
    
    if (!message || chatState.isProcessing) return;
    
    displayUserMessage(message);
    
    userInput.value = '';
    document.getElementById('charCount').textContent = '0';
    userInput.style.height = 'auto';
    
    processAnswer(message);
}

function displayUserMessage(message) {
    const messagesContainer = document.getElementById('chatMessages');
    
    const messageGroup = document.createElement('div');
    messageGroup.className = 'message-group user';
    
    messageGroup.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-user"></i>
        </div>
        <div class="message-content">
            <div class="message-bubble">
                <p>${escapeHtml(message)}</p>
            </div>
            <div class="message-time">Just now</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageGroup);
    scrollToBottom();
}

function displayBotMessage(message, questionData = null) {
    const messagesContainer = document.getElementById('chatMessages');
    
    const messageGroup = document.createElement('div');
    messageGroup.className = 'message-group bot';
    
    let optionsHTML = '';
    if (questionData && questionData.type === 'multiple_choice' && questionData.options) {
        optionsHTML = '<div class="quick-options">';
        questionData.options.forEach(option => {
            const escapedOption = option.replace(/'/g, "\\'");
            optionsHTML += `<button class="option-btn" onclick="selectOption('${escapedOption}')">${escapeHtml(option)}</button>`;
        });
        optionsHTML += '</div>';
    }
    
    messageGroup.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="message-bubble">
                ${message}
                ${optionsHTML}
            </div>
            <div class="message-time">Just now</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageGroup);
    scrollToBottom();
}

function displayLoadingMessage() {
    const messagesContainer = document.getElementById('chatMessages');
    
    const messageGroup = document.createElement('div');
    messageGroup.className = 'message-group bot loading-message-group';
    messageGroup.id = 'loadingMessage';
    
    messageGroup.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="loading-message">
                <div class="loading-spinner"></div>
                <span>Thinking...</span>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(messageGroup);
    scrollToBottom();
}

function removeLoadingMessage() {
    const loadingMessage = document.getElementById('loadingMessage');
    if (loadingMessage) loadingMessage.remove();
}

function selectOption(option) {
    document.getElementById('userInput').value = option;
    sendMessage();
}

function processAnswer(answer) {
    chatState.isProcessing = true;
    const sendButton = document.getElementById('sendButton');
    sendButton.disabled = true;
    
    showTypingIndicator();
    setTimeout(() => displayLoadingMessage(), 300);
    
    chatState.answers[chatState.currentQuestion] = answer;
    
    console.log(`Processing Q${chatState.currentQuestion}/${chatState.totalQuestions}: ${answer}`);
    
    fetch('/chatbot/process-answer', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            question_number: chatState.currentQuestion,
            answer: answer
        })
    })
    .then(response => response.json())
    .then(data => {
        removeLoadingMessage();
        hideTypingIndicator();
        
        console.log('Server response:', data);
        
        if (data.success) {
            // Check if we've completed ALL 11 questions
            if (chatState.currentQuestion >= chatState.totalQuestions) {
                console.log('All questions answered! Generating recommendations...');
                generateRecommendations();
            } else {
                // Move to next question
                chatState.currentQuestion++;
                updateProgress();
                
                console.log(`Moving to question ${chatState.currentQuestion}`);
                
                setTimeout(() => {
                    if (data.next_question && data.next_question.question) {
                        displayBotMessage(data.next_question.question, data.next_question);
                    } else {
                        // Fallback: fetch next question manually
                        loadQuestionByNumber(chatState.currentQuestion);
                    }
                }, 500);
            }
        } else {
            displayBotMessage(data.error || "Please try again.");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        removeLoadingMessage();
        hideTypingIndicator();
        displayBotMessage("Sorry, there was an error. Please try again.");
    })
    .finally(() => {
        chatState.isProcessing = false;
        sendButton.disabled = false;
    });
}

function loadQuestionByNumber(questionNumber) {
    fetch(`/chatbot/get-question/${questionNumber}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayBotMessage(data.question.question, data.question);
            } else {
                displayBotMessage("Error loading next question. Please try again.");
            }
        })
        .catch(error => {
            console.error('Error loading question:', error);
            displayBotMessage("Error loading next question. Please try again.");
        });
}

function generateRecommendations() {
    displayBotMessage("Perfect! Generating your personalized outfit with AI...");
    
    showTypingIndicator();
    displayLoadingMessage();
    
    console.log('Sending answers to generate recommendations:', chatState.answers);
    
    fetch('/chatbot/generate-recommendations', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ answers: chatState.answers })
    })
    .then(response => response.json())
    .then(data => {
        removeLoadingMessage();
        hideTypingIndicator();
        
        console.log('Recommendation response:', data);
        
        if (data.success) {
            chatState.currentRecommendation = {
                text: data.recommendations,
                images: data.images,
                sd_prompt: data.sd_prompt,
                id: data.recommendation_id
            };
            
            if (typeof IS_GUEST !== 'undefined' && IS_GUEST) {
                GuestStorage.saveRecommendation({
                    text: data.recommendations,
                    images: data.images,
                    timestamp: new Date().toISOString()
                });
            }
            
            displayRecommendations(data.recommendations, data.images, data.sd_prompt, data.recommendation_id);
        } else {
            displayBotMessage("Sorry, couldn't generate recommendations. Please try again.");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        removeLoadingMessage();
        hideTypingIndicator();
        displayBotMessage("Sorry, there was an error.");
    });
}

function displayRecommendations(recommendations, images, sdPrompt, recId) {
    const messagesContainer = document.getElementById('chatMessages');
    
    const messageGroup = document.createElement('div');
    messageGroup.className = 'message-group bot';
    
    let imagesHTML = '';
    if (images && images.length > 0) {
        imagesHTML = '<div class="image-gallery">';
        images.forEach(imagePath => {
            imagesHTML += `<img src="${imagePath}" class="gallery-image" alt="Outfit" onclick="openImageModal('${imagePath}')">`;
        });
        imagesHTML += '</div>';
    }
    
    const isGuest = typeof IS_GUEST !== 'undefined' && IS_GUEST;
    
    messageGroup.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="message-bubble">
                <p><strong>✨ Your Personalized Outfit:</strong></p>
                <div class="outfit-description">${escapeHtml(recommendations)}</div>
                ${imagesHTML}
                <div class="action-buttons" style="margin-top: 1rem;">
                    ${isGuest ? '' : '<button class="btn btn-primary btn-sm" onclick="saveRecommendation()"><i class="fas fa-bookmark"></i> Save</button>'}
                </div>
            </div>
            <div class="message-time">Just now</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageGroup);
    scrollToBottom();
}

function saveRecommendation() {
    const isGuest = typeof IS_GUEST !== 'undefined' && IS_GUEST;
    
    if (isGuest) {
        if (typeof showGuestLimitModal === 'function') {
            showGuestLimitModal();
        }
        return;
    }
    
    if (!chatState.currentRecommendation || !chatState.currentRecommendation.id) {
        alert('No recommendation to save');
        return;
    }
    
    fetch('/recommendations/api/save-recommendation', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            recommendation_id: chatState.currentRecommendation.id
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('✅ Saved successfully!');
        } else {
            alert('Failed to save');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to save');
    });
}

function modifyOutfit() {
    if (!chatState.currentRecommendation) {
        displayBotMessage('Please generate an outfit first.');
        return;
    }
    
    displayBotMessage('What would you like to change? (e.g., "make it blue", "different shoes", "more casual")');
    chatState.modificationMode = true;
}

function askFollowup() {
    if (!chatState.currentRecommendation) {
        displayBotMessage('Please generate an outfit first.');
        return;
    }
    
    displayBotMessage('What would you like to know about this outfit?');
    chatState.followupMode = true;
}

function startNewChat() {
    if (confirm('Start a new chat? Current progress will be lost.')) {
        fetch('/chatbot/restart-chat', {method: 'POST'})
            .then(() => location.reload())
            .catch(() => location.reload());
    }
}

function updateProgress() {
    const progressText = document.getElementById('questionProgress');
    if (progressText) {
        progressText.textContent = `Question ${chatState.currentQuestion} of ${chatState.totalQuestions}`;
    }
}

function showTypingIndicator() {
    const typingIndicator = document.querySelector('.typing-indicator');
    const statusText = document.querySelector('.status-text');
    if (typingIndicator && statusText) {
        typingIndicator.style.display = 'inline-flex';
        statusText.style.display = 'none';
    }
}

function hideTypingIndicator() {
    const typingIndicator = document.querySelector('.typing-indicator');
    const statusText = document.querySelector('.status-text');
    if (typingIndicator && statusText) {
        typingIndicator.style.display = 'none';
        statusText.style.display = 'inline';
    }
}

function scrollToBottom() {
    const messagesContainer = document.getElementById('chatMessages');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function openImageModal(imagePath) {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.9); display: flex;
        align-items: center; justify-content: center;
        z-index: 10000; cursor: pointer;
    `;
    
    modal.innerHTML = `<img src="${imagePath}" style="max-width: 90%; max-height: 90%; border-radius: 12px;">`;
    modal.onclick = () => modal.remove();
    
    document.body.appendChild(modal);
}

// Make displayRecommendations available globally
window.displayRecommendations = displayRecommendations;