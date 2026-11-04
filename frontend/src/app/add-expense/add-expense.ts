import { Component, inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormControl,
  NonNullableFormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { Router } from '@angular/router';
import { apiErrorMessage } from '../api-error';
import { CATEGORIES, FREQUENCIES, Frequency, NewExpense } from '../expense.model';
import { ExpenseService } from '../expense.service';

/** Required, and more than spaces. */
function notBlank(control: AbstractControl<string>): ValidationErrors | null {
  return control.value.trim() ? null : { blank: true };
}

/** Greater than zero, the same rule as validate_amount() in models.py. */
function positive(control: AbstractControl<number | null>): ValidationErrors | null {
  const value = control.value;
  return value === null || value > 0 ? null : { positive: true };
}

/** Today as YYYY-MM-DD in the user's own time zone (toISOString() would use UTC). */
export function today(now = new Date()): string {
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${now.getFullYear()}-${month}-${day}`;
}

@Component({
  imports: [ReactiveFormsModule],
  selector: 'app-add-expense',
  styleUrl: './add-expense.css',
  templateUrl: './add-expense.html',
})
export class AddExpense {
  private readonly expenseService = inject(ExpenseService);
  private readonly router = inject(Router);

  protected readonly categories = CATEGORIES;
  protected readonly frequencies = FREQUENCIES;

  protected readonly form = inject(NonNullableFormBuilder).group({
    description: ['', [Validators.required, notBlank]],
    amount: new FormControl<number | null>(null, [Validators.required, positive]),
    category: ['', [Validators.required, notBlank]],
    date: [today(), Validators.required],
    frequency: ['' as Frequency | ''],
  });

  protected readonly saving = signal(false);
  /** The API's own message when it rejects the expense or can't be reached. */
  protected readonly serverError = signal('');

  /** Show a field's error once the user has left it, or tried to save. */
  protected showError(name: keyof typeof this.form.controls): boolean {
    const control = this.form.controls[name];
    return control.invalid && (control.touched || control.dirty);
  }

  protected save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const value = this.form.getRawValue();
    const expense: NewExpense = {
      amount: value.amount!,
      category: value.category.trim().toLowerCase(),
      description: value.description.trim(),
      date: value.date,
      ...(value.frequency ? { frequency: value.frequency } : {}),
    };
    this.saving.set(true);
    this.serverError.set('');
    this.expenseService.add(expense).subscribe({
      next: () => this.router.navigate(['/expenses']),
      error: (error: unknown) => {
        this.serverError.set(apiErrorMessage(error));
        this.saving.set(false);
      },
    });
  }
}
