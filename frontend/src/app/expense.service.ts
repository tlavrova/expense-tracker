import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { Expense, NewExpense, Summary } from './expense.model';

/**
 * The only place that knows where expenses come from: the FastAPI backend (backend/api.py).
 *
 * Components only see these four methods, so they didn't change when the mock data was replaced
 * by HTTP calls (stage 10). Errors reach the caller as HttpErrorResponse; apiErrorMessage()
 * turns one into a sentence for the page.
 */
@Injectable({ providedIn: 'root' })
export class ExpenseService {
  private readonly http = inject(HttpClient);
  private readonly url = environment.apiUrl;

  list(): Observable<Expense[]> {
    return this.http.get<Expense[]>(`${this.url}/expenses`);
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
}
