import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Observable, of, throwError } from 'rxjs';
import { Expense } from '../expense.model';
import { ExpenseService } from '../expense.service';
import { ExpenseList } from './expense-list';

const EXPENSES: Expense[] = [
  {
    id: 1,
    amount: 900,
    category: 'housing',
    description: 'Rent',
    date: '2026-10-01',
    frequency: 'monthly',
  },
  { id: 2, amount: 12.5, category: 'food', description: 'Lunch', date: '2026-11-02' },
];

async function render(service: Partial<ExpenseService>) {
  await TestBed.configureTestingModule({
    imports: [ExpenseList],
    providers: [provideRouter([]), { provide: ExpenseService, useValue: service }],
  }).compileComponents();
  const fixture = TestBed.createComponent(ExpenseList);
  await fixture.whenStable();
  return { fixture, page: fixture.nativeElement as HTMLElement };
}

describe('ExpenseList', () => {
  afterEach(() => vi.restoreAllMocks());

  it('shows one row per expense and the total', async () => {
    const { page } = await render({ list: () => of(EXPENSES) });
    expect(page.querySelectorAll('tbody tr').length).toBe(2);
    expect(page.querySelector('tbody')?.textContent).toContain('Rent');
    expect(page.querySelector('.badge')?.textContent).toContain('monthly');
    expect(page.querySelector('.total')?.textContent?.trim()).toBe('912.50');
  });

  it('says so when there are no expenses', async () => {
    const { page } = await render({ list: () => of([]) });
    expect(page.querySelector('table')).toBeNull();
    expect(page.textContent).toContain('No expenses yet.');
  });

  it('shows "Loading…" until the API answers', async () => {
    const { page } = await render({ list: () => new Observable<Expense[]>() }); // never answers
    expect(page.textContent).toContain('Loading…');
  });

  it('explains when the API cannot be reached', async () => {
    const { page } = await render({
      list: () => throwError(() => new HttpErrorResponse({ status: 0 })),
    });
    expect(page.querySelector('[role=alert]')?.textContent).toContain("Can't reach the API");
    expect(page.textContent).not.toContain('Loading…');
  });

  it('deletes a row after confirming', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    const remove = vi.fn(() => of(undefined));
    const { fixture, page } = await render({ list: () => of(EXPENSES), delete: remove });
    page.querySelector<HTMLButtonElement>('button[aria-label="Delete Lunch"]')!.click();
    await fixture.whenStable();
    expect(remove).toHaveBeenCalledWith(2);
    expect(page.querySelectorAll('tbody tr').length).toBe(1);
    expect(page.querySelector('.total')?.textContent?.trim()).toBe('900.00');
  });

  it('keeps the row when the delete is cancelled', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    const remove = vi.fn(() => of(undefined));
    const { fixture, page } = await render({ list: () => of(EXPENSES), delete: remove });
    page.querySelector<HTMLButtonElement>('button[aria-label="Delete Lunch"]')!.click();
    await fixture.whenStable();
    expect(remove).not.toHaveBeenCalled();
    expect(page.querySelectorAll('tbody tr').length).toBe(2);
  });
});
