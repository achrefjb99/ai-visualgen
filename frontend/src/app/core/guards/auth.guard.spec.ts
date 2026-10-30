import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot, UrlTree } from '@angular/router';
import { authGuard } from './auth.guard';
import { AuthService } from '../services/auth.service';
import { signal } from '@angular/core';
import { UserPublic, UserRole } from '../models/auth.model';

describe('authGuard', () => {
  let mockAuthService: {
    currentUser: ReturnType<typeof signal<UserPublic | null>>;
    isAuthenticated: () => boolean;
  };
  let router: Router;

  beforeEach(() => {
    const userSignal = signal<UserPublic | null>(null);
    mockAuthService = {
      currentUser: userSignal,
      isAuthenticated: () => !!userSignal(),
    };

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: mockAuthService },
      ],
    });

    router = TestBed.inject(Router);
  });

  it('devrait autoriser l’accès si l’utilisateur est authentifié', () => {
    mockAuthService.currentUser.set({
      id: 1,
      username: 'test',
      role: UserRole.TEACHER,
      created_at: new Date().toISOString(),
    });

    const route = {} as ActivatedRouteSnapshot;
    const state = { url: '/protected' } as RouterStateSnapshot;

    const result = TestBed.runInInjectionContext(() => authGuard(route, state));
    expect(result).toBe(true);
  });

  it('devrait rediriger vers /login avec returnUrl si l’utilisateur n’est pas authentifié', () => {
    mockAuthService.currentUser.set(null);

    const route = {} as ActivatedRouteSnapshot;
    const state = { url: '/protected-page' } as RouterStateSnapshot;

    const result = TestBed.runInInjectionContext(() => authGuard(route, state));
    expect(result instanceof UrlTree).toBe(true);
    const tree = result as UrlTree;
    expect(tree.toString()).toContain('/login?returnUrl=%2Fprotected-page');
  });
});
