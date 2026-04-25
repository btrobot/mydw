import { createContext, useContext, useEffect, useMemo, useState } from 'react';

import { getCurrentAdminSession, loginAdmin, type AdminSession } from './auth-client.js';
import { clearStoredAccessToken, getStoredAccessToken, setStoredAccessToken, subscribeAuthStorage } from './auth-store.js';

type AuthStatus = 'restoring' | 'anonymous' | 'authenticated';

type AuthContextValue = {
  status: AuthStatus;
  accessToken: string | null;
  session: AdminSession | null;
  authNotice: string | null;
  login: (username: string, password: string) => Promise<AdminSession>;
  logout: () => void;
  refreshSession: () => Promise<void>;
  handleExpiredSession: (message?: string) => void;
  clearAuthNotice: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }): JSX.Element {
  const [accessToken, setAccessToken] = useState<string | null>(() => getStoredAccessToken());
  const [session, setSession] = useState<AdminSession | null>(null);
  const [status, setStatus] = useState<AuthStatus>(() => (getStoredAccessToken() ? 'restoring' : 'anonymous'));
  const [authNotice, setAuthNotice] = useState<string | null>(null);

  useEffect(() => subscribeAuthStorage(() => setAccessToken(getStoredAccessToken())), []);

  useEffect(() => {
    if (!accessToken) {
      setSession(null);
      setStatus('anonymous');
      return;
    }

    let cancelled = false;
    setStatus('restoring');

    void getCurrentAdminSession(accessToken)
      .then((nextSession) => {
        if (cancelled) return;
        setSession(nextSession);
        setStatus('authenticated');
      })
      .catch(() => {
        if (cancelled) return;
        clearStoredAccessToken();
        setSession(null);
        setStatus('anonymous');
        setAuthNotice('Your previous admin session expired. Please sign in again.');
      });

    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      accessToken,
      session,
      authNotice,
      async login(username: string, password: string) {
        const response = await loginAdmin(username, password);
        setStoredAccessToken(response.access_token);
        const nextSession: AdminSession = {
          session_id: response.session_id,
          expires_at: response.expires_at,
          user: response.user,
        };
        setSession(nextSession);
        setStatus('authenticated');
        setAccessToken(response.access_token);
        setAuthNotice(null);
        return nextSession;
      },
      logout() {
        clearStoredAccessToken();
        setSession(null);
        setStatus('anonymous');
        setAccessToken(null);
        setAuthNotice(null);
      },
      async refreshSession() {
        const token = getStoredAccessToken();
        if (!token) {
          setSession(null);
          setStatus('anonymous');
          setAccessToken(null);
          return;
        }
        const nextSession = await getCurrentAdminSession(token);
        setSession(nextSession);
        setStatus('authenticated');
        setAccessToken(token);
        setAuthNotice(null);
      },
      handleExpiredSession(message = 'Your admin session expired. Please sign in again.') {
        clearStoredAccessToken();
        setSession(null);
        setStatus('anonymous');
        setAccessToken(null);
        setAuthNotice(message);
      },
      clearAuthNotice() {
        setAuthNotice(null);
      },
    }),
    [accessToken, authNotice, session, status]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
