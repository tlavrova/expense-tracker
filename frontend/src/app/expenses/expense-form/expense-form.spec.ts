import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { Subject, of, throwError } from 'rxjs';
import { ExpenseService } from '../expense.service';
import { ExpenseForm, today } from './expense-form';

async function render(
  add: ExpenseService['add'],
  suggestCategory: ExpenseService['suggestCategory'] = vi.fn(),
  /** The edit page: the id from the address, and the fake get/update. */
  edit?: { id: string } & Partial<Pick<ExpenseService, 'get' | 'update'>>,
) {
  const service = { add, suggestCategory, get: edit?.get, update: edit?.update };
  await TestBed.configureTestingModule({
    imports: [ExpenseForm],
    providers: [provideRouter([]), { provide: ExpenseService, useValue: service }],
  }).compileComponents();
  const fixture = TestBed.createComponent(ExpenseForm);
  if (edit) {
    fixture.componentRef.setInput('id', edit.id); // what the router does for /expenses/:id/edit
  }
  await fixture.whenStable();
  const page = fixture.nativeElement as HTMLElement;
  const navigate = vi.spyOn(TestBed.inject(Router), 'navigate').mockResolvedValue(true);

  const type = (name: string, value: string) => {
    const field = page.querySelector<HTMLInputElement | HTMLSelectElement>(
      `[formControlName=${name}]`,
    )!;
    field.value = value;
    field.dispatchEvent(new Event(field instanceof HTMLSelectElement ? 'change' : 'input'));
  };
  const submit = async () => {
    page.querySelector('form')!.dispatchEvent(new Event('submit'));
    await fixture.whenStable();
  };
  /** Leave a field, as tabbing to the next one does. */
  const leave = async (name: string) => {
    page.querySelector(`[formControlName=${name}]`)!.dispatchEvent(new Event('blur'));
    await fixture.whenStable();
  };
  const value = (name: string) =>
    page.querySelector<HTMLInputElement>(`[formControlName=${name}]`)!.value;
  const hint = () => page.querySelector('.hint')?.textContent?.trim() ?? '';
  return { page, navigate, type, submit, leave, value, hint, fixture };
}

describe('ExpenseForm', () => {
  it("starts with today's date", async () => {
    const { page } = await render(vi.fn());
    expect(page.querySelector<HTMLInputElement>('[formControlName=date]')!.value).toBe(today());
  });

  it('shows what is missing instead of saving an empty form', async () => {
    const add = vi.fn();
    const { page, submit } = await render(add);
    await submit();
    expect(add).not.toHaveBeenCalled();
    const errors = [...page.querySelectorAll('.field-error')].map((error) =>
      error.textContent?.trim(),
    );
    expect(errors).toEqual([
      'Please describe the expense.',
      'Please enter an amount, for example 12.50.',
      'Please choose or type a category.',
    ]);
  });

  it('rejects a zero amount and a description of only spaces', async () => {
    const add = vi.fn();
    const { page, type, submit } = await render(add);
    type('description', '   ');
    type('amount', '0');
    type('category', 'food');
    await submit();
    expect(add).not.toHaveBeenCalled();
    expect(page.textContent).toContain('The amount must be greater than zero.');
    expect(page.textContent).toContain('Please describe the expense.');
  });

  it('saves a recurring expense and goes back to the list', async () => {
    const add = vi.fn(() =>
      of({ id: 1, amount: 900, category: 'housing', description: 'Rent', date: '2026-11-01' }),
    );
    const { type, submit, navigate } = await render(add);
    type('description', ' Rent ');
    type('amount', '900');
    type('category', 'Housing');
    type('date', '2026-11-01');
    type('frequency', 'monthly');
    await submit();
    expect(add).toHaveBeenCalledWith({
      amount: 900,
      category: 'housing',
      description: 'Rent',
      date: '2026-11-01',
      frequency: 'monthly',
    });
    expect(navigate).toHaveBeenCalledWith(['/expenses']);
  });

  it('leaves frequency out for a one-off expense', async () => {
    const add = vi.fn(() =>
      of({ id: 2, amount: 3, category: 'food', description: 'Coffee', date: today() }),
    );
    const { type, submit } = await render(add);
    type('description', 'Coffee');
    type('amount', '3');
    type('category', 'food');
    await submit();
    expect(add).toHaveBeenCalledWith({
      amount: 3,
      category: 'food',
      description: 'Coffee',
      date: today(),
    });
  });

  it("shows the API's message when it rejects the expense", async () => {
    const add = vi.fn(() =>
      throwError(
        () =>
          new HttpErrorResponse({
            status: 422,
            error: { detail: 'date: Input should be a valid date' },
          }),
      ),
    );
    const { page, type, submit, navigate } = await render(add);
    type('description', 'Coffee');
    type('amount', '3');
    type('category', 'food');
    await submit();
    expect(page.querySelector('[role=alert]')?.textContent).toContain(
      'date: Input should be a valid date',
    );
    expect(navigate).not.toHaveBeenCalled();
    expect(page.querySelector<HTMLButtonElement>('button[type=submit]')!.disabled).toBe(false);
  });
});

/** render() with an add() that saves, for tests that go all the way to saving. */
async function renderWithAdd(suggestCategory: ExpenseService['suggestCategory']) {
  const add = vi.fn(() =>
    of({ id: 1, amount: 32.5, category: 'transport', description: 'Uber', date: today() }),
  );
  return { ...(await render(add, suggestCategory)), add };
}

describe('ExpenseForm: editing', () => {
  const RENT = {
    id: 7,
    amount: 900,
    category: 'housing',
    description: 'Rent',
    date: '2026-10-01',
    frequency: 'monthly' as const,
  };

  it('loads the expense into the form', async () => {
    const get = vi.fn(() => of(RENT));
    const { page, value } = await render(vi.fn(), vi.fn(), { id: '7', get });
    expect(get).toHaveBeenCalledWith(7);
    expect(page.querySelector('h1')?.textContent).toBe('Edit expense');
    expect(value('description')).toBe('Rent');
    expect(value('amount')).toBe('900');
    expect(value('category')).toBe('housing');
    expect(value('date')).toBe('2026-10-01');
    expect(value('frequency')).toBe('monthly');
    expect(page.querySelector('button[type=submit]')?.textContent?.trim()).toBe('Save changes');
    expect(page.querySelector('a[href="/expenses"]')?.textContent).toBe('Cancel');
  });

  it('saves the changes with update, not add, and goes back to the list', async () => {
    const add = vi.fn();
    const update = vi.fn(() => of({ ...RENT, amount: 950 }));
    const { type, submit, navigate } = await render(add, vi.fn(), {
      id: '7',
      get: () => of(RENT),
      update,
    });
    type('amount', '950');
    type('frequency', '');
    await submit();
    expect(add).not.toHaveBeenCalled();
    expect(update).toHaveBeenCalledWith(7, {
      amount: 950,
      category: 'housing',
      description: 'Rent',
      date: '2026-10-01',
    }); // no frequency: it becomes a one-off
    expect(navigate).toHaveBeenCalledWith(['/expenses']);
  });

  it("doesn't ask the AI when leaving the description: the category is already there", async () => {
    const suggestCategory = vi.fn();
    const { type, leave, hint } = await render(vi.fn(), suggestCategory, {
      id: '7',
      get: () => of(RENT),
    });
    await leave('description');
    type('description', 'Rent for November');
    await leave('description');
    expect(suggestCategory).not.toHaveBeenCalled();
    expect(hint()).toContain('Pick one or type your own');
  });

  it("shows the API's message when the expense can't be loaded", async () => {
    const get = vi.fn(() =>
      throwError(
        () => new HttpErrorResponse({ status: 404, error: { detail: 'No expense with id 7.' } }),
      ),
    );
    const { page } = await render(vi.fn(), vi.fn(), { id: '7', get });
    expect(page.querySelector('[role=alert]')?.textContent).toContain('No expense with id 7.');
    expect(page.querySelector('form')).toBeNull();
    expect(page.querySelector('a[href="/expenses"]')?.textContent).toBe('Back to the list');
  });
});

describe('today()', () => {
  it('uses the local date, padded', () => {
    expect(today(new Date(2026, 0, 5, 23, 30))).toBe('2026-01-05');
  });
});

describe('ExpenseForm: AI category suggestion', () => {
  it('asks when the description is left with no category, and fills in the answer', async () => {
    const suggest = vi.fn(() => of('transport'));
    const { type, leave, value, hint } = await render(vi.fn(), suggest);
    type('description', ' Uber to airport ');
    await leave('description');
    expect(suggest).toHaveBeenCalledWith('Uber to airport');
    expect(value('category')).toBe('transport');
    expect(hint()).toContain('Suggested by AI');
  });

  it('does not ask when a category is already there', async () => {
    const suggest = vi.fn(() => of('transport'));
    const { type, leave, value } = await render(vi.fn(), suggest);
    type('category', 'travel');
    type('description', 'Uber to airport');
    await leave('description');
    expect(suggest).not.toHaveBeenCalled();
    expect(value('category')).toBe('travel');
  });

  it('asks only once per description (free-tier limit)', async () => {
    const suggest = vi.fn(() => of('transport'));
    const { type, leave } = await render(vi.fn(), suggest);
    type('description', 'Uber to airport');
    await leave('description');
    type('category', '');
    await leave('description');
    expect(suggest).toHaveBeenCalledTimes(1);
  });

  it('shows "Asking Gemini…" and keeps a category typed meanwhile', async () => {
    const answer = new Subject<string>();
    const { type, leave, value, hint, fixture } = await render(vi.fn(), () => answer);
    type('description', 'Uber to airport');
    await leave('description');
    expect(hint()).toContain('Asking Gemini');
    type('category', 'travel'); // the user decides first
    answer.next('transport'); // a late answer is ignored
    await fixture.whenStable();
    expect(value('category')).toBe('travel');
    expect(hint()).not.toContain('Suggested by AI');
  });

  it('lets the user override the suggestion and saves what they typed', async () => {
    const add = vi.fn(() =>
      of({ id: 1, amount: 32.5, category: 'travel', description: 'Uber', date: today() }),
    );
    const { type, leave, hint, submit } = await render(add, () => of('transport'));
    type('description', 'Uber');
    await leave('description');
    type('category', 'travel');
    type('amount', '32.5');
    await submit();
    expect(hint()).not.toContain('Suggested by AI');
    expect(add).toHaveBeenCalledWith(expect.objectContaining({ category: 'travel' }));
  });

  it('falls back to picking by hand when AI is not available', async () => {
    const unavailable = () =>
      throwError(
        () =>
          new HttpErrorResponse({ status: 503, error: { detail: 'GEMINI_API_KEY is not set.' } }),
      );
    const { type, leave, value, hint, submit, page } = await render(vi.fn(), unavailable);
    type('description', 'Uber');
    await leave('description');
    expect(hint()).toBe('No AI suggestion: GEMINI_API_KEY is not set. Please pick a category.');
    expect(value('category')).toBe('');
    await submit();
    expect(page.textContent).toContain('Please choose or type a category.');
  });

  it('says when the AI limit is reached (429) and lets the user pick by hand', async () => {
    const limited = () =>
      throwError(
        () =>
          new HttpErrorResponse({
            status: 429,
            error: { detail: 'Too many AI suggestions. Try again in 60 minutes.' },
          }),
      );
    const { type, leave, hint, submit, add } = await renderWithAdd(limited);
    type('description', 'Uber');
    await leave('description');
    expect(hint()).toBe(
      'No AI suggestion: Too many AI suggestions. Try again in 60 minutes. Please pick a category.',
    );
    type('amount', '32.5');
    type('category', 'transport');
    await submit();
    expect(add).toHaveBeenCalledWith(expect.objectContaining({ category: 'transport' }));
  });

  it('"Suggest again" asks once more', async () => {
    const suggest = vi.fn().mockReturnValueOnce(of('other')).mockReturnValueOnce(of('food'));
    const { type, leave, value, page, fixture } = await render(vi.fn(), suggest);
    type('description', 'Groceries');
    await leave('description');
    expect(value('category')).toBe('other');
    const again = page.querySelector<HTMLButtonElement>('button.suggest')!;
    expect(again.textContent).toContain('Suggest again');
    again.click();
    await fixture.whenStable();
    expect(suggest).toHaveBeenCalledTimes(2);
    expect(value('category')).toBe('food');
  });
});
