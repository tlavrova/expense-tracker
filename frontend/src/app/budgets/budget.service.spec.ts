import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { BudgetService } from './budget.service';

describe('BudgetService (HTTP)', () => {
  const api = environment.apiUrl;

  function setup() {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    return { service: TestBed.inject(BudgetService), http: TestBed.inject(HttpTestingController) };
  }

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('asks GET /reports/month for one month', async () => {
    const { service, http } = setup();
    const answer = firstValueFrom(service.month('2026-11'));
    const request = http.expectOne(`${api}/reports/month?month=2026-11`);
    expect(request.request.method).toBe('GET');
    const report = { month: '2026-11', rows: [], totalSpent: 0, totalBudget: 0 };
    request.flush(report);
    expect(await answer).toEqual(report);
  });

  it('sets a budget with PUT and removes one with DELETE', async () => {
    const { service, http } = setup();
    const saved = firstValueFrom(service.set('eating out', 120));
    const put = http.expectOne(`${api}/budgets/eating%20out`); // spaces are escaped in the path
    expect(put.request.method).toBe('PUT');
    expect(put.request.body).toEqual({ amount: 120 });
    put.flush({ category: 'eating out', amount: 120 });
    expect(await saved).toEqual({ category: 'eating out', amount: 120 });

    const removed = firstValueFrom(service.remove('food'));
    const del = http.expectOne(`${api}/budgets/food`);
    expect(del.request.method).toBe('DELETE');
    del.flush(null, { status: 204, statusText: 'No Content' });
    await removed;
  });
});
