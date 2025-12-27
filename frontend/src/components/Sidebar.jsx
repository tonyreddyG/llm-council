import { useState, useEffect } from 'react';
import ProfileModal from './ProfileModal';
import SettingsModal from './SettingsModal';
import './Sidebar.css';

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  user,
  onLogout,
  onUserUpdate,
  onDeleteConversation,  // New prop
}) {
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const handleDeleteConversation = async (conversationId, e) => {
    e.stopPropagation(); // Prevent selecting the conversation
    if (!window.confirm("Delete this conversation? This action cannot be undone.")) {
      return;
    }
    onDeleteConversation(conversationId);
  };

  return (
    <>
      <div className="sidebar">
        <div className="sidebar-header">
          <h1>LLM Council</h1>
          <button className="new-conversation-btn" onClick={onNewConversation}>
            + New Conversation
          </button>
        </div>

        <div className="conversation-list">
          {conversations.length === 0 ? (
            <div className="no-conversations">No conversations yet</div>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                className={`conversation-item ${conv.id === currentConversationId ? 'active' : ''
                  }`}
                onClick={() => onSelectConversation(conv.id)}
              >
                <div className="conversation-content">
                  <div className="conversation-title">
                    {conv.title || 'New Conversation'}
                  </div>
                  <div className="conversation-meta">
                    {conv.message_count} messages
                  </div>
                </div>
                <button
                  className="delete-conversation-btn"
                  onClick={(e) => handleDeleteConversation(conv.id, e)}
                  title="Delete conversation"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    <line x1="10" y1="11" x2="10" y2="17"></line>
                    <line x1="14" y1="11" x2="14" y2="17"></line>
                  </svg>
                </button>
              </div>
            ))
          )}
        </div>

        {user && (
          <div className="sidebar-footer">
            <div className="user-info">
              <div className="user-icon">👤</div>
              <div className="user-details">
                <span className="username">{user.username}</span>
              </div>
            </div>
            <div className="footer-actions">
              <button
                className="icon-btn profile-btn"
                onClick={() => setIsProfileOpen(true)}
                title="Profile"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
              </button>
              <button
                className="icon-btn settings-btn"
                onClick={() => setIsSettingsOpen(true)}
                title="Settings"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="3"></circle>
                  <path d="M12 1v6m0 6v6m5.3-13.7l-4.3 4.3m0 4.8l4.3 4.3M1 12h6m6 0h6m-13.7 5.3l4.3-4.3m4.8 0l4.3 4.3"></path>
                </svg>
              </button>
              <button className="logout-btn" onClick={onLogout} title="Logout">
                Logout
              </button>
            </div>
          </div>
        )}
      </div>

      {isProfileOpen && user && (
        <ProfileModal
          user={user}
          onClose={() => setIsProfileOpen(false)}
          onLogout={onLogout}
          onUsernameUpdated={onUserUpdate}
        />
      )}

      {isSettingsOpen && (
        <SettingsModal
          onClose={() => setIsSettingsOpen(false)}
        />
      )}
    </>
  );
}
