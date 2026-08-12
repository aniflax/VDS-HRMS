import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/axios';
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        try {
          const res = await api.get('/api/auth/me');
          setUser(res.data);
        } catch (error) {
          console.error("Failed to verify token on load", error);
          setToken(null);
          localStorage.removeItem('token');
          setUser(null);
        }
      }
      setLoading(false);
    };

    initAuth();

    // Listen to global logout events from axios interceptor
    const handleLogout = () => {
      setToken(null);
      setUser(null);
      navigate('/login');
    };

    window.addEventListener('auth:logout', handleLogout);
    return () => {
      window.removeEventListener('auth:logout', handleLogout);
    };
  }, [token, navigate]);

  const login = async (identifier, password) => {
    try {
      const res = await api.post('/api/auth/login', { identifier, password });
      const { access_token } = res.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      
      // We can either rely on token details or fetch /me immediately.
      // Often fetching /me again gets the full pristine object:
      const userRes = await api.get('/api/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` }
      });
      setUser(userRes.data);
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed. Please check your credentials.' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    navigate('/login');
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    setToken,
    setUser,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{!loading && children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
