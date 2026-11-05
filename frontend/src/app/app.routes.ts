import { Routes } from '@angular/router';
import { AuthPage } from './auth/auth-page/auth-page';
import { PasswordPage } from './auth/password-page/password-page';
import { loggedInGuard, loggedOutGuard } from './auth/auth.guards';
import { ExpenseForm } from './expenses/expense-form/expense-form';
import { ExpenseList } from './expenses/expense-list/expense-list';
import { Summary } from './expenses/summary/summary';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'expenses' },
  // The same page in two modes; "mode" reaches the component as an input.
  {
    path: 'login',
    component: AuthPage,
    title: 'Log in',
    data: { mode: 'login' },
    canActivate: [loggedOutGuard],
  },
  {
    path: 'signup',
    component: AuthPage,
    title: 'Create an account',
    data: { mode: 'signup' },
    canActivate: [loggedOutGuard],
  },
  {
    path: '',
    canActivateChild: [loggedInGuard], // everything below needs a login
    children: [
      { path: 'expenses', component: ExpenseList, title: 'Expenses' },
      { path: 'expenses/new', component: ExpenseForm, title: 'Add expense' },
      // The same form; ":id" reaches the component as its id input and switches it to editing.
      { path: 'expenses/:id/edit', component: ExpenseForm, title: 'Edit expense' },
      { path: 'summary', component: Summary, title: 'Summary' },
      { path: 'password', component: PasswordPage, title: 'Change password' },
    ],
  },
  { path: '**', redirectTo: 'expenses' },
];
