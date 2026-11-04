import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, ParamMap, Router, RouterLink } from '@angular/router';
import { BehaviorSubject, EMPTY, catchError, combineLatest, map, switchMap, tap } from 'rxjs';
import { apiErrorMessage } from '../api-error';
import { CATEGORIES, Expense, ExpenseFilters, SORT_KEYS, SortKey } from '../expense.model';
import { ExpenseService } from '../expense.service';

/** The filters from the page address (?category=food&month=2026-11&sort=amount); bad values are ignored. */
export function filtersFrom(params: ParamMap): ExpenseFilters {
  const filters: ExpenseFilters = {};
  const category = params.get('category')?.trim().toLowerCase();
  const month = params.get('month') ?? '';
  const sort = params.get('sort') ?? '';
  if (category) {
    filters.category = category;
  }
  if (/^\d{4}-(0[1-9]|1[0-2])$/.test(month)) {
    filters.month = month;
  }
  if ((SORT_KEYS as readonly string[]).includes(sort)) {
    filters.sort = sort as SortKey;
  }
  return filters;
}

@Component({
  imports: [DatePipe, DecimalPipe, RouterLink],
  selector: 'app-expense-list',
  styleUrl: './expense-list.css',
  templateUrl: './expense-list.html',
})
export class ExpenseList {
  private readonly expenseService = inject(ExpenseService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly reload$ = new BehaviorSubject<void>(undefined);

  protected readonly categories = CATEGORIES;
  protected readonly filters = signal<ExpenseFilters>({});
  /** Category or month narrows the list; sorting alone doesn't. */
  protected readonly filtered = computed(() => !!(this.filters().category || this.filters().month));

  /** null while the answer from the API is on its way. */
  protected readonly expenses = signal<Expense[] | null>(null);
  protected readonly error = signal('');
  /** The id being deleted, so its button can show that it's busy. */
  protected readonly deleting = signal<number | null>(null);

  protected readonly total = computed(() =>
    (this.expenses() ?? []).reduce((sum, expense) => sum + expense.amount, 0),
  );

  constructor() {
    // Ask the API again whenever the filters in the address change (or "Try again" is clicked).
    // switchMap drops an older answer that arrives after a newer request was sent.
    combineLatest([this.route.queryParamMap, this.reload$])
      .pipe(
        map(([params]) => filtersFrom(params)),
        tap((filters) => {
          this.filters.set(filters);
          this.expenses.set(null);
          this.error.set('');
        }),
        switchMap((filters) =>
          this.expenseService.list(filters).pipe(
            catchError((error: unknown) => {
              this.error.set(apiErrorMessage(error));
              return EMPTY;
            }),
          ),
        ),
        takeUntilDestroyed(),
      )
      .subscribe((expenses) => this.expenses.set(expenses));
  }

  /** Put one filter in the page address (empty removes it); the list follows from there. */
  protected setFilter(name: keyof ExpenseFilters, value: string): void {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { [name]: value.trim() || null },
      queryParamsHandling: 'merge',
      replaceUrl: true, // filtering shouldn't fill the Back button's history
    });
  }

  protected clearFilters(): void {
    this.router.navigate([], { relativeTo: this.route, queryParams: {}, replaceUrl: true });
  }

  protected load(): void {
    this.reload$.next();
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
