import React, { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../security/AuthContext';
import './LoginPage.css'; 

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null); // New state for error message
  const { login } = useAuth();
  const navigate = useNavigate();

  console.log('entered LoginPage.tsx');

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      console.log('LoginPage.tsx - handleLogin()');
      await login(username, password);
      console.log('LoginPage.tsx - handleLogin() - login successful');
      navigate('/app');
    } catch (error) {
      // Set the error message state if login fails
      setErrorMessage('Login failed. Please check your username and password.');
    }
  };

  return (
    <div className="login-container">
      <div className="login-logo">
        <img src="/Azure-512p-maskable.png" alt="Logo" className="logo" /> 
        <h3>Cafe Login</h3>
      </div>
      <div className="login-form">
        <form onSubmit={handleLogin}>
          {errorMessage && <div className="login-error">{errorMessage}</div>} {/* Display error message */}
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
            />
          </div>
          <button type="submit" className="login-button">Login</button>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
