import { Signal, computed, effect, signal, untracked } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormControl } from '@angular/forms';
import { Observable } from 'rxjs';
import { isMonth } from '../../core/dates';
import { MonthReport } from '../../budgets/budget.model';
import { Expense } from '../expense.model';

/** What the form shows under the fields when the category has a budget (wording as on Budgets). */
export interface BudgetLine {
  category: string;
  /** Spent in that category and month, with this expense. */
  total: number;
  budget: number;
  /** Negative: over budget. */
  left: number;
}

/**
 * The budget hint for the add and edit forms: how much of the category's budget the month has
 * used, with the expense being typed. Only a hint: it never blocks saving.
 *
 * Each month's report (GET /reports/month) is loaded once and reused while the user types. When
 * editing, the expense's saved amount is taken out first, so it isn't counted twice.
 *
 * Create it in a field initializer (toSignal and effect need the component's injection context).
 */
export class BudgetHint {
  private readonly category: Signal<string>;
  private readonly amount: Signal<number | null>;
  private readonly date: Signal<string>;
  /** The expense as saved, on the edit page. */
  private readonly saved = signal<Expense | null>(null);
  private readonly reports = signal<Record<string, MonthReport>>({});
  private readonly requested = new Set<string>();

  readonly line = computed<BudgetLine | null>(() => {
    const category = this.category().trim().toLowerCase();
    const amount = this.amount();
    const month = this.date().slice(0, 7);
    const budget = this.reports()[month]?.rows.find((row) => row.category === category);
    if (!budget || budget.budget === null || !amount || amount <= 0) {
      return null;
    }
    const saved = this.saved();
    const alreadyCounted =
      saved && saved.category === category && saved.date.slice(0, 7) === month ? saved.amount : 0;
    const total = budget.spent - alreadyCounted + amount;
    return { category, total, budget: budget.budget, left: budget.budget - total };
  });

  constructor(
    controls: {
      category: FormControl<string>;
      amount: FormControl<number | null>;
      date: FormControl<string>;
    },
    private readonly load: (month: string) => Observable<MonthReport>,
  ) {
    this.category = toSignal(controls.category.valueChanges, {
      initialValue: controls.category.value,
    });
    this.amount = toSignal(controls.amount.valueChanges, { initialValue: controls.amount.value });
    this.date = toSignal(controls.date.valueChanges, { initialValue: controls.date.value });
    // Load a month's report the first time its date is chosen.
    effect(() => {
      const month = this.date().slice(0, 7);
      untracked(() => this.fetch(month));
    });
  }

  /** The edit page: the expense as saved, so its amount isn't counted twice. */
  editing(expense: Expense): void {
    this.saved.set(expense);
  }

  private fetch(month: string): void {
    if (!isMonth(month) || this.requested.has(month)) {
      return;
    }
    this.requested.add(month);
    this.load(month).subscribe({
      next: (report) => this.reports.update((reports) => ({ ...reports, [month]: report })),
      error: () => undefined, // only a hint: without the report there is simply no line
    });
  }
}
