import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { ExpenseService } from '../expense.service';
import { AddExpense, today } from './add-expense';

async function render(add: ExpenseService['add']) {
  await TestBed.configureTestingModule({
    imports: [AddExpense],
    providers: [provideRouter([]), { provide: ExpenseService, useValue: { add } }],
  }).compileComponents();
  const fixture = TestBed.createComponent(AddExpense);
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
  return { page, navigate, type, submit };
}

describe('AddExpense', () => {
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

describe('today()', () => {
  it('uses the local date, padded', () => {
    expect(today(new Date(2026, 0, 5, 23, 30))).toBe('2026-01-05');
  });
});
