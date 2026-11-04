/** Matches the Python `Expense` / `RecurringExpense` in backend/models.py. */

export const FREQUENCIES = ['weekly', 'monthly', 'yearly'] as const;

/** The categories the AI may suggest (CATEGORIES in models.py); people can still type their own. */
export const CATEGORIES = ['food', 'transport', 'housing', 'entertainment', 'shopping', 'health', 'other'] as const;
export type Frequency = (typeof FREQUENCIES)[number];

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
