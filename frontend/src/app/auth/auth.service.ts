import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, map, tap } from 'rxjs';
import { environment } from '../../environments/environment';

/** What /auth/signup and /auth/login answer (backend/schemas.py Token). */
interface TokenAnswer {
  access_token: string;
  token_type: string;
}

/** Where the token is kept between visits; it is never put in a URL or logged. */
const STORAGE_KEY = 'expense-tracker.token';

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

function readStoredToken(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null; // storage blocked (private mode, settings): just not remembered
  }
}

/**
 * Who is logged in, and logging in and out.
 *
 * The token from the API is kept in localStorage, so a reload keeps you logged in until it
 * expires (7 days, set by the backend). The API checks the token on every call; the expiry read
 * here only decides early that a stored token is too old to try.
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly url = `${environment.apiUrl}/auth`;

  private readonly storedToken = signal(readStoredToken());
  /** The email of the logged-in user, once /auth/me has answered. */
  readonly email = signal('');
  /** Why the user is on the login page, for example after the login expired. */
  readonly notice = signal('');

  /** The token, if there is one and it hasn't expired yet. */
  readonly token = computed(() => {
    const token = this.storedToken();
    return token && tokenExpiry(token) * 1000 > Date.now() ? token : null;
  });
  readonly loggedIn = computed(() => this.token() !== null);

  /** Log in with email and password (sent as the OAuth2 form the backend expects). */
  login(email: string, password: string): Observable<void> {
    const form = new HttpParams().set('username', email).set('password', password);
    return this.http.post<TokenAnswer>(`${this.url}/login`, form).pipe(
      tap((answer) => this.keep(answer.access_token)),
      map(() => undefined),
    );
  }

  /** Create an account; the backend logs it in straight away. */
  signup(email: string, password: string): Observable<void> {
    return this.http.post<TokenAnswer>(`${this.url}/signup`, { email, password }).pipe(
      tap((answer) => this.keep(answer.access_token)),
      map(() => undefined),
    );
  }

  /** Forget the token and go to the login page, optionally saying why. */
  logout(notice = ''): void {
    // Several calls can fail at once with 401 (the page's data and /auth/me): log out only once,
    // so the second one doesn't remember the login page as "where you were".
    if (notice && this.storedToken() === null) {
      return;
    }
    this.storedToken.set(null);
    this.email.set('');
    this.notice.set(notice);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // nothing stored, nothing to remove
    }
    const here = this.router.url;
    // After an expiry, come back here (but never "back" to the login page itself).
    const returnUrl = notice && !here.startsWith('/login') ? here : undefined;
    this.router.navigate(['/login'], { queryParams: { returnUrl } });
  }

  private keep(token: string): void {
    this.storedToken.set(token);
    this.notice.set('');
    try {
      localStorage.setItem(STORAGE_KEY, token);
    } catch {
      // can't remember it: logged in until the page is closed
    }
    this.loadEmail();
  }

  /**
   * Ask the API who is logged in, for the header. Not called from the constructor: the request
   * passes through the interceptor, which needs this service to exist already.
   */
  loadEmail(): void {
    this.http.get<{ email: string }>(`${this.url}/me`).subscribe({
      next: (me) => this.email.set(me.email),
      error: () => this.email.set(''), // a 401 here is handled by the interceptor
    });
  }
}
