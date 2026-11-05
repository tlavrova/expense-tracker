import { DatePipe, DecimalPipe, NgTemplateOutlet } from '@angular/common';
import { Component, computed, effect, inject, input, signal, untracked } from '@angular/core';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { apiErrorMessage } from '../../core/api-error';
import { isMonth, shiftMonth, thisMonth } from '../../core/dates';
import { CATEGORIES } from '../../expenses/expense.model';
import { MonthReport } from '../budget.model';
import { BudgetService } from '../budget.service';

/** A budgeted category in the shown month, with what's left (negative: over budget). */
interface BudgetRow {
  category: string;
  spent: number;
  budget: number;
  left: number;
  /** Share of the budget used, 0–1 (capped at 1 for the bar). */
  used: number;
}

/**
 * The budgets page (/budgets?month=2026-11): each budgeted category's spending in one month, set
 * or change budgets in place, and the categories with spending but no budget yet.
 *
 * The month is in the address, like the list's filters, so refreshing or sharing keeps it.
 */
@Component({
  imports: [DatePipe, DecimalPipe, NgTemplateOutlet, ReactiveFormsModule, RouterLink],
  selector: 'app-budgets-page',
  styleUrl: './budgets-page.css',
  templateUrl: './budgets-page.html',
})
export class BudgetsPage {
  private readonly budgets = inject(BudgetService);
  private readonly router = inject(Router);

  protected readonly categories = CATEGORIES;

  /** From the address (?month=2026-11); anything else shows the current month. */
  readonly month = input<string>();
  protected readonly thisMonth = thisMonth();
  protected readonly shown = computed(() => {
    const month = this.month();
    return isMonth(month) ? month : this.thisMonth;
  });
  /** The first of the shown month, for the heading (a local date, so no time-zone shift). */
  protected readonly shownDate = computed(() => {
    const [year, month] = this.shown().split('-').map(Number);
    return new Date(year, month - 1, 1);
  });

  /** null while loading. */
  protected readonly report = signal<MonthReport | null>(null);
  protected readonly error = signal('');

  protected readonly budgeted = computed<BudgetRow[]>(() =>
    (this.report()?.rows ?? [])
      .filter((row) => row.budget !== null)
      .map((row) => ({
        category: row.category,
        spent: row.spent,
        budget: row.budget!,
        left: row.budget! - row.spent,
        used: Math.min(row.spent / row.budget!, 1),
      })),
  );
  protected readonly unbudgeted = computed(() =>
    (this.report()?.rows ?? []).filter((row) => row.budget === null),
  );

  /** The category whose amount field is open; '' is the "new budget" row; null: none. */
  protected readonly editing = signal<string | null>(null);
  protected readonly amount = new FormControl<number | null>(null, [
    Validators.required,
    Validators.min(0.01),
  ]);
  protected readonly newCategory = new FormControl('', { nonNullable: true });
  protected readonly saving = signal(false);
  protected readonly saveError = signal('');

  constructor() {
    // Load whenever the month in the address changes (and once at the start).
    effect(() => {
      const month = this.shown();
      untracked(() => this.load(month));
    });
  }

  protected load(month = this.shown()): void {
    this.error.set('');
    this.report.set(null);
    this.budgets.month(month).subscribe({
      next: (report) => this.report.set(report),
      error: (error: unknown) => this.error.set(apiErrorMessage(error)),
    });
  }

  protected go(by: number): void {
    this.router.navigate([], { queryParams: { month: shiftMonth(this.shown(), by) } });
  }

  /** Open the amount field for a category ('' for a new one), filled with its budget if any. */
  protected edit(category: string, budget: number | null = null): void {
    this.editing.set(category);
    this.amount.reset(budget);
    this.newCategory.reset(category);
    this.saveError.set('');
  }

  protected cancel(): void {
    this.editing.set(null);
    this.saveError.set('');
  }

  protected save(): void {
    const category = (this.editing() || this.newCategory.value).trim();
    if (this.amount.invalid || !category) {
      this.amount.markAsTouched();
      this.saveError.set(category ? '' : 'Please choose or type a category.');
      return;
    }
    this.saving.set(true);
    this.saveError.set('');
    this.budgets.set(category, this.amount.value!).subscribe({
      next: () => {
        this.saving.set(false);
        this.editing.set(null);
        this.load();
      },
      error: (error: unknown) => {
        this.saving.set(false);
        this.saveError.set(apiErrorMessage(error));
      },
    });
  }

  protected remove(category: string): void {
    if (!confirm(`Remove the budget for ${category}?`)) {
      return;
    }
    this.budgets.remove(category).subscribe({
      next: () => this.load(),
      error: (error: unknown) => this.error.set(apiErrorMessage(error)),
    });
  }
}
