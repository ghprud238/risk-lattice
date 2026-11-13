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

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  loginWithGoogleCredential: (credential: string) => Promise<boolean>;
  loginWithPersona: (email: string, name: string, role: UserRole, organization: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  loginWithGoogleCredential: async () => false,
  loginWithPersona: async () => false,
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
              // Token invalid
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

  const loginWithGoogleCredential = async (credential: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/google`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential }),
      });

      if (res.ok) {
        const data = await res.json();
        setToken(data.token);
        setUser(data.user);
        localStorage.setItem("risklattice_token", data.token);
        localStorage.setItem("risklattice_user", JSON.stringify(data.user));
        return true;
      }
      return false;
    } catch (e) {
      console.error("Google login failed", e);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const loginWithPersona = async (
    email: string,
    name: string,
    role: UserRole,
    organization: string
  ): Promise<boolean> => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/google`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, name, role, organization }),
      });

      if (res.ok) {
        const data = await res.json();
        setToken(data.token);
        setUser(data.user);
        localStorage.setItem("risklattice_token", data.token);
        localStorage.setItem("risklattice_user", JSON.stringify(data.user));
        return true;
      }
      return false;
    } catch (e) {
      console.error("Persona login failed", e);
      return false;
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
