import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { Observable, of, throwError } from 'rxjs';
import { shiftMonth, thisMonth } from '../../core/dates';
import { MonthReport } from '../budget.model';
import { BudgetService } from '../budget.service';
import { BudgetsPage } from './budgets-page';

const NOVEMBER: MonthReport = {
  month: '2026-11',
  rows: [
    { category: 'food', spent: 257.5, budget: 300 },
    { category: 'shopping', spent: 120, budget: 100 },
    { category: 'transport', spent: 32.5, budget: null },
  ],
  totalSpent: 410,
  totalBudget: 400,
};

interface Fake {
  month: (month: string) => Observable<MonthReport>;
  set: (category: string, amount: number) => Observable<unknown>;
  remove: (category: string) => Observable<void>;
}

async function open(url: string, service: Partial<Fake> = {}) {
  const fake: Fake = {
    month: vi.fn(() => of(NOVEMBER)),
    set: vi.fn(() => of({})),
    remove: vi.fn(() => of(undefined)),
    ...service,
  };
  TestBed.configureTestingModule({
    providers: [
      provideRouter([{ path: 'budgets', component: BudgetsPage }], withComponentInputBinding()),
      { provide: BudgetService, useValue: fake },
    ],
  });
  const harness = await RouterTestingHarness.create(url);
  const page = () => harness.routeNativeElement as HTMLElement;
  const rows = () =>
    [...page().querySelectorAll('tbody tr')].map((row) =>
      [...row.querySelectorAll('th, td')].map((cell) =>
        cell.textContent?.trim().replace(/\s+/g, ' '),
      ),
    );
  const click = async (text: string, within: ParentNode = page()) => {
    const button = [...within.querySelectorAll('button')].find(
      (b) => b.textContent?.trim() === text,
    )!;
    button.click();
    await harness.fixture.whenStable();
  };
  const typeAmount = (value: string) => {
    const field = page().querySelector<HTMLInputElement>('input[aria-label="Monthly budget"]')!;
    field.value = value;
    field.dispatchEvent(new Event('input'));
  };
  return { harness, page, rows, click, typeAmount, fake };
}

describe('BudgetsPage', () => {
  afterEach(() => vi.restoreAllMocks());

  it('shows each budget with what was spent and what is left or over', async () => {
    const { page, rows, fake } = await open('/budgets?month=2026-11');
    expect(fake.month).toHaveBeenCalledWith('2026-11');
    expect(page().querySelector('.month strong')?.textContent).toBe('November 2026');
    expect(rows().slice(0, 2)).toEqual([
      ['food', '257.50', '300.00', '42.50 left', 'Change Remove'],
      ['shopping', '120.00', '100.00', 'over by 20.00', 'Change Remove'],
    ]);
    expect(page().querySelectorAll('tr.over').length).toBe(1);
    const footer = [...page().querySelectorAll('tfoot th, tfoot td')].map((cell) =>
      cell.textContent?.trim(),
    );
    expect(footer.slice(0, 3)).toEqual(['Total', '410.00', '400.00']);
  });

  it('lists spending without a budget, with "Set budget"', async () => {
    const { page } = await open('/budgets?month=2026-11');
    const item = page().querySelector('.unbudgeted li');
    expect(item?.textContent).toContain('transport: 32.50');
    expect(item?.querySelector('button')?.textContent?.trim()).toBe('Set budget');
  });

  it('starts on the current month and moves with ‹ and ›', async () => {
    const { harness, page, fake } = await open('/budgets');
    expect(fake.month).toHaveBeenCalledWith(thisMonth());
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigate');
    page().querySelector<HTMLButtonElement>('button[aria-label="Previous month"]')!.click();
    await harness.fixture.whenStable();
    expect(navigate).toHaveBeenCalledWith([], {
      queryParams: { month: shiftMonth(thisMonth(), -1) },
    });
  });

  it('changes a budget in place and loads the month again', async () => {
    const { page, click, typeAmount, fake } = await open('/budgets?month=2026-11');
    await click('Change', page().querySelector('tbody tr')!);
    const field = page().querySelector<HTMLInputElement>('input[aria-label="Monthly budget"]')!;
    expect(field.value).toBe('300');
    typeAmount('350');
    await click('Save');
    expect(fake.set).toHaveBeenCalledWith('food', 350);
    expect(fake.month).toHaveBeenCalledTimes(2);
  });

  it('adds a budget for a new category', async () => {
    const { page, click, typeAmount, fake, harness } = await open('/budgets?month=2026-11');
    await click('+ Add a budget');
    const category = page().querySelector<HTMLInputElement>('input[aria-label="Category"]')!;
    category.value = 'Health';
    category.dispatchEvent(new Event('input'));
    typeAmount('50');
    await click('Save');
    await harness.fixture.whenStable();
    expect(fake.set).toHaveBeenCalledWith('Health', 50); // the API stores it lowercase
  });

  it('needs an amount above zero before saving', async () => {
    const { page, click, typeAmount, fake } = await open('/budgets?month=2026-11');
    await click('Set budget');
    typeAmount('0');
    await click('Save');
    expect(fake.set).not.toHaveBeenCalled();
    expect(page().textContent).toContain('Please enter an amount greater than zero.');
  });

  it('removes a budget after confirming', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    const { page, click, fake } = await open('/budgets?month=2026-11');
    await click('Remove', page().querySelector('tbody tr')!);
    expect(fake.remove).toHaveBeenCalledWith('food');
  });

  it("shows the API's message when the month can't be loaded", async () => {
    const { page } = await open('/budgets?month=2026-11', {
      month: () => throwError(() => new HttpErrorResponse({ status: 0 })),
    });
    expect(page().querySelector('[role=alert]')?.textContent).toContain("Can't reach the API");
  });
});
