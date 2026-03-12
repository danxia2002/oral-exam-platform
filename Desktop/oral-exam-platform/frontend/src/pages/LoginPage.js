import { useState } from 'react';
import axios from 'axios';
import '../styles/LoginPage.css';

function LoginPage({ onLoginSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [userType, setUserType] = useState('student');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) {
      setMessage('Please enter your email and password');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/api/auth/login', {
        email,
        password
      });

      if (response.data.success) {
        setMessage('✅ successful login!');
        localStorage.setItem('token', response.data.token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        
        // Call parent component callback
        if (onLoginSuccess) {
          onLoginSuccess();
        }
      } else {
        setMessage('❌ ' + (response.data.error || 'failed login'));
      }
    } catch (error) {
      setMessage('❌ error: ' + (error.response?.data?.error || error.message));
    }
    setLoading(false);
  };

  const handleRegister = async () => {
    if (!email || !username || !password) {
      setMessage('Please fill in all fields');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/api/auth/register', {
        email,
        username,
        password,
        user_type: userType
      });

      if (response.data.message) {
        setMessage('✅ Registration successful! Please log in');
        setIsLogin(true);
        setPassword('');
      } else {
        setMessage('❌ ' + (response.data.error || 'Registration failed'));
      }
    } catch (error) {
      setMessage('❌ error: ' + (error.response?.data?.error || error.message));
    }
    setLoading(false);
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1>Oral Exam Platform</h1>

        {isLogin ? (
          <>
            <h2>login</h2>
            <input
              type="email"
              placeholder="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
            />
            <input
              type="password"
              placeholder="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />
            <button onClick={handleLogin} disabled={loading}>
              {loading ? 'loading' : 'login'}
            </button>
            <p className="toggle-text">
              no account?
              <a href="#" onClick={(e) => {
                e.preventDefault();
                setIsLogin(false);
                setMessage('');
              }}>
                register
              </a>
            </p>
          </>
        ) : (
          <>
            <h2>register</h2>
            <input
              type="email"
              placeholder="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
            />
            <input
              type="text"
              placeholder="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
            />
            <input
              type="password"
              placeholder="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />
            <select 
              value={userType} 
              onChange={(e) => setUserType(e.target.value)}
              disabled={loading}
              style={{
                width: '100%',
                padding: '12px',
                marginBottom: '15px',
                border: '1px solid #ddd',
                borderRadius: '5px',
                fontSize: '16px'
              }}
            >
              <option value="student">Register as Student</option>
              <option value="teacher">Register as Teacher</option>
            </select>

            <button onClick={handleRegister} disabled={loading}>
              {loading ? 'loading' : 'register'}
            </button>
            <p className="toggle-text">
              have account?
              <a href="#" onClick={(e) => {
                e.preventDefault();
                setIsLogin(true);
                setMessage('');
              }}>
                login
              </a>
            </p>
          </>
        )}

        {message && (
          <p className={`message ${message.includes('✅') ? 'success' : 'error'}`}>
            {message}
          </p>
        )}
      </div>
    </div>
  );
}

export default LoginPage;