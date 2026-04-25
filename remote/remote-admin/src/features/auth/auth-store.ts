export const ACCESS_TOKEN_KEY = 'remote_admin_access_token';

const AUTH_STORAGE_EVENT = 'remote-admin-auth-storage';

function broadcastStorageChange(): void {
  window.dispatchEvent(new Event(AUTH_STORAGE_EVENT));
}

export function getStoredAccessToken(): string | null {
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setStoredAccessToken(value: string): void {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, value);
  broadcastStorageChange();
}

export function clearStoredAccessToken(): void {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  broadcastStorageChange();
}

export function subscribeAuthStorage(callback: () => void): () => void {
  const handler = () => callback();
  window.addEventListener(AUTH_STORAGE_EVENT, handler);
  window.addEventListener('storage', handler);
  return () => {
    window.removeEventListener(AUTH_STORAGE_EVENT, handler);
    window.removeEventListener('storage', handler);
  };
}
