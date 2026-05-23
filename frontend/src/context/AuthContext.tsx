import React, { createContext, useState, useEffect, useContext } from 'react';

export interface User {
  id: string;
  name: string;
  university: string;
  email: string;
  phone?: string;
  created_at: string;
  profile_score: number;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  updateProfileScore: (newScore: number) => void;
  refreshUser: () => Promise<void>;
  apiUrl: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [loading, setLoading] = useState<boolean>(true);

  // Fallback local API path, dynamically check environment vars for production vercel build
  const apiUrl = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000';

  useEffect(() => {
    const initializeAuth = async () => {
      if (token) {
        try {
          const res = await fetch(`${apiUrl}/api/auth/me`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          if (res.ok) {
            const data = await res.json();
            setUser(data);
          } else {
            // Token expired or invalid
            logout();
          }
        } catch (e) {
          console.error("Auth server connection failed:", e);
        }
      }
      setLoading(false);
    };

    initializeAuth();
  }, [token]);

  const login = (newToken: string, newUser: User) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
    setUser(newUser);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const updateProfileScore = (newScore: number) => {
    if (user) {
      setUser({ ...user, profile_score: newScore });
    }
  };

  const refreshUser = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${apiUrl}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      }
    } catch (e) {
      console.error("Failed to refresh user info:", e);
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, updateProfileScore, refreshUser, apiUrl }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
