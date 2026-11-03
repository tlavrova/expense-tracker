import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { Expense, NewExpense, Summary } from './expense.model';
import { MOCK_EXPENSES } from './mock-expenses';

/**
 * The only place that knows where expenses come from.
 *
 * For now it serves mock data from memory. Stage 10 swaps the method bodies for HttpClient calls
 * to the FastAPI backend; the signatures (and so the components) stay the same.
 */
@Injectable({ providedIn: 'root' })
export class ExpenseService {
  private expenses: Expense[] = MOCK_EXPENSES.map((expense) => ({ ...expense }));
  private nextId = Math.max(0, ...this.expenses.map((expense) => expense.id ?? 0)) + 1;

  list(): Observable<Expense[]> {
    return of(this.expenses.map((expense) => ({ ...expense })));
  }

  add(expense: NewExpense): Observable<Expense> {
    const saved: Expense = { ...expense, id: this.nextId++ };
    this.expenses.push(saved);
    return of({ ...saved });
  }

  delete(id: number): Observable<void> {
    this.expenses = this.expenses.filter((expense) => expense.id !== id);
    return of(undefined);
  }

  summary(): Observable<Summary> {
    const totalsByCategory: Record<string, number> = {};
    for (const expense of this.expenses) {
      totalsByCategory[expense.category] = (totalsByCategory[expense.category] ?? 0) + expense.amount;
    }
    const total = this.expenses.reduce((sum, expense) => sum + expense.amount, 0);
    return of({ totalsByCategory, total });
  }
}
