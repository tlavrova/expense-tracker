import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ExpenseService } from '../expense.service';

@Component({
  imports: [DatePipe, DecimalPipe],
  selector: 'app-expense-list',
  styleUrl: './expense-list.css',
  templateUrl: './expense-list.html',
})
export class ExpenseList {
  private readonly expenseService = inject(ExpenseService);

  protected readonly expenses = toSignal(this.expenseService.list(), { initialValue: [] });
  protected readonly total = computed(() =>
    this.expenses().reduce((sum, expense) => sum + expense.amount, 0),
  );
}
