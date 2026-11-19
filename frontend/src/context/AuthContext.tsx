import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { api, getStoredUser, getToken, setStoredUser, setToken } from "@/lib/api";
import type { AuthUser, Role, TokenResponse } from "@/lib/types";

interface LoginInput {
  role: Role;
  identifier: string;
  password: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (input: LoginInput) => Promise<AuthUser>;
  setupAdmin: (payload: {
    name: string;
    email: string;
    password: string;
    confirm_password: string;
  }) => Promise<AuthUser>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function storeSession(session: TokenResponse): AuthUser {
  setToken(session.access_token);
  setStoredUser(session.user);
  return session.user;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => getStoredUser<AuthUser>());
  const [loading, setLoading] = useState(Boolean(getToken()));

  const clear = useCallback(() => {
    setToken(null);
    setStoredUser(null);
    setUser(null);
  }, []);

  const refresh = useCallback(async () => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    try {
      const me = await api<AuthUser>("/auth/me");
      setStoredUser(me);
      setUser(me);
    } catch {
      clear();
    } finally {
      setLoading(false);
    }
  }, [clear]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    const handler = () => clear();
    window.addEventListener("facultyinsight:unauthorized", handler);
    return () => window.removeEventListener("facultyinsight:unauthorized", handler);
  }, [clear]);

  const login = useCallback(async ({ role, identifier, password }: LoginInput) => {
    const payload =
      role === "student"
        ? { student_id: identifier, password }
        : { email: identifier, password };
    const session = await api<TokenResponse>(`/auth/${role}/login`, {
      method: "POST",
      body: payload,
    });
    storeSession(session);
    setUser(session.user);
    return session.user;
  }, []);

  const setupAdmin = useCallback(
    async (payload: { name: string; email: string; password: string; confirm_password: string }) => {
      const session = await api<TokenResponse>("/auth/admin/setup", {
        method: "POST",
        body: payload,
      });
      return storeSession(session);
    },
    [],
  );

  const value = useMemo(
    () => ({ user, loading, login, setupAdmin, logout: clear, refresh }),
    [user, loading, login, setupAdmin, clear, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
