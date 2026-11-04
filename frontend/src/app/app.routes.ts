import { Routes } from '@angular/router';
import { AddExpense } from './expenses/add-expense/add-expense';
import { ExpenseList } from './expenses/expense-list/expense-list';
import { Summary } from './expenses/summary/summary';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'expenses' },
  { path: 'expenses', component: ExpenseList, title: 'Expenses' },
  { path: 'expenses/new', component: AddExpense, title: 'Add expense' },
  { path: 'summary', component: Summary, title: 'Summary' },
  { path: '**', redirectTo: 'expenses' },
];
