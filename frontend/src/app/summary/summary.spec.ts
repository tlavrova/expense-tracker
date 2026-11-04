import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Observable, of, throwError } from 'rxjs';
import { Summary as SummaryData } from '../expense.model';
import { ExpenseService } from '../expense.service';
import { Summary } from './summary';

async function render(summary: () => Observable<SummaryData>): Promise<HTMLElement> {
  await TestBed.configureTestingModule({
    imports: [Summary],
    providers: [provideRouter([]), { provide: ExpenseService, useValue: { summary } }],
  }).compileComponents();
  const fixture = TestBed.createComponent(Summary);
  await fixture.whenStable();
  return fixture.nativeElement as HTMLElement;
}

describe('Summary', () => {
  it('lists categories largest first with their share, and the overall total', async () => {
    const page = await render(() =>
      of({ totalsByCategory: { food: 25, housing: 900, transport: 75 }, total: 1000 }),
    );
    const rows = [...page.querySelectorAll('tbody tr')].map((row) =>
      [...row.querySelectorAll('th, td')].map((cell) => cell.textContent?.trim()),
    );
    expect(rows).toEqual([
      ['housing', '90%', '900.00'],
      ['transport', '8%', '75.00'],
      ['food', '3%', '25.00'],
    ]);
    expect(page.querySelector('.total')?.textContent?.trim()).toBe('1,000.00');
  });

  it('links each category to the list filtered by it', async () => {
    const page = await render(() => of({ totalsByCategory: { food: 12 }, total: 12 }));
    expect(page.querySelector('tbody a')?.getAttribute('href')).toBe('/expenses?category=food');
  });

  it('says so when there are no expenses', async () => {
    const page = await render(() => of({ totalsByCategory: {}, total: 0 }));
    expect(page.querySelector('table')).toBeNull();
    expect(page.textContent).toContain('No expenses yet.');
  });

  it('explains when the API cannot be reached', async () => {
    const page = await render(() => throwError(() => new HttpErrorResponse({ status: 0 })));
    expect(page.querySelector('[role=alert]')?.textContent).toContain("Can't reach the API");
  });
});
