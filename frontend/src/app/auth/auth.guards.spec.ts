import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { loggedInGuard, loggedOutGuard } from './auth.guards';
import { fakeToken, storeToken } from './testing';

@Component({ template: '' })
class Blank {}

async function visit(url: string, token: string | null): Promise<string> {
  storeToken(token);
  TestBed.configureTestingModule({
    providers: [
      provideHttpClient(),
      provideHttpClientTesting(),
      provideRouter([
        { path: 'login', component: Blank, canActivate: [loggedOutGuard] },
        { path: 'expenses', component: Blank },
        {
          path: '',
          canActivateChild: [loggedInGuard],
          children: [{ path: 'summary', component: Blank }],
        },
      ]),
    ],
  });
  const router = TestBed.inject(Router);
  await router.navigateByUrl(url);
  return router.url;
}

describe('route guards', () => {
  afterEach(() => storeToken(null));

  it('send logged-out visitors to the login page, remembering where they were going', async () => {
    expect(await visit('/summary?x=1', null)).toBe('/login?returnUrl=%2Fsummary%3Fx%3D1');
  });

  it('let logged-in users in', async () => {
    expect(await visit('/summary', fakeToken())).toBe('/summary');
  });

  it('treat an expired token as logged out', async () => {
    expect(await visit('/summary', fakeToken(-1))).toBe('/login?returnUrl=%2Fsummary');
  });

  it('send logged-in users past the login page', async () => {
    expect(await visit('/login', fakeToken())).toBe('/expenses');
  });
});
