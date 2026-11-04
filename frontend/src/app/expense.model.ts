/** Matches the Python `Expense` / `RecurringExpense` in backend/models.py. */

export const FREQUENCIES = ['weekly', 'monthly', 'yearly'] as const;
export type Frequency = (typeof FREQUENCIES)[number];

/** The categories the AI may suggest (CATEGORIES in models.py); people can still type their own. */
export const CATEGORIES = [
  'food',
  'transport',
  'housing',
  'entertainment',
  'shopping',
  'health',
  'other',
] as const;

export interface Expense {
  /** Set by the backend when it saves the expense. */
  id?: number;
  amount: number;
  category: string;
  description: string;
  /** YYYY-MM-DD */
  date: string;
  /** Only for recurring expenses. */
  frequency?: Frequency;
}

export type NewExpense = Omit<Expense, 'id'>;

export interface Summary {
  totalsByCategory: Record<string, number>;
  total: number;
}

export const SORT_KEYS = ['amount', 'date'] as const;
export type SortKey = (typeof SORT_KEYS)[number];

/** The query parameters of GET /expenses; anything left out means "all" / "as entered". */
export interface ExpenseFilters {
  category?: string;
  /** YYYY-MM */
  month?: string;
  sort?: SortKey;
}
