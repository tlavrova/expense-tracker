import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { Expense } from '../expense.model';
import { ExpenseService } from '../expense.service';
import { ExpenseList } from './expense-list';

async function render(expenses: Expense[]): Promise<HTMLElement> {
  await TestBed.configureTestingModule({
    imports: [ExpenseList],
    providers: [{ provide: ExpenseService, useValue: { list: () => of(expenses) } }],
  }).compileComponents();
  const fixture = TestBed.createComponent(ExpenseList);
  await fixture.whenStable();
  return fixture.nativeElement as HTMLElement;
}

describe('ExpenseList', () => {
  it('shows one row per expense and the total', async () => {
    const page = await render([
      { id: 1, amount: 900, category: 'housing', description: 'Rent', date: '2026-10-01', frequency: 'monthly' },
      { id: 2, amount: 12.5, category: 'food', description: 'Lunch', date: '2026-11-02' },
    ]);
    expect(page.querySelectorAll('tbody tr').length).toBe(2);
    expect(page.querySelector('tbody')?.textContent).toContain('Rent');
    expect(page.querySelector('.badge')?.textContent).toContain('monthly');
    expect(page.querySelector('.total')?.textContent?.trim()).toBe('912.50');
  });

  it('says so when there are no expenses', async () => {
    const page = await render([]);
    expect(page.querySelector('table')).toBeNull();
    expect(page.textContent).toContain('No expenses yet.');
  });
});
