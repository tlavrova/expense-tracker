/** Matches Budget, MonthRow and MonthReport in backend/schemas.py. */

/** A category's monthly budget, the same every month. */
export interface Budget {
  category: string;
  amount: number;
}

/** One category in a month: what was spent, and its budget (null if it has none). */
export interface MonthRow {
  category: string;
  spent: number;
  budget: number | null;
}

/** GET /reports/month: every category with a budget or with spending that month. */
export interface MonthReport {
  /** YYYY-MM */
  month: string;
  rows: MonthRow[];
  totalSpent: number;
  totalBudget: number;
}
