import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { convertToParamMap, provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { Observable, of, throwError } from 'rxjs';
import { Expense, ExpenseFilters } from '../expense.model';
import { ExpenseService } from '../expense.service';
import { ExpenseList, filtersFrom } from './expense-list';

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

/** Open the list page at a URL (for example "/expenses?category=food") with a fake service. */
async function open(url: string, service: Partial<ExpenseService>) {
  TestBed.configureTestingModule({
    providers: [
      provideRouter([{ path: 'expenses', component: ExpenseList }]),
      { provide: ExpenseService, useValue: service },
    ],
  });
  const harness = await RouterTestingHarness.create(url);
  const page = harness.routeNativeElement as HTMLElement;
  return { harness, page };
}

describe('ExpenseList', () => {
  afterEach(() => vi.restoreAllMocks());

  it('shows one row per expense and the total', async () => {
    const { page } = await open('/expenses', { list: () => of(EXPENSES) });
    expect(page.querySelectorAll('tbody tr').length).toBe(2);
    expect(page.querySelector('tbody')?.textContent).toContain('Rent');
    expect(page.querySelector('.badge')?.textContent).toContain('monthly');
    expect(page.querySelector('.total')?.textContent?.trim()).toBe('912.50');
    expect(page.querySelector('tfoot th')?.textContent).toContain('Total spent');
  });

  it('says so when there are no expenses', async () => {
    const { page } = await open('/expenses', { list: () => of([]) });
    expect(page.querySelector('table')).toBeNull();
    expect(page.textContent).toContain('No expenses yet.');
  });

  it('shows "Loading…" until the API answers', async () => {
    const { page } = await open('/expenses', { list: () => new Observable<Expense[]>() });
    expect(page.textContent).toContain('Loading…');
  });

  it('explains when the API cannot be reached', async () => {
    const { page } = await open('/expenses', {
      list: () => throwError(() => new HttpErrorResponse({ status: 0 })),
    });
    expect(page.querySelector('[role=alert]')?.textContent).toContain("Can't reach the API");
    expect(page.textContent).not.toContain('Loading…');
  });

  it('deletes a row after confirming', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    const remove = vi.fn(() => of(undefined));
    const { harness, page } = await open('/expenses', { list: () => of(EXPENSES), delete: remove });
    page.querySelector<HTMLButtonElement>('button[aria-label="Delete Lunch"]')!.click();
    await harness.fixture.whenStable();
    expect(remove).toHaveBeenCalledWith(2);
    expect(page.querySelectorAll('tbody tr').length).toBe(1);
    expect(page.querySelector('.total')?.textContent?.trim()).toBe('900.00');
  });

  it('keeps the row when the delete is cancelled', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    const remove = vi.fn(() => of(undefined));
    const { harness, page } = await open('/expenses', { list: () => of(EXPENSES), delete: remove });
    page.querySelector<HTMLButtonElement>('button[aria-label="Delete Lunch"]')!.click();
    await harness.fixture.whenStable();
    expect(remove).not.toHaveBeenCalled();
    expect(page.querySelectorAll('tbody tr').length).toBe(2);
  });

  describe('filters', () => {
    it('asks the API with the filters from the address and fills in the inputs', async () => {
      const list = vi.fn((_: ExpenseFilters) => of([EXPENSES[1]]));
      const { page } = await open('/expenses?category=Food&month=2026-11&sort=amount', { list });
      expect(list).toHaveBeenLastCalledWith({ category: 'food', month: '2026-11', sort: 'amount' });
      expect(page.querySelector<HTMLInputElement>('input[name=category]')!.value).toBe('food');
      expect(page.querySelector<HTMLInputElement>('input[name=month]')!.value).toBe('2026-11');
      expect(page.querySelector<HTMLSelectElement>('select[name=sort]')!.value).toBe('amount');
      expect(page.querySelector('tfoot th')?.textContent).toContain('Total shown');
    });

    it('puts a chosen filter in the address and loads again', async () => {
      const list = vi.fn((_: ExpenseFilters) => of(EXPENSES));
      const { harness, page } = await open('/expenses?sort=date', { list });
      const month = page.querySelector<HTMLInputElement>('input[name=month]')!;
      month.value = '2026-10';
      month.dispatchEvent(new Event('change'));
      await harness.fixture.whenStable();
      expect(list).toHaveBeenLastCalledWith({ month: '2026-10', sort: 'date' });
    });

    it('offers "Show all" when nothing matches, which clears the filters', async () => {
      const list = vi.fn((filters: ExpenseFilters) => of(filters.category ? [] : EXPENSES));
      const { harness, page } = await open('/expenses?category=travel', { list });
      expect(page.textContent).toContain('No expenses match these filters.');
      [...page.querySelectorAll('button')]
        .find((button) => button.textContent?.includes('Show all'))!
        .click();
      await harness.fixture.whenStable();
      expect(list).toHaveBeenLastCalledWith({});
      expect(page.querySelectorAll('tbody tr').length).toBe(2);
    });
  });
});

describe('filtersFrom()', () => {
  it('keeps good values and drops bad ones', () => {
    expect(
      filtersFrom(convertToParamMap({ category: ' Food ', month: '2026-11', sort: 'date' })),
    ).toEqual({
      category: 'food',
      month: '2026-11',
      sort: 'date',
    });
    expect(
      filtersFrom(convertToParamMap({ category: ' ', month: '2026-13', sort: 'name' })),
    ).toEqual({});
  });
});
