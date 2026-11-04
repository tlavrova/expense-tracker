import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, computed, inject, input, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { Observable } from 'rxjs';
import { apiErrorMessage } from '../../core/api-error';
import { AuthService } from '../auth.service';

/** The same minimum as the backend (schemas.SignupRequest). */
export const MIN_PASSWORD_LENGTH = 8;

/**
 * The login page and the sign-up page: the same form, two modes (set in app.routes.ts).
 *
 * After success it goes to returnUrl (the page that asked for a login) or to the expenses.
 */
@Component({
  imports: [ReactiveFormsModule, RouterLink],
  selector: 'app-auth-page',
  styleUrl: './auth-page.css',
  templateUrl: './auth-page.html',
})
export class AuthPage implements OnInit {
  private readonly router = inject(Router);
  protected readonly auth = inject(AuthService);

  /** From the route's data; inputs from the router need withComponentInputBinding(). */
  readonly mode = input<'login' | 'signup'>('login');
  /** From the address (?returnUrl=/summary). */
  readonly returnUrl = input<string>();

  protected readonly signingUp = computed(() => this.mode() === 'signup');
  protected readonly minPasswordLength = MIN_PASSWORD_LENGTH;

  protected readonly form = inject(NonNullableFormBuilder).group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

  protected readonly busy = signal(false);
  protected readonly error = signal('');

  ngOnInit(): void {
    // The length rule is for new passwords only; logging in just needs something typed.
    // (Inputs from the route are set by now, not yet in the constructor.)
    if (this.signingUp()) {
      this.form.controls.password.addValidators(Validators.minLength(MIN_PASSWORD_LENGTH));
      this.form.controls.password.updateValueAndValidity();
    }
  }

  protected showError(name: 'email' | 'password'): boolean {
    const control = this.form.controls[name];
    return control.invalid && (control.touched || control.dirty);
  }

  protected submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { email, password: secret } = this.form.getRawValue();
    const request: Observable<void> = this.signingUp()
      ? this.auth.signup(email.trim(), secret)
      : this.auth.login(email.trim(), secret);
    this.busy.set(true);
    this.error.set('');
    request.subscribe({
      next: () => this.router.navigateByUrl(this.safeReturnUrl()),
      error: (error: unknown) => {
        this.busy.set(false);
        this.error.set(this.messageFor(error));
        this.form.controls.password.reset(); // type it again; never kept around after a failure
      },
    });
  }

  /** Only a page of this site, never another address someone put into the link. */
  private safeReturnUrl(): string {
    const url = this.returnUrl();
    return url && url.startsWith('/') && !url.startsWith('//') && !url.startsWith('/login')
      ? url
      : '/expenses';
  }

  private messageFor(error: unknown): string {
    if (error instanceof HttpErrorResponse && error.status === 401) {
      return 'Wrong email or password.';
    }
    return apiErrorMessage(error); // 409 "already an account", 422 details, API not running
  }
}
