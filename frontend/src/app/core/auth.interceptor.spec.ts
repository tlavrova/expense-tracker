import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { AuthService } from '../auth/auth.service';
import { fakeToken, storeToken } from '../auth/testing';
import { authInterceptor } from './auth.interceptor';

const api = environment.apiUrl;

function setup(token: string | null) {
  storeToken(token);
  TestBed.configureTestingModule({
    providers: [
      provideRouter([]),
      provideHttpClient(withInterceptors([authInterceptor])),
      provideHttpClientTesting(),
    ],
  });
  const auth = TestBed.inject(AuthService);
  const logout = vi.spyOn(auth, 'logout').mockImplementation(() => undefined);
  return {
    client: TestBed.inject(HttpClient),
    http: TestBed.inject(HttpTestingController),
    logout,
  };
}

describe('authInterceptor', () => {
  afterEach(() => storeToken(null));

  it('sends the token to our API', () => {
    const token = fakeToken();
    const { client, http } = setup(token);
    client.get(`${api}/expenses`).subscribe();
    expect(http.expectOne(`${api}/expenses`).request.headers.get('Authorization')).toBe(
      `Bearer ${token}`,
    );
  });

  it('never sends the token to another site', () => {
    const { client, http } = setup(fakeToken());
    client.get('https://example.com/data').subscribe();
    client.get(`${api}.evil.example/expenses`).subscribe(); // looks like ours, isn't
    for (const request of http.match(() => true)) {
      expect(request.request.headers.has('Authorization')).toBe(false);
    }
  });

  it('sends no header when logged out', () => {
    const { client, http } = setup(null);
    client.get(`${api}/expenses`).subscribe();
    expect(http.expectOne(`${api}/expenses`).request.headers.has('Authorization')).toBe(false);
  });

  it('logs out with a notice when the API answers 401', async () => {
    const { client, http, logout } = setup(fakeToken());
    const answer = firstValueFrom(client.get(`${api}/summary`));
    http
      .expectOne(`${api}/summary`)
      .flush({ detail: 'Please log in.' }, { status: 401, statusText: 'Unauthorized' });
    await expect(answer).rejects.toMatchObject({ status: 401 });
    expect(logout).toHaveBeenCalledWith('Your login has expired. Please log in again.');
  });

  it('leaves a 401 from the login itself to the login page', async () => {
    const { client, http, logout } = setup(null);
    const answer = firstValueFrom(client.post(`${api}/auth/login`, {}));
    http
      .expectOne(`${api}/auth/login`)
      .flush({ detail: 'Wrong email or password.' }, { status: 401, statusText: 'Unauthorized' });
    await expect(answer).rejects.toMatchObject({ status: 401 });
    expect(logout).not.toHaveBeenCalled();
  });

  it('does not log out on other errors', async () => {
    const { client, http, logout } = setup(fakeToken());
    const answer = firstValueFrom(client.get(`${api}/expenses`));
    http
      .expectOne(`${api}/expenses`)
      .flush({ detail: 'Database is down.' }, { status: 500, statusText: 'Error' });
    await expect(answer).rejects.toMatchObject({ status: 500 });
    expect(logout).not.toHaveBeenCalled();
  });
});
