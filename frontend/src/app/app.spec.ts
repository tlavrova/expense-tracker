import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { App } from './app';
import { routes } from './app.routes';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter(routes), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  it('shows the app name and the navigation', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const page = fixture.nativeElement as HTMLElement;
    expect(page.querySelector('.brand')?.textContent).toContain('Expense Tracker');
    const links = Array.from(page.querySelectorAll('nav a')).map((link) =>
      link.textContent?.trim(),
    );
    expect(links).toEqual(['Expenses', 'Add expense', 'Summary']);
  });

  it('keeps "Expenses" highlighted while filters are in the address', async () => {
    const fixture = TestBed.createComponent(App);
    await TestBed.inject(Router).navigateByUrl('/expenses?category=food&sort=amount');
    await fixture.whenStable();
    const active = (fixture.nativeElement as HTMLElement).querySelector('nav a.active');
    expect(active?.textContent?.trim()).toBe('Expenses');
  });
});
