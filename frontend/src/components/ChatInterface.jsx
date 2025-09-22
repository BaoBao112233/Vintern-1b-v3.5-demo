import React, { useState, useRef, useEffect } from 'react';
import './ChatInterface.css';
import { apiService } from '../services/api';

const ChatInterface = ({ currentImageData, detectedObjects, onChatResponse }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [includeObjects, setIncludeObjects] = useState(true);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');

    // Add user message to chat
    const newUserMessage = {
      id: Date.now(),
      type: 'user',
      content: userMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newUserMessage]);
    setIsLoading(true);

    try {
      // Send to backend
      const response = await apiService.chatWithVision({
        message: userMessage,
        image_data: currentImageData,
        include_objects: includeObjects,
        confidence_threshold: 0.5
      });

      // Add assistant response to chat
      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.response,
        timestamp: new Date(),
        detectedObjects: response.detected_objects,
        objectsSummary: response.objects_summary,
        imageWithBoxes: response.image_with_boxes
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Callback to parent component
      if (onChatResponse) {
        onChatResponse(response);
      }

    } catch (error) {
      console.error('Chat error:', error);
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: 'Xin lỗi, có lỗi xảy ra khi xử lý tin nhắn của bạn.',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h3>💬 Chat với AI</h3>
        <div className="chat-controls">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={includeObjects}
              onChange={(e) => setIncludeObjects(e.target.checked)}
            />
            Bao gồm thông tin vật thể
          </label>
          <button 
            className="clear-chat-btn"
            onClick={clearChat}
            title="Xóa lịch sử chat"
          >
            🗑️
          </button>
        </div>
      </div>

      <div className="messages-container">
        {messages.length === 0 && (
          <div className="empty-chat">
            <p>👋 Xin chào! Tôi có thể giúp bạn phân tích những gì tôi thấy trên camera.</p>
            <p>Hãy hỏi tôi về các vật thể trong khung hình!</p>
          </div>
        )}

        {messages.map(message => (
          <div key={message.id} className={`message ${message.type}`}>
            <div className="message-content">
              {message.type === 'user' && (
                <div className="user-message">
                  <strong>Bạn:</strong> {message.content}
                </div>
              )}

              {message.type === 'assistant' && (
                <div className="assistant-message">
                  <strong>🤖 AI:</strong>
                  <p>{message.content}</p>
                  
                  {message.objectsSummary && (
                    <div className="objects-summary">
                      <strong>🎯 Phát hiện:</strong>
                      <p>{message.objectsSummary}</p>
                    </div>
                  )}

                  {message.imageWithBoxes && (
                    <div className="image-with-boxes">
                      <strong>📷 Ảnh với khung vật thể:</strong>
                      <img 
                        src={`data:image/jpeg;base64,${message.imageWithBoxes}`}
                        alt="Detected objects"
                        className="detection-result"
                      />
                    </div>
                  )}
                </div>
              )}

              {message.type === 'error' && (
                <div className="error-message">
                  <strong>❌ Lỗi:</strong> {message.content}
                </div>
              )}
            </div>
            
            <div className="message-time">
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message assistant loading">
            <div className="message-content">
              <strong>🤖 AI:</strong> <span className="typing-indicator">Đang suy nghĩ...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <div className="chat-input-wrapper">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Hỏi tôi về những gì bạn thấy trên camera..."
            className="chat-input"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            className={`send-button ${isLoading ? 'loading' : ''}`}
            disabled={!inputMessage.trim() || isLoading}
          >
            {isLoading ? '⏳' : '📤'}
          </button>
        </div>
        
        <div className="input-info">
          {detectedObjects && detectedObjects.length > 0 && (
            <div className="current-objects">
              Vật thể hiện tại: {detectedObjects.map(obj => obj.name).join(', ')}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;