import { DecimalPipe, PercentPipe } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { apiErrorMessage } from '../api-error';
import { Summary as SummaryData } from '../expense.model';
import { ExpenseService } from '../expense.service';

interface CategoryTotal {
  category: string;
  total: number;
  /** Share of the overall total, 0–1. */
  share: number;
}

@Component({
  imports: [DecimalPipe, PercentPipe, RouterLink],
  selector: 'app-summary',
  styleUrl: './summary.css',
  templateUrl: './summary.html',
})
export class Summary {
  private readonly expenseService = inject(ExpenseService);

  /** null while the answer from the API is on its way. */
  protected readonly summary = signal<SummaryData | null>(null);
  protected readonly error = signal('');

  /** Largest category first. */
  protected readonly rows = computed<CategoryTotal[]>(() => {
    const summary = this.summary();
    if (!summary) {
      return [];
    }
    return Object.entries(summary.totalsByCategory)
      .map(([category, total]) => ({
        category,
        total,
        share: summary.total ? total / summary.total : 0,
      }))
      .sort((a, b) => b.total - a.total || a.category.localeCompare(b.category));
  });

  constructor() {
    this.load();
  }

  protected load(): void {
    this.error.set('');
    this.expenseService.summary().subscribe({
      next: (summary) => this.summary.set(summary),
      error: (error: unknown) => this.error.set(apiErrorMessage(error)),
    });
  }
}
