import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { apiErrorMessage } from '../api-error';
import { Expense } from '../expense.model';
import { ExpenseService } from '../expense.service';

@Component({
  imports: [DatePipe, DecimalPipe, RouterLink],
  selector: 'app-expense-list',
  styleUrl: './expense-list.css',
  templateUrl: './expense-list.html',
})
export class ExpenseList {
  private readonly expenseService = inject(ExpenseService);

  /** null while the first answer from the API is on its way. */
  protected readonly expenses = signal<Expense[] | null>(null);
  protected readonly error = signal('');
  /** The id being deleted, so its button can show that it's busy. */
  protected readonly deleting = signal<number | null>(null);

  protected readonly total = computed(() =>
    (this.expenses() ?? []).reduce((sum, expense) => sum + expense.amount, 0),
  );

  constructor() {
    this.load();
  }

  protected load(): void {
    this.error.set('');
    this.expenseService.list().subscribe({
      next: (expenses) => this.expenses.set(expenses),
      error: (error: unknown) => this.error.set(apiErrorMessage(error)),
    });
  }

  protected delete(expense: Expense): void {
    if (expense.id === undefined || !confirm(`Delete "${expense.description}"?`)) {
      return;
    }
    const id = expense.id;
    this.deleting.set(id);
    this.error.set('');
    this.expenseService.delete(id).subscribe({
      next: () => {
        this.expenses.update((expenses) => (expenses ?? []).filter((item) => item.id !== id));
        this.deleting.set(null);
      },
      error: (error: unknown) => {
        this.error.set(apiErrorMessage(error));
        this.deleting.set(null);
      },
    });
  }
}
