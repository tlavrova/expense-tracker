import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { environment } from '../../environments/environment';
import { AuthService } from '../auth/auth.service';

/**
 * Every call to our API carries the login token; the token goes to no other site.
 *
 * When the API answers 401 (no token, expired, or not valid any more), the user is logged out and
 * sent to the login page. A wrong password on the login page itself is a 401 too, so calls to
 * /auth/login and /auth/signup are left to that page.
 */
export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const auth = inject(AuthService);
  const toOurApi = request.url.startsWith(`${environment.apiUrl}/`);
  const token = auth.token();
  if (toOurApi && token) {
    request = request.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
  }
  return next(request).pipe(
    catchError((error: unknown) => {
      const loginCall = /\/auth\/(login|signup)$/.test(request.url);
      if (toOurApi && !loginCall && error instanceof HttpErrorResponse && error.status === 401) {
        auth.logout('Your login has expired. Please log in again.');
      }
      return throwError(() => error);
    }),
  );
};
