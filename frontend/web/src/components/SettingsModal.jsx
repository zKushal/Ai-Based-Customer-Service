import React, { useState } from 'react';
import { X, Sun, Moon, Monitor, Trash2, Download, Info } from 'lucide-react';

const SettingsModal = ({ isOpen, onClose, onDeleteAllChats, theme, onThemeChange, chatHistory }) => {
  const [activeTab, setActiveTab] = useState('general');
  const [confirmDeleteAll, setConfirmDeleteAll] = useState(false);
  const [exportStatus, setExportStatus] = useState('');

  if (!isOpen) return null;

  const handleDeleteAll = () => {
    if (confirmDeleteAll) {
      onDeleteAllChats();
      setConfirmDeleteAll(false);
      onClose();
    } else {
      setConfirmDeleteAll(true);
    }
  };

  const handleExportData = async () => {
    setExportStatus('Exporting...');
    try {
      // Fetch all conversations
      const res = await fetch('http://localhost:8000/conversations/');
      if (!res.ok) throw new Error('Failed to fetch conversations');
      const data = await res.json();

      // Fetch messages for each conversation
      const fullExport = [];
      for (const conv of data.conversations) {
        const msgRes = await fetch(`http://localhost:8000/conversations/${conv.id}/messages`);
        let messages = [];
        if (msgRes.ok) {
          const msgData = await msgRes.json();
          messages = msgData.messages;
        }
        fullExport.push({
          conversation_id: conv.id,
          summary: conv.summary,
          status: conv.status,
          priority: conv.priority,
          created_at: conv.created_at,
          messages: messages.map(m => ({
            sender_type: m.sender_type,
            content: m.content,
            created_at: m.created_at,
          })),
        });
      }

      // Download as JSON
      const blob = new Blob([JSON.stringify(fullExport, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `chat-export-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setExportStatus('Exported successfully!');
      setTimeout(() => setExportStatus(''), 3000);
    } catch (e) {
      console.error('Export failed:', e);
      setExportStatus('Export failed.');
      setTimeout(() => setExportStatus(''), 3000);
    }
  };

  const tabs = [
    { id: 'general', label: 'General' },
    { id: 'appearance', label: 'Appearance' },
    { id: 'data', label: 'Data controls' },
    { id: 'shortcuts', label: 'Shortcuts' },
    { id: 'about', label: 'About' },
  ];

  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={(e) => e.stopPropagation()}>
        <div className="settings-header">
          <h2>Settings</h2>
          <button className="icon-button" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="settings-body">
          <div className="settings-tabs">
            {tabs.map(tab => (
              <button
                key={tab.id}
                className={`settings-tab ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => { setActiveTab(tab.id); setConfirmDeleteAll(false); }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="settings-content">
            {activeTab === 'general' && (
              <div className="settings-section">
                <h3>General</h3>

                <div className="setting-row">
                  <div className="setting-info">
                    <span className="setting-label">Chat history count</span>
                    <span className="setting-desc">Total conversations stored</span>
                  </div>
                  <span className="setting-value">{chatHistory?.length || 0} chats</span>
                </div>

                <div className="setting-row">
                  <div className="setting-info">
                    <span className="setting-label">Clear search history</span>
                    <span className="setting-desc">Reset the search filter in sidebar</span>
                  </div>
                  <button className="setting-action-btn" onClick={() => {
                    onClose();
                  }}>Done</button>
                </div>
              </div>
            )}

            {activeTab === 'appearance' && (
              <div className="settings-section">
                <h3>Appearance</h3>

                <div className="setting-row" style={{ borderBottom: 'none' }}>
                  <div className="setting-info">
                    <span className="setting-label">Theme</span>
                    <span className="setting-desc">Select your preferred theme</span>
                  </div>
                </div>

                <div className="theme-options">
                  <button
                    className={`theme-card ${theme === 'system' ? 'active' : ''}`}
                    onClick={() => onThemeChange('system')}
                  >
                    <Monitor size={24} />
                    <span>System</span>
                  </button>
                  <button
                    className={`theme-card ${theme === 'dark' ? 'active' : ''}`}
                    onClick={() => onThemeChange('dark')}
                  >
                    <Moon size={24} />
                    <span>Dark</span>
                  </button>
                  <button
                    className={`theme-card ${theme === 'light' ? 'active' : ''}`}
                    onClick={() => onThemeChange('light')}
                  >
                    <Sun size={24} />
                    <span>Light</span>
                  </button>
                </div>

                <div style={{ marginTop: '16px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  Current theme: <strong style={{ color: 'var(--text-primary)' }}>{theme.charAt(0).toUpperCase() + theme.slice(1)}</strong>
                </div>
              </div>
            )}

            {activeTab === 'data' && (
              <div className="settings-section">
                <h3>Data controls</h3>

                <div className="setting-row">
                  <div className="setting-info">
                    <span className="setting-label">Export data</span>
                    <span className="setting-desc">Download all your conversations as a JSON file</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {exportStatus && <span style={{ fontSize: '0.78rem', color: exportStatus.includes('success') ? '#10a37f' : '#ff5b5b' }}>{exportStatus}</span>}
                    <button className="setting-action-btn" onClick={handleExportData}>
                      <Download size={14} />
                      Export
                    </button>
                  </div>
                </div>

                <div className="setting-row danger-zone">
                  <div className="setting-info">
                    <span className="setting-label">Delete all chats</span>
                    <span className="setting-desc">Permanently delete all your conversations and messages</span>
                  </div>
                  <button
                    className={`setting-action-btn danger ${confirmDeleteAll ? 'confirm' : ''}`}
                    onClick={handleDeleteAll}
                  >
                    <Trash2 size={14} />
                    {confirmDeleteAll ? 'Confirm Delete' : 'Delete All'}
                  </button>
                </div>

                {confirmDeleteAll && (
                  <div className="confirm-warning">
                    <span>⚠️ This action cannot be undone. All your chat history will be permanently deleted.</span>
                    <button className="cancel-btn" onClick={() => setConfirmDeleteAll(false)}>Cancel</button>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'shortcuts' && (
              <div className="settings-section">
                <h3>Keyboard shortcuts</h3>

                <div className="shortcut-list">
                  <div className="shortcut-row">
                    <span>New chat</span>
                    <div className="shortcut-keys"><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>O</kbd></div>
                  </div>
                  <div className="shortcut-row">
                    <span>Toggle sidebar</span>
                    <div className="shortcut-keys"><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>S</kbd></div>
                  </div>
                  <div className="shortcut-row">
                    <span>Open settings</span>
                    <div className="shortcut-keys"><kbd>Ctrl</kbd> + <kbd>,</kbd></div>
                  </div>
                  <div className="shortcut-row">
                    <span>Send message</span>
                    <div className="shortcut-keys"><kbd>Enter</kbd></div>
                  </div>
                  <div className="shortcut-row">
                    <span>New line in message</span>
                    <div className="shortcut-keys"><kbd>Shift</kbd> + <kbd>Enter</kbd></div>
                  </div>
                  <div className="shortcut-row">
                    <span>Close dialog</span>
                    <div className="shortcut-keys"><kbd>Esc</kbd></div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'about' && (
              <div className="settings-section">
                <h3>About</h3>

                <div className="about-info">
                  <div className="about-row">
                    <span className="about-label">Application</span>
                    <span>AI Customer Service</span>
                  </div>
                  <div className="about-row">
                    <span className="about-label">Version</span>
                    <span>1.0.0</span>
                  </div>
                  <div className="about-row">
                    <span className="about-label">Backend</span>
                    <span>FastAPI + Groq LLM</span>
                  </div>
                  <div className="about-row">
                    <span className="about-label">Database</span>
                    <span>PostgreSQL</span>
                  </div>
                  <div className="about-row">
                    <span className="about-label">RAG Engine</span>
                    <span>FAISS + LangChain</span>
                  </div>
                  <div className="about-row">
                    <span className="about-label">Frontend</span>
                    <span>React + Vite</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
