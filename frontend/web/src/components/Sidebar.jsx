import React, { useState, useEffect, useRef } from 'react';
import { PenSquare, PanelLeftClose, Search, MoreHorizontal, Trash2, ChevronDown, ChevronRight, Settings } from 'lucide-react';

const Sidebar = ({ isCollapsed, toggleSidebar, onNewChat, chatHistory, onSelectChat, currentChatId, onDeleteChat, onOpenSettings }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [menuOpenId, setMenuOpenId] = useState(null);
  const [isHistoryExpanded, setIsHistoryExpanded] = useState(true);

  const sidebarRef = useRef(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (sidebarRef.current && !sidebarRef.current.contains(e.target)) {
        setMenuOpenId(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filteredHistory = chatHistory.filter(chat =>
    chat.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleContextMenu = (e, id) => {
    e.preventDefault();
    setMenuOpenId(menuOpenId === id ? null : id);
  };

  const handleOptionClick = (e, id) => {
    e.stopPropagation();
    setMenuOpenId(menuOpenId === id ? null : id);
  };

  const handleDelete = (e, id) => {
    e.stopPropagation();
    if (window.confirm("Are you sure you want to delete this chat?")) {
      onDeleteChat(id);
    }
    setMenuOpenId(null);
  };

  return (
    <div className={`sidebar ${isCollapsed ? 'collapsed' : ''}`} ref={sidebarRef}>
      <div className="sidebar-header">
        <div className="sidebar-top-row">
          <button className="icon-button" onClick={toggleSidebar} title="Close sidebar">
            <PanelLeftClose size={20} />
          </button>
          <button className="icon-button" onClick={onNewChat} title="New chat">
            <PenSquare size={20} />
          </button>
        </div>

        <button className="new-chat-btn" onClick={onNewChat}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <img src="/favicon.svg" alt="Logo" style={{ width: 20, height: 20, filter: 'invert(1)' }} onError={(e) => e.target.style.display = 'none'} />
            Chat Here
          </div>
          <PenSquare size={16} style={{ marginLeft: 'auto', color: '#b4b4b4' }} />
        </button>

        <div className="search-container">
          <Search size={16} color="#b4b4b4" />
          <input
            type="text"
            className="search-input"
            placeholder="Search chats"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="sidebar-history">
        <div className="history-section">
          <div className="history-section-header" onClick={() => setIsHistoryExpanded(!isHistoryExpanded)}>
            <span style={{ fontWeight: '600', fontSize: '0.8rem', color: '#fff' }}>Chats</span>
            {isHistoryExpanded ? <ChevronDown size={14} color="#b4b4b4" /> : <ChevronRight size={14} color="#b4b4b4" />}
          </div>

          {isHistoryExpanded && (
            <div className="history-list">
              {filteredHistory.length > 0 ? (
                filteredHistory.map(chat => (
                  <div
                    key={chat.id}
                    className={`history-item-wrapper ${currentChatId === chat.id ? 'active' : ''}`}
                    onContextMenu={(e) => handleContextMenu(e, chat.id)}
                  >
                    <div
                      className="history-item"
                      onClick={() => onSelectChat(chat.id)}
                      title={chat.title}
                    >
                      {chat.title}
                    </div>
                    <button
                      className="history-options-btn"
                      onClick={(e) => handleOptionClick(e, chat.id)}
                    >
                      <MoreHorizontal size={16} />
                    </button>

                    {menuOpenId === chat.id && (
                      <div className="history-dropdown">
                        <button className="dropdown-item delete" onClick={(e) => handleDelete(e, chat.id)}>
                          <Trash2 size={14} />
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div style={{ padding: '10px 12px', fontSize: '0.85rem', color: '#b4b4b4' }}>
                  {searchQuery ? "No matching chats" : "No recent chats"}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="sidebar-footer">
        <div className="footer-item" onClick={onOpenSettings}>
          <Settings size={18} />
          <span>Settings</span>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
