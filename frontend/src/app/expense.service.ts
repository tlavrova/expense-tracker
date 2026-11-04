import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../environments/environment';
import { Expense, ExpenseFilters, NewExpense, Summary } from './expense.model';

/**
 * The only place that knows where expenses come from: the FastAPI backend (backend/api.py).
 *
 * Errors reach the caller as HttpErrorResponse; apiErrorMessage() turns one into a sentence for
 * the page.
 */
@Injectable({ providedIn: 'root' })
export class ExpenseService {
  private readonly http = inject(HttpClient);
  private readonly url = environment.apiUrl;

  /** All expenses, or only those matching the filters; the API does the filtering. */
  list(filters: ExpenseFilters = {}): Observable<Expense[]> {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value) {
        params = params.set(key, value);
      }
    }
    return this.http.get<Expense[]>(`${this.url}/expenses`, { params });
  }

  add(expense: NewExpense): Observable<Expense> {
    return this.http.post<Expense>(`${this.url}/expenses`, expense);
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.url}/expenses/${id}`);
  }

  summary(): Observable<Summary> {
    return this.http.get<Summary>(`${this.url}/summary`);
  }

  /** Gemini's category for a description. Fails with 503 (and the reason) when AI isn't available. */
  suggestCategory(description: string): Observable<string> {
    return this.http
      .post<{ category: string }>(`${this.url}/suggest-category`, { description })
      .pipe(map((answer) => answer.category));
  }
}
