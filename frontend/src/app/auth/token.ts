/**
 * The login token itself: keeping it between visits, and reading its expiry.
 *
 * It lives in localStorage under one key, so a reload keeps you logged in. It is never put in a
 * URL or logged. When the browser blocks storage (private mode, settings), nothing is remembered
 * and you stay logged in only until the page is closed.
 */

export const STORAGE_KEY = 'expense-tracker.token';

export function readToken(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export function saveToken(token: string): void {
  try {
    localStorage.setItem(STORAGE_KEY, token);
  } catch {
    // can't remember it: logged in until the page is closed
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // nothing stored, nothing to remove
  }
}

/** The seconds-since-1970 expiry inside a JWT, or 0 if it can't be read. */
export function tokenExpiry(token: string): number {
  try {
    const payload = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    const claims = JSON.parse(atob(payload)) as { exp?: unknown };
    return typeof claims.exp === 'number' ? claims.exp : 0;
  } catch {
    return 0;
  }
}
