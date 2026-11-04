import { HttpErrorResponse, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { AuthService } from './auth.service';
import { tokenExpiry } from './token';
import { fakeToken, storeToken, storedToken } from './testing';

const api = environment.apiUrl;

function setup() {
  TestBed.configureTestingModule({
    providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
  });
  const navigate = vi.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);
  return {
    auth: TestBed.inject(AuthService),
    http: TestBed.inject(HttpTestingController),
    navigate,
  };
}

describe('AuthService', () => {
  afterEach(() => {
    storeToken(null);
    TestBed.inject(HttpTestingController).verify();
  });

  it('starts logged out when nothing is stored', () => {
    const { auth } = setup();
    expect(auth.loggedIn()).toBe(false);
    expect(auth.token()).toBeNull();
  });

  it('keeps a stored token that has not expired yet', () => {
    const token = fakeToken(600);
    storeToken(token);
    const { auth } = setup();
    expect(auth.token()).toBe(token);
  });

  it('ignores a stored token that has expired', () => {
    storeToken(fakeToken(-60));
    expect(setup().auth.loggedIn()).toBe(false);
  });

  it('logs in with the OAuth2 form, keeps the token and loads the email', async () => {
    const { auth, http } = setup();
    const done = firstValueFrom(auth.login('ana@example.com', 'correct horse'), {
      defaultValue: undefined,
    });
    const request = http.expectOne(`${api}/auth/login`);
    expect(request.request.method).toBe('POST');
    expect(request.request.body.toString()).toBe(
      'username=ana@example.com&password=correct%20horse',
    );
    const token = fakeToken();
    request.flush({ access_token: token, token_type: 'bearer' });
    await done;
    expect(auth.loggedIn()).toBe(true);
    expect(storedToken()).toBe(token);
    http.expectOne(`${api}/auth/me`).flush({ id: 1, email: 'ana@example.com' });
    expect(auth.email()).toBe('ana@example.com');
  });

  it('signs up with JSON and is logged in straight away', async () => {
    const { auth, http } = setup();
    const done = firstValueFrom(auth.signup('ana@example.com', 'correct horse'), {
      defaultValue: undefined,
    });
    const request = http.expectOne(`${api}/auth/signup`);
    expect(request.request.body).toEqual({ email: 'ana@example.com', password: 'correct horse' });
    request.flush(
      { access_token: fakeToken(), token_type: 'bearer' },
      { status: 201, statusText: 'Created' },
    );
    await done;
    expect(auth.loggedIn()).toBe(true);
    http.expectOne(`${api}/auth/me`).flush({ id: 1, email: 'ana@example.com' });
  });

  it('keeps nothing when the login fails', async () => {
    const { auth, http } = setup();
    const done = firstValueFrom(auth.login('ana@example.com', 'wrong'));
    http
      .expectOne(`${api}/auth/login`)
      .flush({ detail: 'Wrong email or password.' }, { status: 401, statusText: 'Unauthorized' });
    await expect(done).rejects.toBeInstanceOf(HttpErrorResponse);
    expect(auth.loggedIn()).toBe(false);
    expect(storedToken()).toBeNull();
  });

  it('logs out: forgets the token and goes to the login page', () => {
    storeToken(fakeToken());
    const { auth, navigate } = setup();
    auth.logout();
    expect(auth.loggedIn()).toBe(false);
    expect(storedToken()).toBeNull();
    expect(navigate).toHaveBeenCalledWith(['/login'], { queryParams: { returnUrl: undefined } });
  });

  it('after an expiry, says why and remembers where to come back to', () => {
    storeToken(fakeToken());
    const { auth, navigate } = setup();
    vi.spyOn(TestBed.inject(Router), 'url', 'get').mockReturnValue('/summary');
    auth.logout('Your login has expired. Please log in again.');
    expect(auth.notice()).toContain('expired');
    expect(navigate).toHaveBeenCalledWith(['/login'], { queryParams: { returnUrl: '/summary' } });
  });

  it('logs out only once when several calls fail with 401 at the same time', () => {
    storeToken(fakeToken());
    const { auth, navigate } = setup();
    const url = vi.spyOn(TestBed.inject(Router), 'url', 'get').mockReturnValue('/summary');
    auth.logout('Your login has expired. Please log in again.');
    url.mockReturnValue('/login?returnUrl=%2Fsummary'); // the first logout is on its way there
    auth.logout('Your login has expired. Please log in again.');
    expect(navigate).toHaveBeenCalledTimes(1);
    expect(navigate).toHaveBeenCalledWith(['/login'], { queryParams: { returnUrl: '/summary' } });
  });
});

describe('tokenExpiry()', () => {
  it('reads exp from the token, and 0 from anything else', () => {
    expect(tokenExpiry(fakeToken(0))).toBe(Math.floor(Date.now() / 1000));
    expect(tokenExpiry('not-a-token')).toBe(0);
    expect(tokenExpiry('a.bm90IGpzb24.c')).toBe(0);
  });
});
