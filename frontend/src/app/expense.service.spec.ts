import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';
import { environment } from '../environments/environment';
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
