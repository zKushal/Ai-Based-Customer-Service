import { useState, useRef, useEffect } from 'react';
import { Send, Bot, PanelLeft, Plus, Mic } from 'lucide-react';
import ChatMessage from './components/ChatMessage';
import Sidebar from './components/Sidebar';
import SettingsModal from './components/SettingsModal';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [chatHistory, setChatHistory] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');

  const chatContainerRef = useRef(null);

  // Apply theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  // Fetch history from backend
  const fetchHistory = async () => {
    try {
      const res = await fetch('http://localhost:8000/conversations/');
      if (res.ok) {
        const data = await res.json();
        const formattedHistory = data.conversations.map(c => ({
          id: c.id,
          title: c.summary || c.last_message_preview || `Conversation ${c.id}`
        }));
        setChatHistory(formattedHistory);
      }
    } catch (e) {
      console.error("Failed to fetch history from backend", e);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  // Auto-scroll
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  // Global keyboard shortcuts
  useEffect(() => {
    const handleGlobalKeyDown = (e) => {
      // Ctrl+Shift+O = New chat
      if (e.ctrlKey && e.shiftKey && e.key === 'O') {
        e.preventDefault();
        handleNewChat();
      }
      // Ctrl+Shift+S = Toggle sidebar
      if (e.ctrlKey && e.shiftKey && e.key === 'S') {
        e.preventDefault();
        setIsSidebarOpen(prev => !prev);
      }
      // Ctrl+, = Open settings
      if (e.ctrlKey && e.key === ',') {
        e.preventDefault();
        setIsSettingsOpen(prev => !prev);
      }
      // Esc = Close settings
      if (e.key === 'Escape' && isSettingsOpen) {
        setIsSettingsOpen(false);
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, [isSettingsOpen]);

  const handleNewChat = () => {
    setMessages([]);
    setCurrentChatId(null);
    setInput('');
  };

  const handleSelectChat = async (id) => {
    setCurrentChatId(id);
    setIsLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/conversations/${id}/messages`);
      if (res.ok) {
        const data = await res.json();
        const formattedMessages = data.messages.map(m => ({
          role: m.sender_type === 'customer' || m.sender_type === 'user' ? 'user' : 'ai',
          content: m.content
        }));
        setMessages(formattedMessages);
      }
    } catch (e) {
      console.error("Failed to fetch messages", e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteChat = async (id) => {
    try {
      const res = await fetch(`http://localhost:8000/conversations/${id}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        if (currentChatId === id) {
          handleNewChat();
        }
        fetchHistory();
      } else {
        console.error("Failed to delete chat");
      }
    } catch (e) {
      console.error("Error deleting chat", e);
    }
  };

  const handleDeleteAllChats = async () => {
    try {
      const res = await fetch('http://localhost:8000/conversations/all', {
        method: 'DELETE',
      });
      if (res.ok) {
        handleNewChat();
        setChatHistory([]);
        fetchHistory();
      } else {
        console.error("Failed to delete all chats");
      }
    } catch (e) {
      console.error("Error deleting all chats", e);
    }
  };

  const handleSend = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userText = input.trim();
    setInput('');

    const newMessages = [...messages, { role: 'user', content: userText }];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userText,
          conversation_id: currentChatId
        }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();

      const updatedMessages = [...newMessages, {
        role: 'ai',
        content: data.reply || data.response || data.message || "I'm sorry, I couldn't process that response."
      }];

      setMessages(updatedMessages);

      if (data.conversation_id && !currentChatId) {
        setCurrentChatId(data.conversation_id);
      }

      fetchHistory();

    } catch (error) {
      console.error('Error sending message:', error);
      setMessages([...newMessages, {
        role: 'ai',
        content: "Sorry, I encountered an error communicating with the server."
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="app-container">
      <Sidebar
        isCollapsed={!isSidebarOpen}
        toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        onNewChat={handleNewChat}
        chatHistory={chatHistory}
        onSelectChat={handleSelectChat}
        currentChatId={currentChatId}
        onDeleteChat={handleDeleteChat}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      <main className="main-content">
        {!isSidebarOpen && (
          <button
            className="icon-button header-toggle"
            onClick={() => setIsSidebarOpen(true)}
            title="Open sidebar"
          >
            <PanelLeft size={20} />
          </button>
        )}

        <div className="chat-container" ref={chatContainerRef}>
          {messages.length === 0 ? (
            <div className="empty-chat-state">
              What's on the agenda today?
            </div>
          ) : (
            messages.map((msg, idx) => (
              <ChatMessage key={idx} role={msg.role} content={msg.content} />
            ))
          )}

          {isLoading && (
            <div className="message-row ai">
              <div className="avatar">
                <img src="/favicon.svg" alt="AI" style={{ width: 20, height: 20, filter: 'invert(1)' }} />
              </div>
              <div className="typing-indicator">
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
              </div>
            </div>
          )}
        </div>

        <div className="input-area-wrapper">
          <form className="input-container" onSubmit={handleSend}>
            <button type="button" className="icon-button" style={{ color: '#ececec', padding: 4 }}>
              <Plus size={20} />
            </button>
            <textarea
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything"
              rows={1}
              disabled={isLoading}
            />
            <div className="input-actions">
              {input.trim() ? (
                <button
                  type="submit"
                  className="send-button"
                  disabled={isLoading}
                >
                  <Send size={16} />
                </button>
              ) : (
                <button type="button" className="icon-button" style={{ color: '#ececec', padding: 4 }}>
                  <Mic size={20} />
                </button>
              )}
            </div>
          </form>
          <div style={{ textAlign: 'center', fontSize: '0.75rem', color: '#b4b4b4', marginTop: '8px' }}>
            AI can make mistakes. Consider verifying important information.
          </div>
        </div>
      </main>

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onDeleteAllChats={handleDeleteAllChats}
        theme={theme}
        onThemeChange={setTheme}
        chatHistory={chatHistory}
      />
    </div>
  );
}

export default App;
