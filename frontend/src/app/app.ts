import { Component, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';
import { AuthService } from './auth/auth.service';

@Component({
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App {
  protected readonly auth = inject(AuthService);

  /** Phones: whether the account menu (email, log out) is open. */
  protected readonly menuOpen = signal(false);

  constructor() {
    // Any page change (a nav link, Change password, Log out) closes the menu.
    inject(Router)
      .events.pipe(
        filter((event) => event instanceof NavigationEnd),
        takeUntilDestroyed(),
      )
      .subscribe(() => this.menuOpen.set(false));
    if (this.auth.loggedIn()) {
      this.auth.loadEmail(); // a token kept from an earlier visit: show whose it is
    }
  }
}
