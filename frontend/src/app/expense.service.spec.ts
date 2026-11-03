import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';
import { ExpenseService } from './expense.service';
import { MOCK_EXPENSES } from './mock-expenses';

describe('ExpenseService (mock data)', () => {
  let service: ExpenseService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ExpenseService);
  });

  it('lists the mock expenses', async () => {
    const expenses = await firstValueFrom(service.list());
    expect(expenses.length).toBe(MOCK_EXPENSES.length);
  });

  it('adds an expense with a new id', async () => {
    const saved = await firstValueFrom(
      service.add({ amount: 5, category: 'food', description: 'Coffee', date: '2026-11-03' }),
    );
    expect(saved.id).toBe(MOCK_EXPENSES.length + 1);
    expect((await firstValueFrom(service.list())).length).toBe(MOCK_EXPENSES.length + 1);
  });

  it('deletes an expense by id', async () => {
    await firstValueFrom(service.delete(1));
    const expenses = await firstValueFrom(service.list());
    expect(expenses.some((expense) => expense.id === 1)).toBe(false);
  });

  it('sums totals per category and overall', async () => {
    const summary = await firstValueFrom(service.summary());
    expect(summary.totalsByCategory['transport']).toBe(50.5);
    expect(summary.total).toBeCloseTo(977.49);
  });

  it('does not let callers change its data', async () => {
    const expenses = await firstValueFrom(service.list());
    expenses[0].amount = 1;
    expect((await firstValueFrom(service.list()))[0].amount).toBe(900);
  });
});
