"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

export type UserRole = "CHIEF_RISK_OFFICER" | "PORTFOLIO_MANAGER" | "ANALYST" | "AUDITOR";

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  picture?: string;
  role: UserRole;
  organization: string;
  permissions: string[];
  auth_provider: string;
  created_at: string;
}

interface AuthResult {
  success: boolean;
  error?: string;
}

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  loginWithCredentials: (email: string, password: string) => Promise<AuthResult>;
  registerUser: (
    email: string,
    password: string,
    name: string,
    role: UserRole,
    organization: string
  ) => Promise<AuthResult>;
  loginWithGoogleCredential: (credential: string) => Promise<AuthResult>;
  loginWithPersona: (
    email: string,
    name: string,
    role: UserRole,
    organization: string
  ) => Promise<AuthResult>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  loginWithCredentials: async () => ({ success: false, error: "Not initialized" }),
  registerUser: async () => ({ success: false, error: "Not initialized" }),
  loginWithGoogleCredential: async () => ({ success: false, error: "Not initialized" }),
  loginWithPersona: async () => ({ success: false, error: "Not initialized" }),
  logout: () => {},
});

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5051";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Restore session from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem("risklattice_token");
    const savedUser = localStorage.getItem("risklattice_user");

    if (savedToken && savedUser) {
      try {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
        // Verify with backend
        fetch(`${API_BASE}/api/v1/auth/me`, {
          headers: { Authorization: `Bearer ${savedToken}` },
        })
          .then((res) => {
            if (res.ok) {
              return res.json();
            } else {
              logout();
            }
          })
          .then((data) => {
            if (data?.user) {
              setUser(data.user);
              localStorage.setItem("risklattice_user", JSON.stringify(data.user));
            }
          })
          .catch(() => {
            // Keep local cached user if network temporarily down
          })
          .finally(() => setIsLoading(false));
      } catch {
        logout();
        setIsLoading(false);
      }
    } else {
      setIsLoading(false);
    }
  }, []);

  const loginWithCredentials = async (email: string, password: string): Promise<AuthResult> => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();
      if (res.ok) {
        setToken(data.token);
        setUser(data.user);
        localStorage.setItem("risklattice_token", data.token);
        localStorage.setItem("risklattice_user", JSON.stringify(data.user));
        return { success: true };
      } else {
        return { success: false, error: data.detail || "Authentication failed." };
      }
    } catch (e: any) {
      console.error("Proprietary login failed", e);
      return { success: false, error: e.message || "Network error during login." };
    } finally {
      setIsLoading(false);
    }
  };

  const registerUser = async (
    email: string,
    password: string,
    name: string,
    role: UserRole,
    organization: string
  ): Promise<AuthResult> => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, name, role, organization }),
      });

      const data = await res.json();
      if (res.ok) {
        setToken(data.token);
        setUser(data.user);
        localStorage.setItem("risklattice_token", data.token);
        localStorage.setItem("risklattice_user", JSON.stringify(data.user));
        return { success: true };
      } else {
        return { success: false, error: data.detail || "Registration failed." };
      }
    } catch (e: any) {
      console.error("Registration failed", e);
      return { success: false, error: e.message || "Network error during registration." };
    } finally {
      setIsLoading(false);
    }
  };

  const loginWithGoogleCredential = async (credential: string): Promise<AuthResult> => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/google`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential }),
      });

      const data = await res.json();
      if (res.ok) {
        setToken(data.token);
        setUser(data.user);
        localStorage.setItem("risklattice_token", data.token);
        localStorage.setItem("risklattice_user", JSON.stringify(data.user));
        return { success: true };
      }
      return { success: false, error: data.detail || "Google login failed" };
    } catch (e: any) {
      console.error("Google login failed", e);
      return { success: false, error: e.message || "Google OAuth network error." };
    } finally {
      setIsLoading(false);
    }
  };

  const loginWithPersona = async (
    email: string,
    name: string,
    role: UserRole,
    organization: string
  ): Promise<AuthResult> => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/google`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, name, role, organization }),
      });

      const data = await res.json();
      if (res.ok) {
        setToken(data.token);
        setUser(data.user);
        localStorage.setItem("risklattice_token", data.token);
        localStorage.setItem("risklattice_user", JSON.stringify(data.user));
        return { success: true };
      }
      return { success: false, error: data.detail || "Persona login failed" };
    } catch (e: any) {
      console.error("Persona login failed", e);
      return { success: false, error: e.message || "Persona network error." };
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    if (token) {
      fetch(`${API_BASE}/api/v1/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => {});
    }
    setToken(null);
    setUser(null);
    localStorage.removeItem("risklattice_token");
    localStorage.removeItem("risklattice_user");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        loginWithCredentials,
        registerUser,
        loginWithGoogleCredential,
        loginWithPersona,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
