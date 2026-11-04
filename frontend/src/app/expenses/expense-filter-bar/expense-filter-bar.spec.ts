import { TestBed } from '@angular/core/testing';
import { ExpenseFilters } from '../expense.model';
import { ExpenseFilterBar, FilterChange } from './expense-filter-bar';

async function render(filters: ExpenseFilters) {
  await TestBed.configureTestingModule({ imports: [ExpenseFilterBar] }).compileComponents();
  const fixture = TestBed.createComponent(ExpenseFilterBar);
  fixture.componentRef.setInput('filters', filters);
  const changes: FilterChange[] = [];
  let cleared = 0;
  fixture.componentInstance.changed.subscribe((change) => changes.push(change));
  fixture.componentInstance.cleared.subscribe(() => cleared++);
  await fixture.whenStable();
  return { page: fixture.nativeElement as HTMLElement, changes, cleared: () => cleared };
}

describe('ExpenseFilterBar', () => {
  it('shows the filters it is given', async () => {
    const { page } = await render({ category: 'food', month: '2026-11', sort: 'amount' });
    expect(page.querySelector<HTMLInputElement>('input[name=category]')!.value).toBe('food');
    expect(page.querySelector<HTMLInputElement>('input[name=month]')!.value).toBe('2026-11');
    expect(page.querySelector<HTMLSelectElement>('select[name=sort]')!.value).toBe('amount');
  });

  it('reports each change with the filter name and value', async () => {
    const { page, changes } = await render({});
    const category = page.querySelector<HTMLInputElement>('input[name=category]')!;
    category.value = 'transport';
    category.dispatchEvent(new Event('change'));
    const sort = page.querySelector<HTMLSelectElement>('select[name=sort]')!;
    sort.value = 'date';
    sort.dispatchEvent(new Event('change'));
    expect(changes).toEqual([
      { name: 'category', value: 'transport' },
      { name: 'sort', value: 'date' },
    ]);
  });

  it('offers "Clear" only when a filter or sort is set', async () => {
    expect((await render({})).page.querySelector('button.clear')).toBeNull();
    TestBed.resetTestingModule();
    const { page, cleared } = await render({ sort: 'date' });
    page.querySelector<HTMLButtonElement>('button.clear')!.click();
    expect(cleared()).toBe(1);
  });
});
