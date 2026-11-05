import { Component, inject, signal } from '@angular/core';
import {
  AbstractControl,
  NonNullableFormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { apiErrorMessage } from '../../core/api-error';
import { MIN_PASSWORD_LENGTH } from '../auth-page/auth-page';
import { AuthService } from '../auth.service';

/** The new password typed the same way twice (a typo here would lock you out). */
function sameNewPassword(group: AbstractControl): ValidationErrors | null {
  const { newPassword, repeat } = group.value as { newPassword: string; repeat: string };
  return !repeat || newPassword === repeat ? null : { different: true };
}

/** Change the password while logged in (/password); the email in the header links here. */
@Component({
  imports: [ReactiveFormsModule],
  selector: 'app-password-page',
  // The same card and fields as the login page.
  styleUrl: '../auth-page/auth-page.css',
  templateUrl: './password-page.html',
})
export class PasswordPage {
  private readonly auth = inject(AuthService);

  protected readonly minPasswordLength = MIN_PASSWORD_LENGTH;

  protected readonly form = inject(NonNullableFormBuilder).group(
    {
      current: ['', Validators.required],
      newPassword: ['', [Validators.required, Validators.minLength(MIN_PASSWORD_LENGTH)]],
      repeat: ['', Validators.required],
    },
    { validators: sameNewPassword },
  );

  protected readonly busy = signal(false);
  protected readonly error = signal('');
  protected readonly done = signal(false);

  protected showError(name: 'current' | 'newPassword' | 'repeat'): boolean {
    const control = this.form.controls[name];
    return control.invalid && (control.touched || control.dirty);
  }

  /** Shown under the repeat field once it's filled in and doesn't match. */
  protected different(): boolean {
    return this.form.hasError('different') && this.form.controls.repeat.dirty;
  }

  protected submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.form.controls.repeat.markAsDirty(); // so a mismatch shows too
      return;
    }
    const { current, newPassword } = this.form.getRawValue();
    this.busy.set(true);
    this.error.set('');
    this.done.set(false);
    this.auth.changePassword(current, newPassword).subscribe({
      next: () => {
        this.busy.set(false);
        this.done.set(true);
        this.form.reset(); // never keep passwords around
      },
      error: (error: unknown) => {
        this.busy.set(false);
        this.error.set(apiErrorMessage(error)); // 400 wrong current password, 429 too many tries
        this.form.controls.current.reset();
      },
    });
  }
}
