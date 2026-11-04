import { Component, computed, input, output } from '@angular/core';
import { CATEGORIES, ExpenseFilters } from '../expense.model';

/** One filter the user changed; an empty value means "remove this filter". */
export interface FilterChange {
  name: keyof ExpenseFilters;
  value: string;
}

/**
 * The category, month and sort fields above the expense list.
 *
 * It only shows the filters it is given and reports changes; the list page decides what to do
 * with them (it keeps them in the page address).
 */
@Component({
  selector: 'app-expense-filter-bar',
  styleUrl: './expense-filter-bar.css',
  templateUrl: './expense-filter-bar.html',
})
export class ExpenseFilterBar {
  readonly filters = input.required<ExpenseFilters>();
  readonly changed = output<FilterChange>();
  readonly cleared = output<void>();

  protected readonly categories = CATEGORIES;
  protected readonly active = computed(() => {
    const filters = this.filters();
    return !!(filters.category || filters.month || filters.sort);
  });
}
