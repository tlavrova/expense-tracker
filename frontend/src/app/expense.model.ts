/** Matches the Python `Expense` / `RecurringExpense` in backend/models.py. */

export const FREQUENCIES = ['weekly', 'monthly', 'yearly'] as const;
export type Frequency = (typeof FREQUENCIES)[number];

export interface Expense {
  /** Set by the backend once saved (stage 8a). */
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
