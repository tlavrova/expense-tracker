/**
 * Helpers for the tests only (nothing in the app imports this file, so it isn't in the build).
 */

const STORAGE_KEY = 'expense-tracker.token';

function base64url(value: object): string {
  return btoa(JSON.stringify(value)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/** A token shaped like the backend's, expiring this many seconds from now (negative: expired). */
export function fakeToken(expiresInSeconds = 3600): string {
  const exp = Math.floor(Date.now() / 1000) + expiresInSeconds;
  return `${base64url({ alg: 'HS256', typ: 'JWT' })}.${base64url({ sub: '1', exp })}.signature`;
}

/** Pretend an earlier visit left a token behind (read when AuthService is created). */
export function storeToken(token: string | null): void {
  if (token) {
    localStorage.setItem(STORAGE_KEY, token);
  } else {
    localStorage.removeItem(STORAGE_KEY);
  }
}

export function storedToken(): string | null {
  return localStorage.getItem(STORAGE_KEY);
}
