import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Budget, MonthReport } from './budget.model';

/** Budgets and the month report from the API (backend/routers/budgets.py and reports.py). */
@Injectable({ providedIn: 'root' })
export class BudgetService {
  private readonly http = inject(HttpClient);
  private readonly url = environment.apiUrl;

  /** Spent per category in one month (YYYY-MM), next to each budget. */
  month(month: string): Observable<MonthReport> {
    const params = new HttpParams().set('month', month);
    return this.http.get<MonthReport>(`${this.url}/reports/month`, { params });
  }

  /** Set or change a category's monthly budget; the API stores the category lowercase. */
  set(category: string, amount: number): Observable<Budget> {
    return this.http.put<Budget>(`${this.url}/budgets/${encodeURIComponent(category)}`, { amount });
  }

  remove(category: string): Observable<void> {
    return this.http.delete<void>(`${this.url}/budgets/${encodeURIComponent(category)}`);
  }
}
