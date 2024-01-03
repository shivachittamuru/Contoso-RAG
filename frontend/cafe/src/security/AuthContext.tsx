// AuthContext.tsx

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { validateToken, AuthToken, login, refreshToken } from './securityUtils'; // Ensure refreshToken is defined and exported

interface AuthContextType {
  isAuthenticated: boolean;
  userToken: AuthToken | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>(null!); // Non-null assertion

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [userToken, setUserToken] = useState<AuthToken | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  console.log('entered AuthContext.tsx');

  const checkAuth = async () => {
    console.log('AuthContext.tsx - checkAuth()');
    const tokenString = localStorage.getItem('jwtToken');
    if (tokenString) {
      const token: AuthToken = JSON.parse(tokenString);
      if (validateToken()) {
        console.log('AuthContext.tsx - checkAuth() - token is valid');
        setIsAuthenticated(true);
        setUserToken(token);
      } else {
        try {
          console.log('AuthContext.tsx - checkAuth() - token is invalid');
          // const newToken = await refreshToken(token.id);
          // localStorage.setItem('jwtToken', JSON.stringify(newToken));
          setIsAuthenticated(true);
          // setUserToken(newToken);
        } catch (error) {
          localStorage.removeItem('jwtToken');
          setIsAuthenticated(false);
          setUserToken(null);
        }
      } 
    } else {
      console.log('AuthContext.tsx - checkAuth() - token is null');
    }
  };

  useEffect(() => {
    console.log('AuthContext.tsx - useEffect()');
    checkAuth();
  }, []);

  const handleLogin = async (username: string, password: string) => {
    console.log('AuthContext.tsx - handleLogin()');
    const token = await login(username, password);
    console.log('AuthContext.tsx - handleLogin() - token: ', token);
    localStorage.setItem('jwtToken', JSON.stringify(token));
    setIsAuthenticated(true);
    setUserToken(token);
  };

  const handleLogout = () => {
    localStorage.removeItem('jwtToken');
    setIsAuthenticated(false);
    setUserToken(null);
  };

  // Value provided to context consumers
  const value = {
    isAuthenticated,
    userToken,
    login: handleLogin,
    logout: handleLogout,
    checkAuth,
  };

  console.log('AuthContext.tsx - value: ', value);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
