import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

/** Pages that need a login: logged-out users go to the login page, and come back after it. */
export const loggedInGuard: CanActivateFn = (_route, state) => {
  if (inject(AuthService).loggedIn()) {
    return true;
  }
  return inject(Router).createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
};

/** The login and sign-up pages: someone already logged in goes straight to the expenses. */
export const loggedOutGuard: CanActivateFn = () =>
  inject(AuthService).loggedIn() ? inject(Router).createUrlTree(['/expenses']) : true;
