import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { environment } from '../environments/environment';
import { App } from './app';
import { routes } from './app.routes';
import { fakeToken, storeToken } from './auth/testing';

async function render(url: string, token: string | null) {
  storeToken(token);
  await TestBed.configureTestingModule({
    imports: [App],
    providers: [provideRouter(routes), provideHttpClient(), provideHttpClientTesting()],
  }).compileComponents();
  const fixture = TestBed.createComponent(App);
  const http = TestBed.inject(HttpTestingController);
  await TestBed.inject(Router).navigateByUrl(url);
  for (const request of http.match(`${environment.apiUrl}/auth/me`)) {
    request.flush({ id: 1, email: 'ana@example.com' });
  }
  await fixture.whenStable();
  return fixture.nativeElement as HTMLElement;
}

describe('App', () => {
  afterEach(() => storeToken(null));

  it('shows the app name, the navigation and who is logged in', async () => {
    const page = await render('/expenses', fakeToken());
    expect(page.querySelector('.brand')?.textContent).toContain('Expense Tracker');
    const links = Array.from(page.querySelectorAll('nav a')).map((link) =>
      link.textContent?.trim(),
    );
    expect(links).toEqual(['Expenses', 'Add expense', 'Summary']);
    expect(page.querySelector('.email')?.textContent).toBe('ana@example.com');
    expect(page.querySelector('.email')?.getAttribute('href')).toBe('/password'); // change password
    expect(page.querySelector('button.logout')).not.toBeNull();
  });

  it('shows no navigation when logged out, and the login page instead of the expenses', async () => {
    const page = await render('/expenses', null);
    expect(page.querySelector('nav')).toBeNull();
    expect(page.querySelector('button.logout')).toBeNull();
    expect(page.querySelector('h1')?.textContent).toContain('Log in');
  });

  it('keeps "Expenses" highlighted while filters are in the address', async () => {
    const page = await render('/expenses?category=food&sort=amount', fakeToken());
    expect(page.querySelector('nav a.active')?.textContent?.trim()).toBe('Expenses');
  });
});
