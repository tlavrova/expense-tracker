import { HttpErrorResponse } from '@angular/common/http';
import { Component, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { Observable, of, throwError } from 'rxjs';
import { AuthService } from '../auth.service';
import { AuthPage } from './auth-page';

@Component({ template: 'page' })
class Blank {}

interface FakeAuth {
  login: (email: string, password: string) => Observable<void>;
  signup: (email: string, password: string) => Observable<void>;
  notice: ReturnType<typeof signal<string>>;
}

async function open(url: string, auth: Partial<FakeAuth> = {}) {
  const fake: FakeAuth = {
    login: vi.fn(() => of(undefined)),
    signup: vi.fn(() => of(undefined)),
    notice: signal(''),
    ...auth,
  };
  TestBed.configureTestingModule({
    providers: [
      provideRouter(
        [
          { path: 'login', component: AuthPage, data: { mode: 'login' } },
          { path: 'signup', component: AuthPage, data: { mode: 'signup' } },
          { path: 'expenses', component: Blank },
          { path: 'summary', component: Blank },
        ],
        withComponentInputBinding(),
      ),
      { provide: AuthService, useValue: fake },
    ],
  });
  const harness = await RouterTestingHarness.create(url);
  const page = () => harness.routeNativeElement as HTMLElement;
  const type = (name: string, value: string) => {
    const field = page().querySelector<HTMLInputElement>(`[formControlName=${name}]`)!;
    field.value = value;
    field.dispatchEvent(new Event('input'));
  };
  const submit = async () => {
    page().querySelector('form')!.dispatchEvent(new Event('submit'));
    await harness.fixture.whenStable();
  };
  return { fake, harness, page, type, submit, router: TestBed.inject(Router) };
}

describe('AuthPage: log in', () => {
  it('shows the login form with a link to sign up', async () => {
    const { page } = await open('/login');
    expect(page().querySelector('h1')?.textContent).toContain('Log in');
    expect(page().querySelector('.switch a')?.getAttribute('href')).toBe('/signup');
  });

  it('asks for both fields before sending anything', async () => {
    const { fake, page, submit } = await open('/login');
    await submit();
    expect(fake.login).not.toHaveBeenCalled();
    expect(page().textContent).toContain('Please enter your email address.');
    expect(page().textContent).toContain('Please enter your password.');
  });

  it('accepts a short password when logging in (length rules are for new ones)', async () => {
    const { fake, type, submit } = await open('/login');
    type('email', ' ana@example.com ');
    type('password', 'short');
    await submit();
    expect(fake.login).toHaveBeenCalledWith('ana@example.com', 'short');
  });

  it('goes back to the page that asked for the login', async () => {
    const { type, submit, router } = await open('/login?returnUrl=%2Fsummary');
    type('email', 'ana@example.com');
    type('password', 'correct horse');
    await submit();
    expect(router.url).toBe('/summary');
  });

  for (const unsafe of ['//evil.example', 'https://evil.example', '/login']) {
    it(`goes to the expenses instead of returnUrl=${unsafe}`, async () => {
      const { type, submit, router } = await open(`/login?returnUrl=${encodeURIComponent(unsafe)}`);
      type('email', 'ana@example.com');
      type('password', 'correct horse');
      await submit();
      expect(router.url).toBe('/expenses');
    });
  }

  it('says when the email or password is wrong, and clears the password', async () => {
    const login = vi.fn(() => throwError(() => new HttpErrorResponse({ status: 401 })));
    const { page, type, submit } = await open('/login', { login });
    type('email', 'ana@example.com');
    type('password', 'wrong one');
    await submit();
    expect(page().querySelector('[role=alert]')?.textContent).toContain('Wrong email or password.');
    expect(page().querySelector<HTMLInputElement>('[formControlName=password]')!.value).toBe('');
    expect(page().querySelector<HTMLButtonElement>('button[type=submit]')!.disabled).toBe(false);
  });

  it('shows why the user was sent here', async () => {
    const { page } = await open('/login', {
      notice: signal('Your login has expired. Please log in again.'),
    });
    expect(page().querySelector('[role=status]')?.textContent).toContain('expired');
  });
});

describe('AuthPage: sign up', () => {
  it('shows the sign-up form with the password rule', async () => {
    const { page } = await open('/signup');
    expect(page().querySelector('h1')?.textContent).toContain('Create an account');
    expect(page().textContent).toContain('At least 8 characters.');
    expect(page().querySelector('[formControlName=password]')?.getAttribute('autocomplete')).toBe(
      'new-password',
    );
  });

  it('needs a password of at least 8 characters and a real-looking email', async () => {
    const { fake, page, type, submit } = await open('/signup');
    type('email', 'not-an-email');
    type('password', 'short');
    await submit();
    expect(fake.signup).not.toHaveBeenCalled();
    expect(page().textContent).toContain('Please enter your email address.');
    expect(page().textContent).toContain('The password needs at least 8 characters.');
  });

  it('creates the account and goes to the expenses', async () => {
    const { fake, type, submit, router } = await open('/signup');
    type('email', 'ana@example.com');
    type('password', 'correct horse');
    await submit();
    expect(fake.signup).toHaveBeenCalledWith('ana@example.com', 'correct horse');
    expect(router.url).toBe('/expenses');
  });

  it("shows the API's message when the email has an account already", async () => {
    const signup = vi.fn(() =>
      throwError(
        () =>
          new HttpErrorResponse({
            status: 409,
            error: { detail: 'There is already an account with this email.' },
          }),
      ),
    );
    const { page, type, submit } = await open('/signup', { signup });
    type('email', 'ana@example.com');
    type('password', 'correct horse');
    await submit();
    expect(page().querySelector('[role=alert]')?.textContent).toContain('already an account');
  });
});
