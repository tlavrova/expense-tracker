import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { Expense } from './expense.model';
import { ExpenseService } from './expense.service';

describe('ExpenseService (HTTP)', () => {
  let service: ExpenseService;
  let http: HttpTestingController;
  const api = environment.apiUrl;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ExpenseService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify()); // no unexpected requests

  it('lists expenses with GET /expenses', async () => {
    const answer = firstValueFrom(service.list());
    const expenses: Expense[] = [
      { id: 1, amount: 12, category: 'food', description: 'Lunch', date: '2026-11-02' },
    ];
    const request = http.expectOne(`${api}/expenses`);
    expect(request.request.method).toBe('GET');
    request.flush(expenses);
    expect(await answer).toEqual(expenses);
  });

  it('sends only the filters that are set as query parameters', async () => {
    const answer = firstValueFrom(
      service.list({ category: 'food', month: '2026-11', sort: undefined }),
    );
    const request = http.expectOne((req) => req.url === `${api}/expenses`);
    expect(request.request.params.keys()).toEqual(['category', 'month']);
    expect(request.request.urlWithParams).toBe(`${api}/expenses?category=food&month=2026-11`);
    request.flush([]);
    expect(await answer).toEqual([]);
  });

  it('gets one expense with GET /expenses/{id} and changes it with PUT', async () => {
    const rent: Expense = {
      id: 7,
      amount: 900,
      category: 'housing',
      description: 'Rent',
      date: '2026-10-01',
    };
    const got = firstValueFrom(service.get(7));
    const get = http.expectOne(`${api}/expenses/7`);
    expect(get.request.method).toBe('GET');
    get.flush(rent);
    expect(await got).toEqual(rent);

    const { id, ...values } = { ...rent, amount: 950 };
    const saved = firstValueFrom(service.update(id!, values));
    const put = http.expectOne(`${api}/expenses/7`);
    expect(put.request.method).toBe('PUT');
    expect(put.request.body).toEqual(values);
    put.flush({ ...values, id });
    expect(await saved).toEqual({ ...values, id: 7 });
  });

  it('asks POST /suggest-category and returns just the category', async () => {
    const answer = firstValueFrom(service.suggestCategory('Uber to airport'));
    const request = http.expectOne(`${api}/suggest-category`);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ description: 'Uber to airport' });
    request.flush({ category: 'transport' });
    expect(await answer).toBe('transport');
  });

  it('adds with POST /expenses and returns the saved expense with its id', async () => {
    const expense = { amount: 5, category: 'food', description: 'Coffee', date: '2026-11-03' };
    const answer = firstValueFrom(service.add(expense));
    const request = http.expectOne(`${api}/expenses`);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual(expense);
    request.flush({ ...expense, id: 7 }, { status: 201, statusText: 'Created' });
    expect((await answer).id).toBe(7);
  });

  it('deletes with DELETE /expenses/{id}', async () => {
    const answer = firstValueFrom(service.delete(3), { defaultValue: undefined });
    const request = http.expectOne(`${api}/expenses/3`);
    expect(request.request.method).toBe('DELETE');
    request.flush(null, { status: 204, statusText: 'No Content' });
    await answer;
  });

  it('reads the summary with GET /summary', async () => {
    const answer = firstValueFrom(service.summary());
    http.expectOne(`${api}/summary`).flush({ totalsByCategory: { food: 12 }, total: 12 });
    expect((await answer).total).toBe(12);
  });

  it('passes API errors on to the caller', async () => {
    const answer = firstValueFrom(service.list());
    http
      .expectOne(`${api}/expenses`)
      .flush({ detail: 'Database is down.' }, { status: 500, statusText: 'Server Error' });
    await expect(answer).rejects.toMatchObject({
      status: 500,
      error: { detail: 'Database is down.' },
    });
  });
});
