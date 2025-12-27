import { useState } from 'react';
import { api } from '../api';
import './ProfileModal.css';

export default function ProfileModal({ user, onClose, onLogout, onUsernameUpdated }) {
  const [activeTab, setActiveTab] = useState('password');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  // Password fields
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');

  // Username field
  const [newUsername, setNewUsername] = useState('');

  const clearForm = () => {
    setMessage(null);
    setError(null);
    setOldPassword('');
    setNewPassword('');
    setConfirmNewPassword('');
    setNewUsername('');
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    clearForm();
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setError(null);
    setMessage(null);

    if (newPassword !== confirmNewPassword) {
      setError("New passwords do not match");
      return;
    }

    if (oldPassword === newPassword) {
      setError("Old and New passwords are same. Please provide new different password.");
      return;
    }

    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setLoading(true);
    try {
      await api.changePassword(oldPassword, newPassword);
      setMessage("Password changed successfully! You will need to use the new password next time.");
      setOldPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleChangeUsername = async (e) => {
    e.preventDefault();
    setError(null);
    setMessage(null);

    if (newUsername.trim() === '') {
      setError("Username cannot be empty");
      return;
    }

    setLoading(true);
    try {
      const result = await api.changeUsername(newUsername);
      setMessage("Username updated successfully!");
      if (onUsernameUpdated) {
        onUsernameUpdated(result.username);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (!window.confirm("ARE YOU SURE? This will permanently delete your account and ALL conversations. This action cannot be undone.")) {
      return;
    }

    setLoading(true);
    try {
      await api.deleteAccount();
      onLogout();
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>User Profile</h2>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="form-group email-group">
          <label>Email</label>
          <input type="email" value={user.email} disabled className="disabled-input" />
        </div>

        <div className="modal-tabs">
          <button className={`tab-btn ${activeTab === 'password' ? 'active' : ''}`} onClick={() => handleTabChange('password')}>
            Change Password
          </button>
          <button className={`tab-btn ${activeTab === 'username' ? 'active' : ''}`} onClick={() => handleTabChange('username')}>
            Change Username
          </button>
          <button className={`tab-btn danger ${activeTab === 'delete' ? 'active' : ''}`} onClick={() => handleTabChange('delete')}>
            Delete Account
          </button>
        </div>

        <div className="modal-body">
          {message && <div className="success-message">{message}</div>}
          {error && <div className="error-message">{error}</div>}

          {activeTab === 'password' && (
            <form onSubmit={handleChangePassword}>
              <div className="form-group">
                <label>Old Password</label>
                <input type="password" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} required />
              </div>
              <div className="form-group">
                <label>New Password</label>
                <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required />
              </div>
              <div className="form-group">
                <label>Confirm New Password</label>
                <input type="password" value={confirmNewPassword} onChange={(e) => setConfirmNewPassword(e.target.value)} required />
              </div>
              <button type="submit" disabled={loading} className="action-btn">Update Password</button>
            </form>
          )}

          {activeTab === 'username' && (
            <form onSubmit={handleChangeUsername}>
              <div className="form-group">
                <label>Current Username</label>
                <input type="text" value={user.username} disabled className="disabled-input" />
              </div>
              <div className="form-group">
                <label>New Username</label>
                <input type="text" value={newUsername} onChange={(e) => setNewUsername(e.target.value)} required minLength={3} />
              </div>
              <button type="submit" disabled={loading} className="action-btn">Update Username</button>
            </form>
          )}

          {activeTab === 'delete' && (
            <div className="delete-section">
              <p className="warning-text">Warning: This action is irreversible. All your conversations and data will be permanently removed.</p>
              <button onClick={handleDeleteAccount} disabled={loading} className="delete-btn">Delete My Account</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
