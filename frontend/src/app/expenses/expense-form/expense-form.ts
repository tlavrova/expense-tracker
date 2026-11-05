import { Component, OnInit, computed, inject, input, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  AbstractControl,
  FormControl,
  NonNullableFormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { Observable, Subscription } from 'rxjs';
import { apiErrorMessage } from '../../core/api-error';
import { CATEGORIES, Expense, FREQUENCIES, Frequency, NewExpense } from '../expense.model';
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

/**
 * The add page (/expenses/new) and the edit page (/expenses/:id/edit): the same form, two modes.
 *
 * Editing loads the expense into the form first and saves with PUT instead of POST. The AI
 * suggestion works the same in both, so it only asks when the category is empty.
 */
@Component({
  imports: [ReactiveFormsModule, RouterLink],
  selector: 'app-expense-form',
  styleUrl: './expense-form.css',
  templateUrl: './expense-form.html',
})
export class ExpenseForm implements OnInit {
  private readonly expenseService = inject(ExpenseService);
  private readonly router = inject(Router);

  /** From the address on the edit page (/expenses/:id/edit); not set on the add page. */
  readonly id = input<string>();
  protected readonly editing = computed(() => this.id() !== undefined);
  /** Edit page: true while the expense is loading; the error if it can't be loaded. */
  protected readonly loading = signal(false);
  protected readonly loadError = signal('');

  protected readonly categories = CATEGORIES;
  protected readonly frequencies = FREQUENCIES;

  protected readonly form = inject(NonNullableFormBuilder).group({
    description: ['', [Validators.required, notBlank]],
    amount: new FormControl<number | null>(null, [Validators.required, positive]),
    category: ['', [Validators.required, notBlank]],
    date: [today(), Validators.required],
    frequency: ['' as Frequency | ''],
  });

  /** The AI suggestion for the category: idle, waiting for Gemini, suggested, or unavailable. */
  protected readonly ai = signal<'idle' | 'asking' | 'suggested' | 'failed'>('idle');
  protected readonly aiError = signal('');
  /** The description last sent to the AI, so leaving the field again doesn't ask twice. */
  private askedFor = '';
  private suggested = '';
  private pending?: Subscription;

  protected readonly saving = signal(false);
  /** The API's own message when it rejects the expense or can't be reached. */
  protected readonly serverError = signal('');

  constructor() {
    // Typing a category of your own overrides the AI: drop its note, or its answer still on the way.
    this.form.controls.category.valueChanges.pipe(takeUntilDestroyed()).subscribe((value) => {
      if (value !== this.suggested) {
        this.cancelSuggestion();
      }
    });
  }

  ngOnInit(): void {
    // Inputs from the route are set by now, not yet in the constructor.
    const id = this.id();
    if (id !== undefined) {
      this.load(Number(id));
    }
  }

  private load(id: number): void {
    this.loading.set(true);
    this.expenseService.get(id).subscribe({
      next: (expense) => {
        this.fill(expense);
        this.loading.set(false);
      },
      error: (error: unknown) => {
        this.loadError.set(apiErrorMessage(error)); // e.g. 404 "No expense with id 7."
        this.loading.set(false);
      },
    });
  }

  private fill(expense: Expense): void {
    this.form.setValue({
      description: expense.description,
      amount: expense.amount,
      category: expense.category,
      date: expense.date,
      frequency: expense.frequency ?? '',
    });
    this.askedFor = expense.description; // it has a category: leaving the description won't ask
  }

  /** Leaving the description with no category yet asks the AI, once per description. */
  protected descriptionDone(): void {
    const description = this.form.controls.description.value.trim();
    if (description && description !== this.askedFor && !this.form.controls.category.value.trim()) {
      this.suggest();
    }
  }

  /** Ask the AI for a category; the answer fills the field unless the user typed one meanwhile. */
  protected suggest(): void {
    const description = this.form.controls.description.value.trim();
    if (!description) {
      return;
    }
    this.cancelSuggestion();
    this.askedFor = description;
    this.ai.set('asking');
    this.pending = this.expenseService.suggestCategory(description).subscribe({
      next: (category) => {
        this.suggested = category;
        this.form.controls.category.setValue(category);
        this.ai.set('suggested');
      },
      error: (error: unknown) => {
        this.aiError.set(apiErrorMessage(error));
        this.ai.set('failed');
      },
    });
  }

  private cancelSuggestion(): void {
    this.pending?.unsubscribe();
    this.pending = undefined;
    this.suggested = '';
    this.ai.set('idle');
  }

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
    const id = this.id();
    const request: Observable<Expense> =
      id === undefined
        ? this.expenseService.add(expense)
        : this.expenseService.update(Number(id), expense);
    this.saving.set(true);
    this.serverError.set('');
    request.subscribe({
      next: () => this.router.navigate(['/expenses']),
      error: (error: unknown) => {
        this.serverError.set(apiErrorMessage(error));
        this.saving.set(false);
      },
    });
  }
}
