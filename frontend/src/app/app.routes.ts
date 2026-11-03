import { Routes } from '@angular/router';
import { AddExpense } from './add-expense/add-expense';
import { ExpenseList } from './expense-list/expense-list';
import { Summary } from './summary/summary';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'expenses' },
  { path: 'expenses', component: ExpenseList, title: 'Expenses' },
  { path: 'expenses/new', component: AddExpense, title: 'Add expense' },
  { path: 'summary', component: Summary, title: 'Summary' },
  { path: '**', redirectTo: 'expenses' },
];
