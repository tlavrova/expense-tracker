import { Expense } from './expense.model';

/** Sample data until the API exists (stage 10 replaces it with HttpClient calls). */
export const MOCK_EXPENSES: Expense[] = [
  { id: 1, amount: 900, category: 'housing', description: 'Rent', date: '2026-10-01', frequency: 'monthly' },
  { id: 2, amount: 32.5, category: 'transport', description: 'Uber to airport', date: '2026-11-01' },
  { id: 3, amount: 12, category: 'food', description: 'Lunch', date: '2026-11-02' },
  { id: 4, amount: 18, category: 'transport', description: 'Taxi home', date: '2026-11-03' },
  { id: 5, amount: 14.99, category: 'entertainment', description: 'Streaming', date: '2026-11-03', frequency: 'monthly' },
];
