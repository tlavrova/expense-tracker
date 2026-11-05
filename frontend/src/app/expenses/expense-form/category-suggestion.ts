import { signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl } from '@angular/forms';
import { Observable, Subscription } from 'rxjs';
import { apiErrorMessage } from '../../core/api-error';

/**
 * The AI suggestion for a form's category field, from its description field.
 *
 * Leaving the description with no category yet asks once per description; "Suggest" asks again.
 * The answer fills the category unless the user typed one meanwhile, and typing a category of
 * your own drops the AI's note (or its answer still on the way).
 *
 * Create it in a field initializer (it uses takeUntilDestroyed, which needs the component's
 * injection context).
 */
export class CategorySuggestion {
  /** Idle, waiting for Gemini, suggested, or unavailable. */
  readonly state = signal<'idle' | 'asking' | 'suggested' | 'failed'>('idle');
  /** Why there is no suggestion, when state is "failed". */
  readonly error = signal('');

  /** The description last sent to the AI, so leaving the field again doesn't ask twice. */
  private askedFor = '';
  private suggested = '';
  private pending?: Subscription;

  constructor(
    private readonly description: FormControl<string>,
    private readonly category: FormControl<string>,
    private readonly ask: (description: string) => Observable<string>,
  ) {
    category.valueChanges.pipe(takeUntilDestroyed()).subscribe((value) => {
      if (value !== this.suggested) {
        this.cancel();
      }
    });
  }

  /** The form was filled with a saved expense: it has its category, so don't ask for it. */
  alreadyHas(description: string): void {
    this.askedFor = description;
  }

  /** Leaving the description with no category yet asks the AI, once per description. */
  descriptionDone(): void {
    const description = this.description.value.trim();
    if (description && description !== this.askedFor && !this.category.value.trim()) {
      this.suggest();
    }
  }

  /** Ask the AI for a category; the answer fills the field unless the user typed one meanwhile. */
  suggest(): void {
    const description = this.description.value.trim();
    if (!description) {
      return;
    }
    this.cancel();
    this.askedFor = description;
    this.state.set('asking');
    this.pending = this.ask(description).subscribe({
      next: (category) => {
        this.suggested = category;
        this.category.setValue(category);
        this.state.set('suggested');
      },
      error: (error: unknown) => {
        this.error.set(apiErrorMessage(error));
        this.state.set('failed');
      },
    });
  }

  private cancel(): void {
    this.pending?.unsubscribe();
    this.pending = undefined;
    this.suggested = '';
    this.state.set('idle');
  }
}
