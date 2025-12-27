/**
 * API client for the LLM Council backend.
 */

const API_BASE =
  window.location.hostname === "localhost"
    ? "https://localhost:8001"
    : `https://${window.location.hostname}:8001`;



export const api = {
  /**
   * Helper to handle response and check for auth errors
   */
  async _handleResponse(response) {
    if (response.status === 401) {
      throw new Error('Unauthorized');
    }
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || 'API request failed');
    }
    return response.json();
  },

  /**
   * Helper to fetch with a single retry on network errors (e.g. WinError 10054 connection reset)
   */
  async _fetchWithRetry(url, options) {
    try {
      return await fetch(url, options);
    } catch (e) {
      // Only retry on network-level errors (failed to fetch, connection reset)
      // fetch() itself does NOT throw on HTTP errors like 401, 500, etc.
      if (e.message.includes('fetch') || e.name === 'TypeError' || e.message.includes('NetworkError')) {
        console.warn(`Transient network error at ${url}, retrying once: ${e.message}`);
        await new Promise(r => setTimeout(r, 300));
        try {
          return await fetch(url, options);
        } catch (retryError) {
          console.error(`Retry also failed for ${url}:`, retryError);
          throw retryError;
        }
      }
      throw e;
    }
  },

  async login(username, password) {
    // Note: Cookies are set automatically by the backend via Set-Cookie header
    const response = await this._fetchWithRetry(`${API_BASE}/api/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, password }),
    });

    // We don't save the token in JS, it's HttpOnly cookie
    if (!response.ok) {
      throw new Error('Login failed: Invalid credentials');
    }
    return response.json();
  },

  async register(username, email, password) {
    const response = await this._fetchWithRetry(`${API_BASE}/api/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, email, password }),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || 'Registration failed');
    }
    return response.json();
  },

  async logout() {
    await this._fetchWithRetry(`${API_BASE}/api/logout`, { method: 'POST', credentials: 'include' });
  },

  async checkAuth() {
    // Try to get current user to verify session
    try {
      const response = await this._fetchWithRetry(`${API_BASE}/api/me`, { credentials: 'include' });
      if (response.ok) {
        return await response.json();
      }
    } catch (e) {
      // Ignore network errors during check
    }
    return null;
  },

  async refreshToken() {
    try {
      await this._fetchWithRetry(`${API_BASE}/api/refresh`, { method: 'POST', credentials: 'include' });
    } catch (e) {
      console.error("Failed to refresh token", e);
    }
  },

  /**
   * List all conversations.
   */
  async listConversations() {
    const response = await this._fetchWithRetry(`${API_BASE}/api/conversations`, { credentials: 'include' });
    return this._handleResponse(response);
  },

  /**
   * Create a new conversation.
   */
  async createConversation() {
    const response = await this._fetchWithRetry(`${API_BASE}/api/conversations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({}),
    });
    return this._handleResponse(response);
  },

  /**
   * Get a specific conversation.
   */
  async getConversation(conversationId) {
    const response = await this._fetchWithRetry(
      `${API_BASE}/api/conversations/${conversationId}`,
      { credentials: 'include' }
    );
    return this._handleResponse(response);
  },

  /**
   * Send a message in a conversation.
   */
  async sendMessage(conversationId, content) {
    const response = await this._fetchWithRetry(
      `${API_BASE}/api/conversations/${conversationId}/message`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ content }),
      }
    );
    return this._handleResponse(response);
  },

  /**
   * Send a message and receive streaming updates.
   */
  async sendMessageStream(conversationId, content, onEvent) {
    const response = await this._fetchWithRetry(
      `${API_BASE}/api/conversations/${conversationId}/message/stream`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ content }),
      }
    );

    if (response.status === 401) {
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          try {
            const event = JSON.parse(data);
            onEvent(event.type, event);
          } catch (e) {
            console.error('Failed to parse SSE event:', e);
          }
        }
      }
    }
  },
  async changePassword(oldPassword, newPassword) {
    const response = await this._fetchWithRetry(`${API_BASE}/api/change-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || 'Failed to change password');
    }
    return response.json();
  },

  async changeUsername(newUsername) {
    const response = await this._fetchWithRetry(`${API_BASE}/api/change-username`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ new_username: newUsername }),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || 'Failed to change username');
    }
    return response.json();
  },

  async deleteAccount() {
    const response = await this._fetchWithRetry(`${API_BASE}/api/me`, {
      method: 'DELETE',
      credentials: 'include',
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || 'Failed to delete account');
    }
    return response.json();
  },

  async getAvailableModels() {
    const response = await this._fetchWithRetry(`${API_BASE}/api/models`, {
      credentials: 'include',
    });
    return this._handleResponse(response);
  },

  async getUserPreferences() {
    const response = await this._fetchWithRetry(`${API_BASE}/api/user/preferences`, {
      credentials: 'include',
    });
    return this._handleResponse(response);
  },

  async updateUserPreferences(preferences) {
    const response = await this._fetchWithRetry(`${API_BASE}/api/user/preferences`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(preferences),
    });
    return this._handleResponse(response);
  },

  async deleteConversation(conversationId) {
    const response = await this._fetchWithRetry(`${API_BASE}/api/conversations/${conversationId}`, {
      method: 'DELETE',
      credentials: 'include',
    });
    return this._handleResponse(response);
  }
};
