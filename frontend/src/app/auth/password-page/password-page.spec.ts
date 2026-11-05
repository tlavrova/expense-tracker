import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { Observable, of, throwError } from 'rxjs';
import { AuthService } from '../auth.service';
import { PasswordPage } from './password-page';

async function render(changePassword: (current: string, next: string) => Observable<void>) {
  await TestBed.configureTestingModule({
    imports: [PasswordPage],
    providers: [{ provide: AuthService, useValue: { changePassword } }],
  }).compileComponents();
  const fixture = TestBed.createComponent(PasswordPage);
  await fixture.whenStable();
  const page = fixture.nativeElement as HTMLElement;
  const type = (name: string, value: string) => {
    const field = page.querySelector<HTMLInputElement>(`[formControlName=${name}]`)!;
    field.value = value;
    field.dispatchEvent(new Event('input'));
  };
  const submit = async () => {
    page.querySelector('form')!.dispatchEvent(new Event('submit'));
    await fixture.whenStable();
  };
  const errors = () =>
    [...page.querySelectorAll('.field-error')].map((error) => error.textContent?.trim());
  const value = (name: string) =>
    page.querySelector<HTMLInputElement>(`[formControlName=${name}]`)!.value;
  return { page, type, submit, errors, value };
}

describe('PasswordPage', () => {
  it('asks for all three fields before sending anything', async () => {
    const changePassword = vi.fn();
    const { submit, errors } = await render(changePassword);
    await submit();
    expect(changePassword).not.toHaveBeenCalled();
    expect(errors()).toEqual([
      'Please enter your current password.',
      'Please enter a new password.',
      'Please type the new password again.',
    ]);
  });

  it('needs a long enough new password, typed the same way twice', async () => {
    const changePassword = vi.fn();
    const { type, submit, errors } = await render(changePassword);
    type('current', 'correct horse');
    type('newPassword', 'short');
    type('repeat', 'short');
    await submit();
    expect(errors()).toEqual(['The new password needs at least 8 characters.']);
    type('newPassword', 'long enough one');
    type('repeat', 'long enough 0ne');
    await submit();
    expect(errors()).toEqual(['The two new passwords are different.']);
    expect(changePassword).not.toHaveBeenCalled();
  });

  it('changes the password, says so and clears the fields', async () => {
    const changePassword = vi.fn(() => of(undefined));
    const { page, type, submit, value } = await render(changePassword);
    type('current', 'correct horse');
    type('newPassword', 'new horse battery');
    type('repeat', 'new horse battery');
    await submit();
    expect(changePassword).toHaveBeenCalledWith('correct horse', 'new horse battery');
    expect(page.querySelector('[role=status]')?.textContent).toContain('Password changed.');
    expect([value('current'), value('newPassword'), value('repeat')]).toEqual(['', '', '']);
  });

  it("shows the API's message when the current password is wrong", async () => {
    const changePassword = vi.fn(() =>
      throwError(
        () =>
          new HttpErrorResponse({
            status: 400,
            error: { detail: 'Your current password is wrong.' },
          }),
      ),
    );
    const { page, type, submit, value } = await render(changePassword);
    type('current', 'wrong one');
    type('newPassword', 'new horse battery');
    type('repeat', 'new horse battery');
    await submit();
    expect(page.querySelector('[role=alert]')?.textContent).toContain(
      'Your current password is wrong.',
    );
    expect(page.querySelector('[role=status]')).toBeNull();
    expect(value('current')).toBe(''); // type it again
    expect(page.querySelector<HTMLButtonElement>('button[type=submit]')!.disabled).toBe(false);
  });
});
