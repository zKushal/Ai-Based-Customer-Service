import React from 'react';
import ReactMarkdown from 'react-markdown';

const ChatMessage = ({ role, content }) => {
  const isUser = role === 'user';
  
  return (
    <div className={`message-row ${isUser ? 'user' : 'ai'}`}>
      <div className="avatar">
        {!isUser && (
          <img src="/favicon.svg" alt="AI" style={{ width: 20, height: 20, filter: 'invert(1)' }} onError={(e) => e.target.style.display = 'none'} />
        )}
      </div>
      <div className="message-bubble markdown-body">
        {isUser ? (
          // User messages are typically plain text, just render them directly
          content
        ) : (
          // AI messages use Markdown formatting
          <ReactMarkdown>{content}</ReactMarkdown>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
