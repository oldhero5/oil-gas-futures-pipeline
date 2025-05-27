// frontend/src/contexts/AuthContext.tsx
'use client';

import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { useRouter } from 'next/navigation';

const ADMIN_EMAIL = 'admin@example.com'; // Define admin email

interface User {
  id: string;
  email: string;
  isAdmin: boolean; // Added isAdmin flag
}

interface AuthContextType {
  user: User | null;
  login: (email: string, pass: string) => Promise<void>;
  logout: () => void;
  register: (email: string, pass: string) => Promise<void>;
  isLoading: boolean;
  isAdmin: boolean; // Expose isAdmin directly for convenience
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const storedUserString = localStorage.getItem('currentUser');
    if (storedUserString) {
      try {
        const storedUser = JSON.parse(storedUserString);
        // Ensure isAdmin flag is correctly set from localStorage or re-evaluated
        if (storedUser && typeof storedUser.email === 'string') {
            storedUser.isAdmin = storedUser.email === ADMIN_EMAIL;
            setUser(storedUser);
        } else {
            localStorage.removeItem('currentUser'); // Clear invalid stored user
        }
      } catch (error) {
        console.error("Failed to parse stored user:", error);
        localStorage.removeItem('currentUser'); // Clear corrupted data
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, pass: string) => {
    setIsLoading(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    console.log('AuthContext: Logging in with', { email, pass });
    if (email && pass) {
      const isAdminUser = email === ADMIN_EMAIL;
      const mockUser: User = {
        id: isAdminUser ? 'admin-001' : 'user-' + Date.now(), // Simple unique ID
        email: email,
        isAdmin: isAdminUser
      };
      setUser(mockUser);
      localStorage.setItem('currentUser', JSON.stringify(mockUser));
      router.push('/');
    } else {
      throw new Error('Invalid credentials (simulated)');
    }
    setIsLoading(false);
  };

  const logout = () => {
    console.log('AuthContext: Logging out');
    setUser(null);
    localStorage.removeItem('currentUser');
    router.push('/login');
  };

  const register = async (email: string, pass: string) => {
    setIsLoading(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    console.log('AuthContext: Registering with', { email, pass });
    if (!email || !pass) {
        throw new Error('Email and password are required (simulated)');
    }
    if (email === ADMIN_EMAIL) {
        throw new Error('This email is reserved for admin account.');
    }
    // Simulate successful registration
    setIsLoading(false);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, register, isLoading, isAdmin: !!user?.isAdmin }}>
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
