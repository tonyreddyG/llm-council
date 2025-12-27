
import { useState } from 'react';
import { api } from '../api';

function Login({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isLogin) {
        await api.login(username, password);
        onLogin();
      } else {
        // Basic email validation
        if (!email.includes('@') || !email.includes('.')) {
          throw new Error('Please use a valid email address');
        }

        // Password policy validation
        if (password.length < 8 || password.length > 100) {
          throw new Error('Password must be between 8 and 100 characters');
        }
        if (!/[A-Z]/.test(password)) {
          throw new Error('Password must contain at least one uppercase letter');
        }
        if (!/[a-z]/.test(password)) {
          throw new Error('Password must contain at least one lowercase letter');
        }
        if (!/\d/.test(password)) {
          throw new Error('Password must contain at least one number');
        }
        if (!/^[A-Za-z\d!@#%()\-_+]*$/.test(password)) {
          throw new Error('Password contains restricted characters. Use only !@#%()-_+');
        }

        if (password !== confirmPassword) {
          throw new Error('Passwords do not match');
        }

        await api.register(username, email, password);
        // Auto login after register
        await api.login(username, password);
        onLogin();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h2>{isLogin ? 'Login to LLM Council' : 'Register New Account'}</h2>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username {isLogin && '(or Email)'}</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          {!isLogin && (
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="example@email.com"
              />
            </div>
          )}

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {!isLogin && (
              <small className="help-text">
                8-100 chars, 1 Upper, 1 Lower, 1 Number. <br />
                Specials: !@#%()-_+
              </small>
            )}
          </div>

          {!isLogin && (
            <div className="form-group">
              <label>Confirm Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>
          )}

          {error && <div className="error-message">{error}</div>}

          <button type="submit" disabled={loading} className="submit-btn">
            {loading ? 'Please wait...' : (isLogin ? 'Login' : 'Register')}
          </button>
        </form>

        <p className="toggle-auth">
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <button onClick={() => {
            setIsLogin(!isLogin);
            setError(null);
            setConfirmPassword('');
          }} className="link-btn">
            {isLogin ? 'Register' : 'Login'}
          </button>
        </p>
      </div>

      <style>{`
        .login-container {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100vh;
          background-color: #f5f7fa;
        }
        .login-box {
          background: white;
          padding: 2rem;
          border-radius: 8px;
          box-shadow: 0 4px 6px rgba(0,0,0,0.1);
          width: 100%;
          max-width: 400px;
        }
        h2 {
          text-align: center;
          margin-bottom: 2rem;
          color: #333;
        }
        .form-group {
          margin-bottom: 1.5rem;
        }
        label {
          display: block;
          margin-bottom: 0.5rem;
          color: #666;
        }
        input {
          width: 100%;
          padding: 0.75rem;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 1rem;
        }
        .submit-btn {
          width: 100%;
          padding: 0.75rem;
          background-color: #4a90e2;
          color: white;
          border: none;
          border-radius: 4px;
          font-size: 1rem;
          cursor: pointer;
        }
        .submit-btn:disabled {
          background-color: #a0c0e0;
        }
        .error-message {
          color: #e74c3c;
          margin-bottom: 1rem;
          text-align: center;
          font-size: 0.9rem;
        }
        .toggle-auth {
          margin-top: 1.5rem;
          text-align: center;
          font-size: 0.9rem;
          color: #666;
        }
        .link-btn {
          background: none;
          border: none;
          color: #4a90e2;
          cursor: pointer;
          text-decoration: underline;
          padding: 0;
          font: inherit;
        }
        .help-text {
          display: block;
          margin-top: 5px;
          font-size: 0.75rem;
          color: #888;
          line-height: 1.2;
        }
      `}</style>
    </div>
  );
}

export default Login;
